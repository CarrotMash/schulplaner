import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
import zoneinfo
from supabase import create_client
import os
import uuid

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
if 'bus_halt'          not in st.session_state: st.session_state.bus_halt = None

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
[data-testid="stHorizontalBlock"] button {
    font-size: 0.78rem !important; padding: 0.4rem 0.2rem !important;
    white-space: normal !important; line-height: 1.2 !important;
    min-height: 56px !important;
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

/* Bus-Cards */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    height: 60px !important; white-space: normal !important;
    line-height: 1.3 !important; font-size: 0.85rem !important;
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
# 1. DASHBOARD
# =============================================================================
if st.session_state.view == 'start':

    # Datum + Wochentag
    heute = datetime.now(zoneinfo.ZoneInfo("Europe/Berlin"))
    wt_namen = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    # Bild links, Logo-Block rechts
    img_col, txt_col = st.columns([1, 2])
    with img_col:
        if os.path.exists("startbild.jpg"):
            st.image("startbild.jpg", use_container_width=True)
    with txt_col:
        tag_nr = heute.strftime("%d")
        monat  = heute.strftime("%b").upper()
        jahr   = heute.strftime("%Y")
        wt     = wt_namen[heute.weekday()]
        logo_html = (
            f'<div style="background:linear-gradient(150deg,#FF4B4B,#c0392b);border-radius:16px;padding:14px 16px 12px 16px;box-shadow:0 4px 14px rgba(255,75,75,0.35);">'
            f'<div style="font-size:1.45rem;font-weight:900;color:white;letter-spacing:1px;text-transform:uppercase;line-height:1;">Schul<span style="opacity:0.65;">planer</span></div>'
            f'<div style="height:1px;background:rgba(255,255,255,0.25);margin:8px 0;"></div>'
            f'<div style="display:flex;align-items:flex-end;gap:6px;">'
            f'<div style="background:rgba(255,255,255,0.18);border-radius:10px;padding:4px 10px;text-align:center;min-width:42px;">'
            f'<div style="font-size:1.6rem;font-weight:900;color:white;line-height:1;">{tag_nr}</div>'
            f'<div style="font-size:0.65rem;font-weight:700;color:rgba(255,255,255,0.75);letter-spacing:1px;">{monat} {jahr}</div>'
            f'</div>'
            f'<div style="font-size:0.82rem;font-weight:600;color:rgba(255,255,255,0.85);padding-bottom:4px;">{wt}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(logo_html, unsafe_allow_html=True)

    # Klausur-Frühwarnung
    try:
        res_warn = supabase.table("klausuren").select("*").execute()
        heute_d  = date.today()
        bald = []
        for k in res_warn.data:
            try:
                delta = (date.fromisoformat(k["start_date"]) - heute_d).days
                if 0 <= delta <= 2:
                    bald.append((delta, k))
            except Exception:
                pass
        for delta, k in sorted(bald, key=lambda x: x[0]):
            titel = k["titel"].replace("\n", " · ")
            wann  = {0:"⚡ **heute!**", 1:"⏰ **morgen**"}.get(delta, "📅 **übermorgen**")
            st.warning(f"🔔 Klausur {wann}: **{titel}**")
    except Exception:
        pass

    # Navigations-Buttons 2×2
    r1a, r1b = st.columns(2)
    with r1a:
        if st.button("📅 KLAUSUREN",   use_container_width=True, type="primary", key="btn_kl"):
            st.session_state.view = 'klausuren'; st.rerun()
    with r1b:
        if st.button("🏫 STUNDENPLÄNE", use_container_width=True, type="primary", key="btn_sp"):
            st.session_state.view = 'stundenplan'; st.rerun()
    r2a, r2b = st.columns(2)
    with r2a:
        if st.button("🚌 BUS-CHECK",    use_container_width=True, type="primary", key="btn_bc"):
            st.session_state.view = 'bus'; st.rerun()
    with r2b:
        if st.button("🌴 FERIEN",       use_container_width=True, type="primary", key="btn_fe"):
            st.session_state.view = 'ferien'; st.rerun()

    # --- PINNWAND ---
    st.divider()
    st.markdown("#### 📌 Pinnwand")

    try:
        msgs = supabase.table("nachrichten").select("*").order("created_at", desc=True).limit(10).execute().data
    except Exception:
        msgs = []

    if msgs:
        for msg in msgs:
            farbe = PINNWAND_FARBEN.get(msg.get("name",""), "#888")
            name  = msg.get("name","?")
            text  = msg.get("text","")
            try:
                ts    = datetime.fromisoformat(msg["created_at"].replace("Z","+00:00"))
                zeit  = ts.astimezone(zoneinfo.ZoneInfo("Europe/Berlin")).strftime("%d.%m. %H:%M")
            except Exception:
                zeit = ""
            col_msg, col_del = st.columns([11, 1])
            with col_msg:
                st.markdown(
                    f'<div class="pin-bubble" style="border-left-color:{farbe};">'
                    f'<span class="pin-name" style="color:{farbe};">{name}</span>'
                    f'<span class="pin-zeit">{zeit}</span>'
                    f'<div class="pin-text">{text}</div></div>',
                    unsafe_allow_html=True
                )
            with col_del:
                st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
                if st.button("🗑", key=f"del_msg_{msg['id']}"):
                    supabase.table("nachrichten").delete().eq("id", msg["id"]).execute()
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Noch keine Nachrichten.")

    # Nachricht schreiben – direkt sichtbar
    with st.form("pinnwand_form", clear_on_submit=True):
        pc1, pc2 = st.columns([2, 5])
        with pc1:
            pname = st.selectbox("Von", PINNWAND_NAMEN, label_visibility="collapsed")
        with pc2:
            ptext = st.text_input("Nachricht …", max_chars=200, label_visibility="collapsed")
        if st.form_submit_button("📨 Senden", use_container_width=True):
            if ptext.strip():
                supabase.table("nachrichten").insert({"name": pname, "text": ptext.strip()}).execute()
                st.rerun()

    st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)


# =============================================================================
# 2. KLAUSUREN
# =============================================================================
elif st.session_state.view == 'klausuren':
    try:
        res = supabase.table("klausuren").select("*").execute()
        k_data, k_df = res.data, pd.DataFrame(res.data)
    except Exception:
        k_data, k_df = [], pd.DataFrame()

    page_header("📅 Klausuren")

    zart_gruen = "#C8E6C9"
    holidays = [
        {"title":"Osterferien",    "start":"2025-04-11","end":"2025-04-26","backgroundColor":zart_gruen,"display":"background"},
        {"title":"Sommerferien",   "start":"2025-07-28","end":"2025-09-06","backgroundColor":zart_gruen,"display":"background"},
        {"title":"Herbstferien",   "start":"2025-10-20","end":"2025-10-31","backgroundColor":zart_gruen,"display":"background"},
        {"title":"Weihnachtsferien","start":"2025-12-19","end":"2026-01-06","backgroundColor":zart_gruen,"display":"background"},
        {"title":"Osterferien '26","start":"2026-03-26","end":"2026-04-11","backgroundColor":zart_gruen,"display":"background"},
        {"title":"Sommerferien '26","start":"2026-07-13","end":"2026-08-22","backgroundColor":zart_gruen,"display":"background"},
    ]
    cal_ev = [{"id":str(d["id"]),"title":d["titel"],"start":d["start_date"],
               "backgroundColor":d["color"],"allDay":True,"textColor":"white"} for d in k_data]

    state = calendar(
        events=cal_ev + holidays,
        options={
            "headerToolbar":{"left":"prev,next today","center":"title","right":"dayGridMonth,listMonth"},
            "buttonText":{"today":"Heute","month":"Monat","list":"Liste"},
            "initialView":"dayGridMonth","locale":"de","firstDay":1,
            "weekends":False,"height":"auto","selectable":True,
            "timeZone":"UTC","displayEventTime":False
        },
        key=st.session_state.cal_key
    )

    if state.get("dateClick"):
        if st.session_state.cancel_click:
            st.session_state.cancel_click = False
        else:
            nd = state["dateClick"]["date"][:10]
            if st.session_state.selected_date != nd:
                st.session_state.selected_date = nd; st.session_state.edit_id = None; st.rerun()
    if state.get("eventClick"):
        ni = state["eventClick"]["event"].get("id")
        if st.session_state.edit_id != ni:
            st.session_state.edit_id = ni; st.session_state.selected_date = None; st.rerun()

    # Neu-Eingabe
    if st.session_state.selected_date:
        st.divider()
        datum_fmt = datetime.strptime(st.session_state.selected_date,'%Y-%m-%d').strftime('%d.%m.%Y')
        st.markdown(f"**➕ Neu am {datum_fmt}**")
        with st.form("q_f", clear_on_submit=True):
            qc = st.selectbox("Kind",  list(CHILD_COLORS.keys()))
            qs = st.selectbox("Fach",  SUBJECTS)
            qn = st.text_input("Notiz")
            if st.form_submit_button("💾 Speichern", use_container_width=True):
                supabase.table("klausuren").insert({
                    "datum": datum_fmt, "titel": f"{qc}\n{qs}",
                    "start_date": st.session_state.selected_date,
                    "color": CHILD_COLORS[qc], "child": qc, "note": qn
                }).execute()
                st.success("✅ Gespeichert!")
                st.session_state.selected_date = None
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
        if st.button("✕ Abbrechen", use_container_width=True, key="btn_cancel_new"):
            st.session_state.selected_date = None
            st.session_state.cancel_click  = True; st.rerun()

    # Bearbeiten/Löschen
    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        try:
            edit_row = k_df[k_df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("ed_f"):
                st.markdown("**✏️ Bearbeiten**")
                new_c = st.selectbox("Kind", list(CHILD_COLORS.keys()),
                                     index=list(CHILD_COLORS.keys()).index(edit_row['child']))
                curr_s = edit_row['titel'].split('\n')[-1]
                new_s  = st.selectbox("Fach", SUBJECTS,
                                      index=SUBJECTS.index(curr_s) if curr_s in SUBJECTS else 0)
                new_d  = st.date_input("Datum",
                                       datetime.strptime(edit_row['start_date'],'%Y-%m-%d'),
                                       format="DD.MM.YYYY")
                new_n  = st.text_input("Notiz", value=edit_row['note'])
                c1, c2, c3 = st.columns([3, 3, 1])
                if c1.form_submit_button("💾 Speichern"):
                    supabase.table("klausuren").update({
                        "datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}",
                        "start_date": str(new_d), "color": CHILD_COLORS[new_c],
                        "child": new_c, "note": new_n
                    }).eq("id", st.session_state.edit_id).execute()
                    st.success("✅ Gespeichert!")
                    st.session_state.edit_id = None
                    st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c2.form_submit_button("🗑️ Löschen"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None
                    st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c3.form_submit_button("✕"):
                    st.session_state.edit_id = None; st.rerun()
        except Exception:
            st.session_state.edit_id = None

    # Tabelle bevorstehender Klausuren mit farbigen Labels
    st.divider()
    if not k_df.empty:
        df_t = k_df.copy()
        df_t['start_date_dt'] = pd.to_datetime(df_t['start_date']).dt.date
        df_t = df_t[df_t['start_date_dt'] >= date.today()].sort_values('start_date')
        if not df_t.empty:
            for _, row in df_t.iterrows():
                kind   = row.get('child','')
                fach   = row['titel'].split('\n')[-1] if '\n' in row['titel'] else row['titel']
                farbe  = CHILD_COLORS.get(kind, "#888")
                datum  = row['datum']
                note   = row.get('note','')
                note_html = f'<span style="color:#aaa;font-size:0.78rem;margin-left:6px;">{note}</span>' if note else ''
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;'
                    f'border-bottom:1px solid #f0f0f0;">'
                    f'<span style="background:{farbe};color:white;font-size:0.72rem;font-weight:700;'
                    f'padding:2px 8px;border-radius:20px;white-space:nowrap;">{kind}</span>'
                    f'<span style="font-weight:600;">{fach}</span>'
                    f'<span style="margin-left:auto;color:#888;font-size:0.82rem;white-space:nowrap;">{datum}</span>'
                    f'{note_html}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Keine bevorstehenden Klausuren.")
    else:
        st.info("Keine Einträge vorhanden.")

    back_button()


# =============================================================================
# 3. STUNDENPLÄNE
# =============================================================================
elif st.session_state.view == 'stundenplan':
    page_header("🏫 Stundenpläne")

    # Kind-Auswahl (3 Buttons, immer nebeneinander)
    st.markdown("""
    <style>
    .kind-row > div[data-testid="stColumn"] {
        flex:1 1 0 !important; min-width:0 !important;
    }
    .kind-row > div[data-testid="stColumn"] button {
        font-size:0.88rem !important; padding:0.4rem !important;
        white-space:nowrap !important;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="kind-row">', unsafe_allow_html=True)
    kc = st.columns(3)
    for i, name in enumerate(CHILD_COLORS.keys()):
        aktiv = st.session_state.stundenplan_child == name
        if kc[i].button(name, key=f"cs_{name}", use_container_width=True,
                        type="primary" if aktiv else "secondary"):
            st.session_state.stundenplan_child = name
            st.session_state.editing_grade     = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    cur_c = st.session_state.stundenplan_child

    if cur_c is None:
        st.info("Bitte oben ein Kind auswählen.")
        back_button()
        st.stop()

    # Klasse
    try:
        k_info    = supabase.table("kinder_info").select("klasse").eq("child", cur_c).execute().data
        cur_klasse = k_info[0]['klasse'] if k_info else "Klasse ?"
    except Exception:
        cur_klasse = "Klasse ?"

    if not st.session_state.editing_grade:
        if st.button(f"✏️ {cur_klasse}", use_container_width=True, key="grade_btn"):
            st.session_state.editing_grade = True; st.rerun()
    else:
        with st.form("grade_form"):
            new_g = st.text_input("Klasse anpassen:", value=cur_klasse)
            if st.form_submit_button("Speichern"):
                supabase.table("kinder_info").upsert({"child": cur_c, "klasse": new_g}).execute()
                st.session_state.editing_grade = False; st.rerun()

    res       = supabase.table("stundenplaene").select("*").eq("child", cur_c).execute()
    plan_dict = {(item['tag'], int(item['stunde'])): item for item in res.data}

    # Wochentag-Buttons (Mo Di Mi Do Fr)
    day_short = {"Montag":"Mo","Dienstag":"Di","Mittwoch":"Mi","Donnerstag":"Do","Freitag":"Fr"}
    dc = st.columns(5)
    for i, day in enumerate(DAYS):
        aktiv = st.session_state.stundenplan_day == day
        if dc[i].button(day_short[day], key=f"day_{day}", use_container_width=True,
                        type="primary" if aktiv else "secondary"):
            st.session_state.stundenplan_day = day
            if 'edit_cell' in st.session_state:
                del st.session_state.edit_cell
            st.rerun()

    cur_day = st.session_state.stundenplan_day
    kind_farbe = CHILD_COLORS.get(cur_c, "#333")

    # Kompakte HTML-Tabelle
    rows = ""
    for std in range(1, 8):
        lesson = plan_dict.get((cur_day, std))
        fach   = lesson['fach'] if lesson else "—"
        f_col  = kind_farbe if fach != "—" else "#ccc"
        rows  += (f'<tr>'
                  f'<td class="std-nr">{std}.</td>'
                  f'<td class="fach" style="color:{f_col};">{fach}</td>'
                  f'<td class="uhr">{TIMES[std]}</td>'
                  f'</tr>')
    st.markdown(f'<table class="sp-table">{rows}</table>', unsafe_allow_html=True)

    # Edit-Buttons 1–7
    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
    ec_cols = st.columns(7)
    for idx, std in enumerate(range(1, 8)):
        lesson = plan_dict.get((cur_day, std))
        fach   = lesson['fach'] if lesson else "---"
        if ec_cols[idx].button(str(std), key=f"ec_{cur_c}_{cur_day}_{std}",
                               use_container_width=True):
            st.session_state.edit_cell = {
                "day": cur_day, "std": std, "fach": fach,
                "id": lesson['id'] if lesson else None
            }
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("↑ Stundennummer antippen zum Bearbeiten")

    if 'edit_cell' in st.session_state:
        ec = st.session_state.edit_cell
        st.divider()
        with st.form("ed_p"):
            st.markdown(f"**📌 {ec['day']}, {ec['std']}. Stunde ({TIMES[ec['std']]})**")
            new_f = st.selectbox("Fach", SUBJECTS,
                                 index=SUBJECTS.index(ec['fach']) if ec['fach'] in SUBJECTS else 0)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Speichern"):
                if ec['id']:
                    supabase.table("stundenplaene").update({"fach": new_f}).eq("id", ec['id']).execute()
                else:
                    supabase.table("stundenplaene").insert({
                        "child": cur_c, "tag": ec['day'],
                        "stunde": ec['std'], "fach": new_f
                    }).execute()
                st.success("✅ Gespeichert!")
                del st.session_state.edit_cell; st.rerun()
            if c2.form_submit_button("✕ Abbrechen"):
                del st.session_state.edit_cell; st.rerun()

    back_button()


# =============================================================================
# 4. BUS-CHECK
# =============================================================================
elif st.session_state.view == 'bus':
    page_header("🚌 Bus-Check")

    st.markdown("""
    <div style="text-align:center; padding: 40px 20px 30px 20px;">
        <div style="font-size:4rem; margin-bottom:16px;">🚧</div>
        <div style="font-size:1.3rem; font-weight:800; color:#444; margin-bottom:10px;">
            Hier wird noch gearbeitet
        </div>
        <div style="font-size:0.95rem; color:#888; max-width:280px; margin:0 auto; line-height:1.6;">
            Wir arbeiten daran, Echtzeit-Abfahrtszeiten inkl. Verspätungen 
            einzubinden. Bitte schau bald wieder rein!
        </div>
        <div style="margin-top:24px; font-size:0.8rem; color:#bbb;">
            Aktuell verfügbar: 
            <a href="https://www.nah.sh" target="_blank" style="color:#FF4B4B;">nah.sh Fahrplanauskunft</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    back_button()


# =============================================================================
# 5. FERIEN
# =============================================================================
elif st.session_state.view == 'ferien':
    page_header("🌴 Ferien S-H")

    heute = date.today()

    # Countdown zur nächsten Ferienperiode
    nf = naechste_ferien()
    if nf:
        if nf["start"] <= heute <= nf["end"]:
            tage_noch = (nf["end"] - heute).days
            st.markdown(
                f'<div class="countdown-box">'
                f'<div class="cd-label">🎉 Wir haben gerade Ferien!</div>'
                f'<div class="cd-days">{tage_noch}</div>'
                f'<div class="cd-name">Tage noch frei</div>'
                f'<div class="cd-name" style="font-size:0.95rem;margin-top:6px;">{nf["name"]} {nf["start"].year}</div>'
                f'<div class="cd-date">bis {nf["end"].strftime("%d.%m.%Y")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            tage_bis = (nf["start"] - heute).days
            st.markdown(
                f'<div class="countdown-box">'
                f'<div class="cd-label">⏳ Noch</div>'
                f'<div class="cd-days">{tage_bis}</div>'
                f'<div class="cd-name">Tag{"e" if tage_bis!=1 else ""}</div>'
                f'<div class="cd-name" style="font-size:0.95rem;margin-top:6px;">bis zu den {nf["name"]} {nf["start"].year}</div>'
                f'<div class="cd-date">Start am {nf["start"].strftime("%d.%m.%Y")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Zeitleiste aller Ferien
    st.markdown("#### Alle Ferien im Überblick")
    for f in FERIEN_LIST:
        jahr  = f["start"].year
        lbl   = f'{f["name"]} {jahr}'
        start_fmt = f["start"].strftime("%d.%m.")
        end_fmt   = f["end"].strftime("%d.%m.%Y")
        tage  = (f["end"] - f["start"]).days + 1

        if f["end"] < heute:
            css = "vorbei"
            badge = '<span class="fi-badge" style="background:#eee;color:#aaa;">vorbei</span>'
        elif f["start"] <= heute <= f["end"]:
            css = "aktiv"
            badge = f'<span class="fi-badge" style="background:#FF4B4B;color:white;">🎉 jetzt!</span>'
        else:
            delta = (f["start"] - heute).days
            css   = ""
            badge = (f'<span class="fi-badge" style="background:#FFF3E0;color:#E65100;">'
                     f'in {delta} Tagen</span>')

        st.markdown(
            f'<div class="ferien-item {css}">'
            f'<div>'
            f'<div class="fi-name">{lbl}</div>'
            f'<div class="fi-date">{start_fmt} – {end_fmt} · {tage} Tage</div>'
            f'</div>'
            f'{badge}'
            f'</div>',
            unsafe_allow_html=True
        )

    st.caption("Alle Angaben ohne Gewähr · Schulferien Schleswig-Holstein")
    back_button()