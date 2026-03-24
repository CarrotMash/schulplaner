import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import zoneinfo
from supabase import create_client
import os
import uuid
import hashlib
import secrets

# --- DATENBANK VERBINDUNG ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- KONFIGURATION ---
CHILD_COLORS  = {"Mila": "#FF85A1", "Jojo": "#8B0000", "Mikko": "#2E7D32"}
PINNWAND_NAMEN  = ["Papa", "Mama", "Mila", "Jojo", "Mikko"]
PINNWAND_FARBEN = {
    "Papa": "#1565C0", "Mama": "#6A1B9A",
    "Mila": "#FF85A1", "Jojo": "#8B0000", "Mikko": "#2E7D32"
}
SUBJECTS = ["Englisch","Französisch","Mathematik","Deutsch","Musik","Biologie",
            "Chemie","Kunst","Philosophie","Geschichte","Physik","Spanisch",
            "WiPo","Geografie","Sport","Religion","Freistunde"]
DAYS  = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag"]
TIMES = {1:"07:50–08:35", 2:"08:40–09:25", 3:"09:40–10:25",
         4:"10:30–11:15", 5:"11:30–12:15", 6:"12:20–13:05", 7:"13:35–14:20"}

# Ferien als strukturierte Liste mit date-Objekten für Countdown
FERIEN_LIST = [
    {"name": "Osterferien",     "start": date(2026,  3, 26), "end": date(2026,  4, 11)},
    {"name": "Sommerferien",    "start": date(2026,  7, 13), "end": date(2026,  8, 22)},
    {"name": "Herbstferien",    "start": date(2026, 10, 12), "end": date(2026, 10, 24)},
    {"name": "Weihnachtsferien","start": date(2026, 12, 21), "end": date(2027,  1,  6)},
    {"name": "Osterferien",     "start": date(2027,  3, 22), "end": date(2027,  4,  3)},
    {"name": "Sommerferien",    "start": date(2027,  7, 12), "end": date(2027,  8, 21)},
    {"name": "Herbstferien",    "start": date(2027, 10, 11), "end": date(2027, 10, 23)},
    {"name": "Weihnachtsferien","start": date(2027, 12, 20), "end": date(2028,  1,  5)},
]

# --- SESSION STATE ---
if 'view'              not in st.session_state: st.session_state.view = 'start'
if 'cal_key'           not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = None
if 'stundenplan_day'   not in st.session_state: st.session_state.stundenplan_day = "Montag"
if 'editing_grade'     not in st.session_state: st.session_state.editing_grade = False
if 'selected_date'     not in st.session_state: st.session_state.selected_date = None
if 'edit_id'           not in st.session_state: st.session_state.edit_id = None
if 'cancel_click'      not in st.session_state: st.session_state.cancel_click = False
if 'active_msg'        not in st.session_state: st.session_state.active_msg   = None
if 'bus_halt'          not in st.session_state: st.session_state.bus_halt = None
if 'quiz_name'         not in st.session_state: st.session_state.quiz_name = None
if 'quiz_phase'        not in st.session_state: st.session_state.quiz_phase = 'name'
if 'quiz_fragen'       not in st.session_state: st.session_state.quiz_fragen = []
if 'quiz_idx'          not in st.session_state: st.session_state.quiz_idx = 0
if 'quiz_punkte'       not in st.session_state: st.session_state.quiz_punkte = {}
if 'quiz_antwort'      not in st.session_state: st.session_state.quiz_antwort = None
if 'user'              not in st.session_state: st.session_state.user = None
if 'login_fehler'      not in st.session_state: st.session_state.login_fehler = None

st.set_page_config(page_title="Schulplaner", page_icon="📅", layout="centered")

# --- PWA ---
st.markdown(
    '<link rel="manifest" href="data:application/json;base64,eyJuYW1lIjogIlNjaHVscGxhbmVyIiwgInNob3J0X25hbWUiOiAiU2NodWxwbGFuZXIiLCAiZGVzY3JpcHRpb24iOiAiRmFtaWxpZW4tU2NodWxwbGFuZXIiLCAic3RhcnRfdXJsIjogIi8iLCAiZGlzcGxheSI6ICJzdGFuZGFsb25lIiwgIm9yaWVudGF0aW9uIjogInBvcnRyYWl0IiwgImJhY2tncm91bmRfY29sb3IiOiAiI0ZGRkZGRiIsICJ0aGVtZV9jb2xvciI6ICIjRkY0QjRCIiwgImljb25zIjogW3sic3JjIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvZmx1ZW50dWktZW1vamkvbWFpbi9hc3NldHMvU3BpcmFsJTIwY2FsZW5kYXIvM0Qvc3BpcmFsX2NhbGVuZGFyXzNkLnBuZyIsICJzaXplcyI6ICIyNTZ4MjU2IiwgInR5cGUiOiAiaW1hZ2UvcG5nIiwgInB1cnBvc2UiOiAiYW55IG1hc2thYmxlIn1dfQ==">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="theme-color" content="#FF4B4B">'
    '<script>'
    'window.addEventListener("beforeinstallprompt",function(e){'
    'e.preventDefault();window.deferredPrompt=e;'
    'setTimeout(function(){if(window.deferredPrompt){'
    'window.deferredPrompt.prompt();'
    'window.deferredPrompt.userChoice.then(function(){window.deferredPrompt=null;});}},3000);});'
    '</script>',
    unsafe_allow_html=True
)

# --- GLOBALES CSS ---
st.markdown("""
<style>
/* Layout */
.block-container { padding-top: 1.2rem !important; padding-bottom: 5rem !important; }

/* Page-Header (roter Balken) */
.page-header {
    font-size: 1.6rem !important; font-weight: 900 !important;
    text-align: center; margin-bottom: 16px;
    background: linear-gradient(135deg, #FF4B4B, #c0392b);
    color: #FFFFFF !important;
    padding: 10px 16px; border-radius: 12px;
    line-height: 1.2; letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(255,75,75,0.3);
}

/* Datum-Banner auf Startseite */
.date-banner {
    text-align: center; padding: 6px 0 2px 0;
    font-size: 0.95rem; color: #888; margin-bottom: 4px;
}
.date-banner b { color: #444; font-size: 1.05rem; }

/* Navigationsbuttons */
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0 !important; flex: 1 1 0 !important;
}
[data-testid="stHorizontalBlock"] button,
[data-testid="stHorizontalBlock"] a[data-testid="stLinkButton"] {
    font-size: 0.72rem !important;
    padding: 0.15rem 0.2rem !important;
    white-space: normal !important;
    line-height: 1.15 !important;
    min-height: 0 !important;
    height: 44px !important;
    background-color: #FF4B4B !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
[data-testid="stHorizontalBlock"] button:hover,
[data-testid="stHorizontalBlock"] a[data-testid="stLinkButton"]:hover {
    background-color: #c0392b !important;
    color: white !important;
}

/* Kalender */
.fc-button-primary {
    background-color: #FF4B4B !important; border-color: #FF4B4B !important;
    color: #FFF !important; font-weight: bold !important;
    font-size: 0.8rem !important; text-transform: capitalize !important;
}
.fc-button-active  { background-color: #B91D1D !important; border-color: #B91D1D !important; }
.fc-toolbar-title  { font-size: 1.1rem !important; font-weight: bold !important; }
.fc-event-title    { font-size: 0.75rem !important; white-space: pre-wrap !important;
                     font-weight: bold !important; line-height: 1.1 !important; }
.fc-day-sat, .fc-day-sun { background-color: #F0F2F6 !important; }
.fc-list-event-time { display: none !important; }

/* Bus-Haltestellen-Buttons: gleiche Höhe, Text passt rein */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    height: 64px !important;
    white-space: normal !important;
    line-height: 1.2 !important;
    font-size: 0.72rem !important;
    padding: 4px 4px !important;
    word-break: break-word !important;
}

/* Stundenplan-Tabelle */
.sp-table { width:100%; border-collapse:collapse; font-size:0.88rem; margin-top:4px; }
.sp-table tr { border-bottom: 1px solid #f0f0f0; }
.sp-table td { padding: 5px 6px; vertical-align: middle; }
.sp-table td.std-nr { color:#aaa; width:20px; font-size:0.78rem; }
.sp-table td.uhr    { color:#bbb; font-size:0.75rem; white-space:nowrap; text-align:right; }
.sp-table td.fach   { font-weight:600; padding-left:8px; }

/* Countdown-Box */
.countdown-box {
    background: linear-gradient(135deg, #FF4B4B, #c0392b);
    color: white; border-radius: 14px; padding: 18px 16px 14px 16px;
    text-align: center; margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(255,75,75,0.35);
}
.countdown-box .cd-label { font-size: 0.8rem; opacity: 0.85; margin-bottom: 4px; letter-spacing:1px; text-transform:uppercase; }
.countdown-box .cd-days  { font-size: 3.2rem; font-weight: 900; line-height: 1; }
.countdown-box .cd-name  { font-size: 1rem; font-weight: 700; margin-top: 4px; }
.countdown-box .cd-date  { font-size: 0.78rem; opacity: 0.8; margin-top: 2px; }

/* Ferien-Zeitleiste */
.ferien-item {
    display:flex; align-items:center; gap:12px;
    padding: 10px 12px; border-radius:10px; margin-bottom:8px;
    background:#fafafa; border-left: 5px solid #FF4B4B;
}
.ferien-item.aktiv { background:#fff8f8; border-left-color: #FF4B4B; }
.ferien-item.vorbei { opacity:0.45; border-left-color:#ddd; }
.ferien-item .fi-name { font-weight:700; font-size:0.95rem; color:#222 !important; }
.ferien-item .fi-date { font-size:0.78rem; color:#666 !important; }
.ferien-item .fi-badge {
    margin-left:auto; font-size:0.72rem; font-weight:700;
    padding:3px 8px; border-radius:20px; white-space:nowrap;
}

/* Pinnwand-Bubbles */
.pin-bubble {
    border-radius: 10px; padding: 8px 12px; margin-bottom: 8px;
    border-left: 4px solid #ddd; background: #fafafa;
}
.pin-name  { font-weight:800; font-size:0.88rem; color:#222 !important; }
.pin-zeit  { font-size:0.72rem; color:#999 !important; margin-left:8px; }
.pin-text  { font-size:0.92rem; margin-top:3px; color:#333 !important; }

/* Streamlit-Branding ausblenden */
#MainMenu, footer, header,
[data-testid="stDeployButton"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stMainMenuPopover"],
[data-testid="manage-app-button"],
[data-testid="stActionButton"],
[data-testid="baseButton-headerNoPadding"],
._container_gzau3_1,
._profileContainer_gzau3_53,
.viewerBadge_container__r5tak,
.viewerBadge_link__qRIco { display: none !important; }
</style>
""", unsafe_allow_html=True)

# MutationObserver: Streamlit-UI dauerhaft entfernen
st.markdown("""
<script>
(function(){
    function rm(){
        ['[data-testid="manage-app-button"]','[data-testid="stDeployButton"]',
         '[data-testid="stToolbar"]','._container_gzau3_1','#MainMenu','footer','header']
        .forEach(function(s){
            document.querySelectorAll(s).forEach(function(e){ e.remove(); });
        });
    }
    rm();
    new MutationObserver(rm).observe(document.body,{childList:true,subtree:true});
})();
</script>
""", unsafe_allow_html=True)

# --- HILFSFUNKTION: Seiten-Header ---
def page_header(title):
    st.markdown(f'<p class="page-header">{title}</p>', unsafe_allow_html=True)

# --- HILFSFUNKTION: Zurück-Button ---
def back_button():
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("← Hauptmenü", use_container_width=True, key="back_btn"):
        st.session_state.view = 'start'
        st.rerun()

# --- HILFSFUNKTION: nächste Ferien ---
def naechste_ferien():
    heute = date.today()
    for f in FERIEN_LIST:
        if f["end"] >= heute:
            return f
    return None

# =============================================================================
# LOGIN-SYSTEM
# =============================================================================

def hash_passwort(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def token_generieren() -> str:
    return secrets.token_hex(32)

def session_laden():
    """Token aus query_params lesen und User laden."""
    token = st.query_params.get("token", None)
    if token and not st.session_state.user:
        try:
            res = supabase.table("sessions").select("name,gueltig_bis").eq(
                "token", token).execute()
            if res.data:
                from datetime import timezone
                gueltig = datetime.fromisoformat(res.data[0]["gueltig_bis"])
                if gueltig.tzinfo is None:
                    gueltig = gueltig.replace(tzinfo=timezone.utc)
                if gueltig > datetime.now(timezone.utc):
                    st.session_state.user = res.data[0]["name"]
        except Exception:
            pass

def login(name: str, passwort: str) -> bool:
    """Login prüfen, bei Erfolg Session anlegen."""
    try:
        pw_hash = hash_passwort(passwort)
        res = supabase.table("nutzer").select("name").eq(
            "name", name).eq("passwort_hash", pw_hash).execute()
        if res.data:
            token = token_generieren()
            supabase.table("sessions").insert({
                "token": token,
                "name":  name,
            }).execute()
            st.session_state.user = name
            st.query_params["token"] = token
            return True
    except Exception:
        pass
    return False

def logout():
    token = st.query_params.get("token", None)
    if token:
        try:
            supabase.table("sessions").delete().eq("token", token).execute()
        except Exception:
            pass
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

def nutzer_registrieren(name: str, passwort: str, rolle: str,
                        sicherheitsfrage: str = "", sicherheitsantwort: str = "") -> bool:
    """Neuen Nutzer anlegen (nur wenn Name noch nicht vergeben)."""
    try:
        pw_hash = hash_passwort(passwort)
        eintrag = {
            "name":          name,
            "passwort_hash": pw_hash,
            "rolle":         rolle,
        }
        if sicherheitsfrage:
            eintrag["sicherheitsfrage"]       = sicherheitsfrage
            eintrag["sicherheitsantwort_hash"] = hash_passwort(
                sicherheitsantwort.lower().strip())
        supabase.table("nutzer").insert(eintrag).execute()
        return True
    except Exception:
        return False

# Session beim Start laden (Token aus URL)
session_laden()

# Login-Screen anzeigen wenn nicht eingeloggt
if not st.session_state.user:
    st.markdown(
        '<div style="text-align:center;margin:24px 0 8px 0;">'
        '<span style="font-size:1.8rem;font-weight:900;color:#FF4B4B;">📅 Schulplaner</span><br>'
        '<span style="color:#888;font-size:0.9rem;">Bitte einloggen</span>'
        '</div>',
        unsafe_allow_html=True
    )

    tab_login, tab_reg, tab_reset = st.tabs(["🔑 Login", "✏️ Registrieren", "🔓 Passwort vergessen"])

    with tab_login:
        with st.form("login_form"):
            name_inp = st.selectbox("Name", ["Papa", "Mama", "Mila", "Jojo", "Mikko"])
            pw_inp   = st.text_input("Passwort", type="password")
            submit   = st.form_submit_button("Einloggen", use_container_width=True)
            if submit:
                if login(name_inp, pw_inp):
                    st.rerun()
                else:
                    st.error("❌ Name oder Passwort falsch.")

    with tab_reg:
        st.caption("Nur beim ersten Mal nötig — danach einfach einloggen.")
        with st.form("reg_form"):
            reg_name  = st.selectbox("Name", ["Papa", "Mama", "Mila", "Jojo", "Mikko"],
                                     key="reg_name_sel")
            reg_pw    = st.text_input("Passwort wählen", type="password", key="reg_pw")
            reg_pw2   = st.text_input("Passwort wiederholen", type="password", key="reg_pw2")
            reg_rolle = st.selectbox("Rolle", ["Eltern", "Kind"], key="reg_rolle")
            st.markdown("---")
            st.caption("🔐 Sicherheitsfrage für Passwort-Reset:")
            reg_frage = st.text_input("Deine Sicherheitsfrage",
                placeholder="z.B. Wie heißt unser erstes Haustier?", key="reg_frage")
            reg_antwort = st.text_input("Antwort", type="password", key="reg_antwort")
            reg_btn   = st.form_submit_button("Account erstellen", use_container_width=True)
            if reg_btn:
                if reg_pw != reg_pw2:
                    st.error("❌ Passwörter stimmen nicht überein.")
                elif len(reg_pw) < 4:
                    st.error("❌ Passwort muss mindestens 4 Zeichen haben.")
                elif not reg_frage.strip() or not reg_antwort.strip():
                    st.error("❌ Bitte Sicherheitsfrage und Antwort ausfüllen.")
                elif nutzer_registrieren(reg_name, reg_pw, reg_rolle,
                                         reg_frage.strip(), reg_antwort.strip()):
                    st.success(f"✅ Account für {reg_name} erstellt! Bitte einloggen.")
                else:
                    st.error("❌ Name bereits vergeben oder Fehler aufgetreten.")
    with tab_reset:
        st.caption("Beantworte deine Sicherheitsfrage um ein neues Passwort zu setzen.")
        with st.form("reset_form"):
            rst_name    = st.selectbox("Name", ["Papa", "Mama", "Mila", "Jojo", "Mikko"],
                                       key="rst_name")
            rst_antwort = st.text_input("Antwort auf deine Sicherheitsfrage",
                                        type="password", key="rst_antwort")
            rst_pw_neu  = st.text_input("Neues Passwort", type="password", key="rst_pw")
            rst_pw_neu2 = st.text_input("Neues Passwort wiederholen",
                                        type="password", key="rst_pw2")
            rst_btn     = st.form_submit_button("Passwort zurücksetzen",
                                                use_container_width=True)
            if rst_btn:
                if rst_pw_neu != rst_pw_neu2:
                    st.error("❌ Passwörter stimmen nicht überein.")
                elif len(rst_pw_neu) < 4:
                    st.error("❌ Passwort muss mindestens 4 Zeichen haben.")
                else:
                    try:
                        antwort_hash = hash_passwort(rst_antwort.lower().strip())
                        res = supabase.table("nutzer").select(
                            "name,sicherheitsfrage,sicherheitsantwort_hash").eq(
                            "name", rst_name).execute()
                        if (res.data and
                                res.data[0].get("sicherheitsantwort_hash") == antwort_hash):
                            # Passwort updaten + Sessions löschen
                            supabase.table("nutzer").update({
                                "passwort_hash": hash_passwort(rst_pw_neu)
                            }).eq("name", rst_name).execute()
                            supabase.table("sessions").delete().eq(
                                "name", rst_name).execute()
                            st.success(
                                f"✅ Passwort für {rst_name} wurde zurückgesetzt. "
                                f"Bitte jetzt einloggen.")
                        else:
                            st.error("❌ Antwort falsch oder kein Account gefunden.")
                    except Exception as e:
                        st.error(f"❌ Fehler: {e}")

        # Sicherheitsfrage anzeigen wenn Name gewählt
        try:
            frage_res = supabase.table("nutzer").select(
                "sicherheitsfrage").eq("name", rst_name).execute()
            if frage_res.data and frage_res.data[0].get("sicherheitsfrage"):
                st.info(f"💬 Deine Frage: *{frage_res.data[0]['sicherheitsfrage']}*")
        except Exception:
            pass

    st.stop()

# Eingeloggt: Nutzer-Info
_user = st.session_state.user

# =============================================================================
# 1. DASHBOARD
# =============================================================================
if st.session_state.view == 'start':

    # Datum + Wochentag
    heute = datetime.now(zoneinfo.ZoneInfo("Europe/Berlin"))
    wt_namen = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    # Logo links, Bild rechts – gleiche Breite
    txt_col, img_col = st.columns([1, 1])
    with img_col:
        if os.path.exists("startbild.jpg"):
    