// SchulBuddy API — einzelne Edge Function für Auth, Daten-CRUD und KI-Tutor.
// Läuft mit dem Service-Role-Key (voller DB-Zugriff), damit die Tabellen
// selbst für "anon" gesperrt bleiben. Das Frontend (index.html) spricht
// ausschließlich diese Function an, nie direkt die DB oder die Anthropic API.

import { createClient } from "npm:@supabase/supabase-js@2";
import createHafasClient from "npm:nahsh-hafas@5";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY");

const supabase = createClient(SUPABASE_URL, SERVICE_KEY);
const hafas = createHafasClient("schulbuddy-familien-app");

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const NAMEN = ["Papa", "Mama", "Mila", "Jojo", "Mikko"];
const CHILD_NAMES = ["Mila", "Jojo", "Mikko"];
const SESSION_TAGE = 30;

// Feste HAFAS-Stop-IDs der drei Haltestellen der Familie (via NAH.SH ermittelt).
const BUS_STOPS = {
  seefisch: "9049245", // Kiel Seefischmarkt
  linas: "9083498",    // Schönkirchen Linas Diek
  amboss: "9083492",   // Schönkirchen Amboßweg
} as const;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function randomToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function requireUser(token: string | undefined): Promise<string | null> {
  if (!token) return null;
  const { data, error } = await supabase
    .from("sessions")
    .select("name, gueltig_bis")
    .eq("token", token)
    .maybeSingle();
  if (error || !data) return null;
  if (new Date(data.gueltig_bis).getTime() < Date.now()) return null;
  return data.name as string;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const action = String(body.action || "");

  try {
    // ---------------- AUTH (kein Token nötig) ----------------
    if (action === "register") {
      const name = String(body.name || "");
      const passwort = String(body.passwort || "");
      const rolle = String(body.rolle || "Kind");
      const frage = String(body.frage || "").trim();
      const antwort = String(body.antwort || "").trim();
      if (!NAMEN.includes(name)) return json({ error: "invalid_name" }, 400);
      if (passwort.length < 4) return json({ error: "password_too_short" }, 400);
      if (!frage || !antwort) return json({ error: "missing_security_question" }, 400);

      const { data: existing } = await supabase.from("nutzer").select("name").eq("name", name).maybeSingle();
      if (existing) return json({ error: "name_taken" }, 409);

      const { error } = await supabase.from("nutzer").insert({
        name,
        passwort_hash: await sha256(passwort),
        rolle,
        sicherheitsfrage: frage,
        sicherheitsantwort_hash: await sha256(antwort.toLowerCase()),
      });
      if (error) return json({ error: "db_error", detail: error.message }, 500);
      return json({ ok: true });
    }

    if (action === "login") {
      const name = String(body.name || "");
      const passwort = String(body.passwort || "");
      const pwHash = await sha256(passwort);
      const { data } = await supabase
        .from("nutzer")
        .select("name")
        .eq("name", name)
        .eq("passwort_hash", pwHash)
        .maybeSingle();
      if (!data) return json({ error: "invalid_credentials" }, 401);

      const token = randomToken();
      const gueltigBis = new Date(Date.now() + SESSION_TAGE * 24 * 60 * 60 * 1000).toISOString();
      const { error } = await supabase.from("sessions").insert({ token, name, gueltig_bis: gueltigBis });
      if (error) return json({ error: "db_error", detail: error.message }, 500);
      return json({ ok: true, token, name });
    }

    if (action === "logout") {
      const token = String(body.token || "");
      if (token) await supabase.from("sessions").delete().eq("token", token);
      return json({ ok: true });
    }

    if (action === "verify") {
      const name = await requireUser(String(body.token || ""));
      if (!name) return json({ ok: false });
      return json({ ok: true, name });
    }

    if (action === "get_security_question") {
      const name = String(body.name || "");
      const { data } = await supabase.from("nutzer").select("sicherheitsfrage").eq("name", name).maybeSingle();
      return json({ frage: data?.sicherheitsfrage || null });
    }

    if (action === "reset_password") {
      const name = String(body.name || "");
      const antwort = String(body.antwort || "").trim().toLowerCase();
      const neuesPasswort = String(body.neues_passwort || "");
      if (neuesPasswort.length < 4) return json({ error: "password_too_short" }, 400);

      const { data } = await supabase
        .from("nutzer")
        .select("sicherheitsantwort_hash")
        .eq("name", name)
        .maybeSingle();
      if (!data || data.sicherheitsantwort_hash !== (await sha256(antwort))) {
        return json({ error: "wrong_answer" }, 401);
      }
      await supabase.from("nutzer").update({ passwort_hash: await sha256(neuesPasswort) }).eq("name", name);
      await supabase.from("sessions").delete().eq("name", name);
      return json({ ok: true });
    }

    // ---------------- Ab hier: gültiges Token nötig ----------------
    const user = await requireUser(String(body.token || ""));
    if (!user) return json({ error: "unauthorized" }, 401);
    const isKind = CHILD_NAMES.includes(user);

    if (action === "dashboard") {
      const heute = new Date();
      heute.setHours(0, 0, 0, 0);
      const { data } = await supabase.from("klausuren").select("*");
      const warnungen = (data || [])
        .map((k) => {
          const delta = Math.round((new Date(k.start_date).getTime() - heute.getTime()) / 86400000);
          return { ...k, delta };
        })
        .filter((k) => k.delta >= 0 && k.delta <= 2)
        .sort((a, b) => a.delta - b.delta);
      return json({ warnungen });
    }

    if (action === "klausuren_list") {
      const { data, error } = await supabase.from("klausuren").select("*");
      if (error) return json({ error: "db_error" }, 500);
      return json({ data });
    }

    if (action === "klausur_create") {
      let child = String(body.child || "");
      if (isKind) child = user; // Kinder tragen nur für sich selbst ein
      const { error } = await supabase.from("klausuren").insert({
        datum: body.datum,
        titel: `${child}\n${body.fach}`,
        start_date: body.start_date,
        color: body.color,
        child,
        note: body.note || "",
      });
      if (error) return json({ error: "db_error", detail: error.message }, 500);
      return json({ ok: true });
    }

    if (action === "klausur_update") {
      const id = body.id;
      let child = String(body.child || "");
      if (isKind) child = user;
      const { error } = await supabase
        .from("klausuren")
        .update({
          datum: body.datum,
          titel: `${child}\n${body.fach}`,
          start_date: body.start_date,
          color: body.color,
          child,
          note: body.note || "",
        })
        .eq("id", id);
      if (error) return json({ error: "db_error", detail: error.message }, 500);
      return json({ ok: true });
    }

    if (action === "klausur_delete") {
      if (isKind) {
        // Kinder dürfen nur eigene Klausuren löschen
        const { data } = await supabase.from("klausuren").select("child").eq("id", body.id).maybeSingle();
        if (!data || data.child !== user) return json({ error: "forbidden" }, 403);
      }
      const { error } = await supabase.from("klausuren").delete().eq("id", body.id);
      if (error) return json({ error: "db_error" }, 500);
      return json({ ok: true });
    }

    if (action === "kind_info_get") {
      const { data } = await supabase.from("kinder_info").select("klasse").eq("child", body.child).maybeSingle();
      return json({ klasse: data?.klasse || null });
    }

    if (action === "kind_info_set") {
      const { error } = await supabase
        .from("kinder_info")
        .upsert({ child: body.child, klasse: body.klasse });
      if (error) return json({ error: "db_error" }, 500);
      return json({ ok: true });
    }

    if (action === "stundenplan_get") {
      const { data, error } = await supabase.from("stundenplaene").select("*").eq("child", body.child);
      if (error) return json({ error: "db_error" }, 500);
      return json({ data });
    }

    if (action === "stundenplan_set") {
      const { id, child, tag, stunde, fach } = body as {
        id?: number; child: string; tag: string; stunde: number; fach: string;
      };
      if (id) {
        const { error } = await supabase.from("stundenplaene").update({ fach }).eq("id", id);
        if (error) return json({ error: "db_error" }, 500);
      } else {
        const { error } = await supabase.from("stundenplaene").insert({ child, tag, stunde, fach });
        if (error) return json({ error: "db_error" }, 500);
      }
      return json({ ok: true });
    }

    if (action === "pinnwand_list") {
      const { data, error } = await supabase
        .from("nachrichten")
        .select("*")
        .order("created_at", { ascending: false });
      if (error) return json({ error: "db_error" }, 500);
      return json({ data });
    }

    if (action === "pinnwand_create") {
      const text = String(body.text || "").trim().slice(0, 200);
      if (!text) return json({ error: "empty" }, 400);
      const { error } = await supabase.from("nachrichten").insert({ name: user, text });
      if (error) return json({ error: "db_error" }, 500);
      return json({ ok: true });
    }

    if (action === "pinnwand_delete") {
      const { error } = await supabase.from("nachrichten").delete().eq("id", body.id);
      if (error) return json({ error: "db_error" }, 500);
      return json({ ok: true });
    }

    if (action === "bus_departures") {
      // Nur die drei bekannten Haltestellen der Familie sind erlaubt (kein freier Stop-Zugriff).
      const stopKey = String(body.stopKey || "");
      const stopId = BUS_STOPS[stopKey as keyof typeof BUS_STOPS];
      if (!stopId) return json({ error: "unknown_stop" }, 400);
      try {
        const result = await hafas.departures(stopId, { duration: 240, results: 10, remarks: false });
        const departures = (result.departures ?? result) as Array<Record<string, unknown>>;
        // Fürs Frontend auf das Nötigste reduzieren.
        const slim = departures.map((d) => ({
          when: d.when,
          plannedWhen: d.plannedWhen,
          delay: d.delay,
          line: (d.line as Record<string, unknown> | undefined)?.name ?? "?",
          direction: d.direction,
          platform: d.platform,
          cancelled: d.cancelled ?? false,
        }));
        return json({ departures: slim });
      } catch (e) {
        return json({ error: "hafas_error", detail: String(e) }, 502);
      }
    }

    if (action === "schulbuddy_chat") {
      if (!ANTHROPIC_API_KEY) return json({ error: "no_api_key" }, 500);
      const systemPrompt = String(body.system || "");
      const history = Array.isArray(body.history) ? body.history : [];
      const resp = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": ANTHROPIC_API_KEY,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-5",
          max_tokens: 1000,
          system: systemPrompt,
          messages: history,
        }),
      });
      if (!resp.ok) {
        const errText = await resp.text();
        return json({ error: "anthropic_error", detail: errText }, 502);
      }
      const data = await resp.json();
      const answer = data?.content?.[0]?.text || "";
      return json({ answer });
    }

    return json({ error: "unknown_action" }, 400);
  } catch (e) {
    return json({ error: "internal_error", detail: String(e) }, 500);
  }
});
