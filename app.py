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
if 'active_msg'        not in st.session_state: st.session_state.active_msg   = None
if 'bus_halt'          not in st.session_state: st.session_state.bus_halt = None
if 'quiz_name'         not in st.session_state: st.session_state.quiz_name = None
if 'quiz_phase'        not in st.session_state: st.session_state.quiz_phase = 'name'
if 'quiz_fragen'       not in st.session_state: st.session_state.quiz_fragen = []
if 'quiz_idx'          not in st.session_state: st.session_state.quiz_idx = 0
if 'quiz_punkte'       not in st.session_state: st.session_state.quiz_punkte = {}
if 'quiz_antwort'      not in st.session_state: st.session_state.quiz_antwort = None

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
            st.image("startbild.jpg", use_container_width=True)
    with txt_col:
        tag_nr = heute.strftime("%d")
        monat  = heute.strftime("%b").upper()
        jahr   = heute.strftime("%Y")
        wt     = wt_namen[heute.weekday()]
        logo_html = (
            f'<div style="background:linear-gradient(150deg,#FF4B4B,#c0392b);border-radius:16px;'
            f'padding:14px 16px 12px 16px;box-shadow:0 4px 14px rgba(255,75,75,0.35);'
            f'height:100%;min-height:140px;display:flex;flex-direction:column;justify-content:space-between;">'
            f'<div style="font-size:1.9rem;font-weight:900;color:white;letter-spacing:2px;text-transform:uppercase;line-height:1.1;">SCHUL<br><span style="opacity:0.6;">PLANER</span></div>'
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

    # Klausur-Frühwarnung – volle Breite unterhalb von Logo + Bild
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
            icon  = {0: "⚡", 1: "⏰"}.get(delta, "📅")
            wann  = {0: "heute!", 1: "morgen"}.get(delta, "übermorgen")
            st.markdown(
                f'<div style="margin-top:8px;background:#FF6F00;border-radius:8px;'
                f'padding:8px 12px;font-size:0.85rem;color:#FFFFFF !important;">'
                f'<b style="color:#FFFFFF;">{icon} Klausur {wann}:</b> {titel}'
                f'</div>',
                unsafe_allow_html=True
            )
    except Exception:
        pass

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    # Navigations-Buttons – alle 6 als native Streamlit-Buttons
    # Einheitliches Aussehen via globalem CSS (roter Hintergrund, weiße Schrift)
    # Zeile 1
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📅 KLAUSUREN", key="btn_klausuren", use_container_width=True):
            st.session_state.view = 'klausuren'; st.rerun()
    with c2:
        if st.button("🏫 STUNDENPLÄNE", key="btn_stundenplan", use_container_width=True):
            st.session_state.view = 'stundenplan'; st.rerun()
    # Zeile 2
    c3, c4 = st.columns(2)
    with c3:
        if st.button("🚌 BUS-CHECK", key="btn_bus", use_container_width=True):
            st.session_state.view = 'bus'; st.rerun()
    with c4:
        if st.button("🌴 FERIEN", key="btn_ferien", use_container_width=True):
            st.session_state.view = 'ferien'; st.rerun()
    # Zeile 3: Vokabel-Quiz + Wordle nebeneinander
    c5, c6 = st.columns(2)
    with c5:
        if st.button("🧠 VOKABEL-QUIZ", key="btn_quiz", use_container_width=True):
            st.session_state.view = 'quiz'
            st.session_state.quiz_phase = 'name'; st.rerun()
    with c6:
        # HTML-Link mit exakt gleichem Inline-Style wie die Streamlit-Buttons
        st.markdown(
            '<a href="https://6mal5.com" target="_blank" style="'
            'display:flex;align-items:center;justify-content:center;'
            'width:100%;min-height:44px;'
            'background-color:#FF4B4B;color:white !important;'
            'font-size:0.72rem;font-weight:700;line-height:1.15;'
            'border:none;border-radius:8px;'
            'text-decoration:none;cursor:pointer;'
            'box-sizing:border-box;padding:6px 4px;margin-top:4px;'
            '">🟩 WORDLE</a>',
            unsafe_allow_html=True
        )



    # --- PINNWAND ---
    st.divider()
    st.markdown("#### 📌 Pinnwand")

    try:
        msgs = supabase.table("nachrichten").select("*").order("created_at", desc=True).limit(10).execute().data
    except Exception:
        msgs = []

    if msgs:
        for msg in msgs:
            farbe   = PINNWAND_FARBEN.get(msg.get("name",""), "#888")
            name    = msg.get("name","?")
            text    = msg.get("text","")
            mid     = msg['id']
            aktiv   = st.session_state.active_msg == mid
            try:
                ts   = datetime.fromisoformat(msg["created_at"].replace("Z","+00:00"))
                datum_str = ts.astimezone(zoneinfo.ZoneInfo("Europe/Berlin")).strftime("%d.%m.")
                uhr_str   = ts.astimezone(zoneinfo.ZoneInfo("Europe/Berlin")).strftime("%H:%M")
                zeit      = f"{datum_str} um {uhr_str}"
            except Exception:
                zeit = ""

            rand   = f"2px solid {farbe}" if aktiv else f"1px solid #eee"
            bg     = "#fff" if aktiv else "#f8f8f8"

            # Nachricht anklicken → aktiviert Löschoption
            btn_label = f"👤 {name} – {zeit}: {text}"
            if st.button(
                btn_label,
                key=f"msg_btn_{mid}",
                use_container_width=True,
            ):
                st.session_state.active_msg = None if aktiv else mid
                st.rerun()

            # Lösch- und Abbrechen-Button nur bei aktiver Nachricht
            if aktiv:
                ca, cb = st.columns(2)
                with ca:
                    if st.button("🗑 Löschen", key=f"del_{mid}",
                                 use_container_width=True, type="primary"):
                        supabase.table("nachrichten").delete().eq("id", mid).execute()
                        st.session_state.active_msg = None
                        st.rerun()
                with cb:
                    if st.button("✕ Abbrechen", key=f"cancel_{mid}",
                                 use_container_width=True):
                        st.session_state.active_msg = None
                        st.rerun()
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

    from datetime import timedelta as _td

    # -----------------------------------------------------------------------
    # FAHRPLANDATEN Mo–Fr, Quelle: VKP PDF 200i/210i, Stand 21.11.2024
    # Format: (Abfahrtszeit HH:MM, Linie, Richtung/Ausstieg)
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # FAHRPLANDATEN Mo–Fr · Quelle: VKP PDF 200i/200ii/210i · Stand 27.11.2024
    # Direkt abgelesen aus aktuellen PDFs auf vkp.de (für 2026 unverändert)
    # Format: (Abfahrtszeit, Linie, Ausstieg)
    # 30er-Fahrten (umgekehrte Route) und H-Fahrten (nur Ferientage) ausgelassen
    # E-Fahrten (nur Schultage) sind enthalten da App primär für Schüler
    # -----------------------------------------------------------------------
    FAHRPLAN = {
        "seefisch": {
            "label":    "Seefischmarkt",
            "icon":     "🏠",
            "sub":      "→ Schönkirchen",
            "richtung": "Richtung Schönkirchen / Schönberg",
            "zeiten": [
                # Linie 201 (direkt): FahrtNr 201xx, kein Söhren-Halt
                # Linie 200 (via Söhren): FahrtNr 200xx
                # Linie 210 (via Amboßweg/Tökendorf): FahrtNr 210xx
                ("05:52", "200", "Linas Diek"),   # 20130
                ("06:22", "201", "Linas Diek"),   # 20102
                ("06:37", "201", "Linas Diek"),   # 20104
                ("06:52", "200", "Linas Diek"),   # 20004
                ("07:07", "200", "Linas Diek"),   # 20006 [E]
                ("07:22", "201", "Linas Diek"),   # 20106
                ("07:37", "200", "Linas Diek"),   # 20008 [E]
                ("07:52", "200", "Linas Diek"),   # 20010
                ("08:07", "200", "Linas Diek"),   # 20012
                ("08:22", "201", "Linas Diek"),   # 20108
                ("08:37", "200", "Linas Diek"),   # 20014
                ("08:52", "200", "Linas Diek"),   # 20016
                ("09:22", "201", "Linas Diek"),   # 20110
                ("09:52", "200", "Linas Diek"),   # 20018
                ("10:22", "201", "Linas Diek"),   # 20112
                ("10:52", "200", "Linas Diek"),   # 20020
                ("11:22", "201", "Linas Diek"),   # 20114
                ("11:52", "200", "Linas Diek"),   # 20022
                ("12:22", "201", "Linas Diek"),   # 20116 (210 fährt separat)
                ("12:52", "200", "Linas Diek"),   # 20024
                ("13:22", "201", "Linas Diek"),   # 20118 (E)
                ("13:52", "200", "Linas Diek"),   # 20028 (H) → 20030
                ("14:22", "201", "Linas Diek"),   # 20120 (E)
                ("14:52", "200", "Linas Diek"),   # 20034
                ("15:07", "200", "Linas Diek"),   # 20036 [E]
                ("15:22", "201", "Linas Diek"),   # 20122
                ("15:52", "200", "Linas Diek"),   # 20038
                ("16:07", "200", "Linas Diek"),   # 20040 [E]
                ("16:22", "201", "Linas Diek"),   # 20124 (E) → 20126 (Schule)
                ("16:52", "200", "Linas Diek"),   # 20042
                ("17:22", "201", "Linas Diek"),   # 20126
                ("17:52", "200", "Linas Diek"),   # 20048
                # 210er separat
                ("07:37", "210", "Amboßweg"),     # 21002
                ("09:37", "210", "Amboßweg"),     # 21004 [E]
                ("11:37", "210", "Amboßweg"),     # 21002
                ("13:37", "210", "Amboßweg"),     # 21008
                ("15:37", "210", "Amboßweg"),     # 21012
                ("17:37", "210", "Amboßweg"),     # 21016
            ],
        },
        "linas": {
            "label":    "Linas Diek",
            "icon":     "🏫",
            "sub":      "→ Seefischmarkt",
            "richtung": "Richtung Kiel Seefischmarkt",
            "zeiten": [
                # Direkt aus 200ii.pdf Spalte "Schönkirchen, Lina's Diek"
                ("05:18", "200", "Seefischmarkt"),  # 20001 [30]
                ("05:31", "201", "Seefischmarkt"),  # 20103
                ("06:15", "201", "Seefischmarkt"),  # 20105
                ("06:38", "200", "Seefischmarkt"),  # 20003 [30]
                ("06:45", "201", "Seefischmarkt"),  # 20107
                ("07:30", "201", "Seefischmarkt"),  # 20109 [E]
                ("07:33", "200", "Seefischmarkt"),  # 20011 [E]
                ("08:09", "201", "Seefischmarkt"),  # 20113
                ("08:15", "201", "Seefischmarkt"),  # 20111
                ("09:30", "201", "Seefischmarkt"),  # 20115
                ("09:43", "200", "Seefischmarkt"),  # 20015
                ("10:30", "201", "Seefischmarkt"),  # 20117
                ("10:43", "200", "Seefischmarkt"),  # 20017
                ("11:30", "201", "Seefischmarkt"),  # 20121
                ("11:43", "200", "Seefischmarkt"),  # 20019
                ("12:30", "201", "Seefischmarkt"),  # 20123
                ("12:43", "200", "Seefischmarkt"),  # 20023
                ("13:30", "201", "Seefischmarkt"),  # 20125
                ("13:43", "200", "Seefischmarkt"),  # 20025 [E]
                ("14:30", "201", "Seefischmarkt"),  # 20127
                ("14:38", "200", "Seefischmarkt"),  # 20029
                ("15:30", "201", "Seefischmarkt"),  # 20129
                ("15:43", "200", "Seefischmarkt"),  # 20035
                ("16:10", "201", "Seefischmarkt"),  # 20131
                ("16:30", "201", "Seefischmarkt"),  # 20133
                ("16:43", "200", "Seefischmarkt"),  # 20043
                ("17:10", "201", "Seefischmarkt"),  # 20135 [E]
                ("17:30", "201", "Seefischmarkt"),  # 20137
                ("17:38", "200", "Seefischmarkt"),  # 20051
                ("18:30", "201", "Seefischmarkt"),  # 20141
            ],
        },
        "amboss": {
            "label":    "Amboßweg",
            "icon":     "🏫",
            "sub":      "→ Seefischmarkt",
            "richtung": "Richtung Kiel Seefischmarkt",
            "zeiten": [
                # Direkt aus 210i.pdf Spalte "Schönkirchen, Amboßweg"
                ("06:07", "210", "Seefischmarkt"),
                ("07:07", "210", "Seefischmarkt"),
                ("08:17", "210", "Seefischmarkt"),
                ("12:22", "210", "Seefischmarkt"),
                ("14:22", "210", "Seefischmarkt"),
            ],
        },
    }

    LINE_COLORS  = {"200":"#C62828","201":"#1565C0","210":"#2E7D32"}
    LINE_BGLIGHT = {"200":"#FFEBEE","201":"#E3F2FD","210":"#E8F5E9"}

    def naechste_3(zeiten, jetzt):
        """Gibt die 3 nächsten Abfahrten ab jetzt zurück (inkl. heute + nächster Werktag)."""
        heute_str = jetzt.strftime("%H:%M")
        # Heutige Abfahrten ab jetzt
        treffer = [(z, li, ri) for z, li, ri in zeiten if z >= heute_str]
        if len(treffer) >= 3:
            return treffer[:3], False
        # Aufgefüllt mit ersten Fahrten des nächsten Tages
        rest = 3 - len(treffer)
        naechste = [(z, li, ri) for z, li, ri in zeiten][:rest]
        return treffer + naechste, len(treffer) < 3

    def bus_card_static(zeit, linie, richtung, jetzt, ist_erste, naechster_tag=False):
        farbe = LINE_COLORS.get(linie, "#555")
        bg    = LINE_BGLIGHT.get(linie, "#f9f9f9")
        rand  = f"3px solid {farbe}" if ist_erste else f"1px solid #eee"

        # Countdown berechnen
        try:
            h, m   = map(int, zeit.split(":"))
            abf_dt = jetzt.replace(hour=h, minute=m, second=0, microsecond=0)
            if naechster_tag or abf_dt < jetzt:
                abf_dt += _td(days=1)
            diff   = int((abf_dt - jetzt).total_seconds() / 60)
            if diff == 0:
                cd_html = f'<span style="color:{farbe};font-weight:800;">jetzt!</span>'
            elif diff < 60:
                cd_html = f'<span style="color:{farbe};font-weight:700;">in {diff} Min.</span>'
            else:
                h2, m2  = divmod(diff, 60)
                cd_html = f'<span style="color:{farbe};font-weight:700;">in {h2}h {m2:02d}m</span>'
        except Exception:
            cd_html = ""

        naechster_tag_badge = (
            '<span style="background:#888;color:white;font-size:0.68rem;padding:1px 6px;'
            'border-radius:8px;margin-left:6px;">nächster Tag</span>' if naechster_tag else ""
        )
        erste_badge = (
            f'<span style="background:{farbe};color:white;font-size:0.68rem;font-weight:700;'
            f'padding:1px 7px;border-radius:8px;margin-left:6px;">▶ Nächste</span>' if ist_erste else ""
        )

        st.markdown(
            f'<div style="background:{bg};border:{rand};border-left:6px solid {farbe};'
            f'border-radius:12px;padding:12px 16px 10px 16px;margin-bottom:10px;'
            f'box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="min-width:0;">'
            f'<span style="font-size:1.6rem;font-weight:900;color:{farbe};">{zeit}</span>'
            f'<span style="background:{farbe};color:white;font-size:0.82rem;font-weight:700;'
            f'padding:2px 10px;border-radius:6px;margin-left:8px;white-space:nowrap;">Linie {linie}</span>'
            f'</div>'
            f'<div style="text-align:right;flex-shrink:0;margin-left:8px;">{cd_html}</div>'
            f'</div>'
            f'{("<div style=\"margin-top:4px;\">" + erste_badge + naechster_tag_badge + "</div>") if (erste_badge or naechster_tag_badge) else ""}'
            f'<div style="margin-top:6px;font-size:0.88rem;">'
            f'<span style="color:#555 !important;">🚏 Ausstieg: </span>'
            f'<b style="color:#222 !important;">{richtung}</b>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Haltestellen-Buttons – ohne Icons, kompakter Text für Smartphone
    bc = st.columns(3)
    for i, (key, cfg) in enumerate(FAHRPLAN.items()):
        aktiv = st.session_state.bus_halt == key
        with bc[i]:
            if st.button(
                f"{cfg['label']}\n{cfg['sub']}",
                key=f"bus_btn_{key}",
                use_container_width=True,
                type="primary" if aktiv else "secondary"
            ):
                st.session_state.bus_halt = key
                st.rerun()

    st.divider()

    if st.session_state.bus_halt:
        cfg  = FAHRPLAN[st.session_state.bus_halt]
        now  = datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).replace(tzinfo=None)
        wt   = now.weekday()
        WT   = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

        st.caption(
            f"📍 **{cfg['label']}** · {cfg['richtung']} · "
            f"Mo–Fr · Stand: VKP Nov. 2024"
        )

        if wt >= 5:
            # Wochenende
            tage = 2 if wt == 5 else 1
            nwt  = now + _td(days=tage)
            st.warning(
                f"⚠️ Dieser Fahrplan gilt Mo–Fr. "
                f"Nächste Fahrten: **{WT[nwt.weekday()]}, {nwt.strftime('%d.%m.')}**"
            )
            treffer = [(z, li, ri) for z, li, ri in cfg["zeiten"]][:3]
            for i, (z, li, ri) in enumerate(treffer):
                bus_card_static(z, li, ri, now, i == 0, naechster_tag=True)
        else:
            treffer, hat_uebertrag = naechste_3(cfg["zeiten"], now)
            if not treffer:
                st.info("Keine Abfahrten gefunden.")
            else:
                for i, (z, li, ri) in enumerate(treffer):
                    ist_uebertrag = hat_uebertrag and i >= (3 - (3 - len(
                        [(z2,l2,r2) for z2,l2,r2 in cfg["zeiten"]
                         if z2 >= now.strftime("%H:%M")]
                    )))
                    bus_card_static(z, li, ri, now, i == 0,
                                    naechster_tag=(hat_uebertrag and
                                                   z < now.strftime("%H:%M")))

        if st.button("🔄 Aktualisieren", use_container_width=True, key="bus_refresh"):
            st.rerun()
    else:
        st.markdown(
            "<div style='text-align:center;color:#aaa;padding:30px 0;font-size:1.1rem;'>"
            "⬆️ Bitte Haltestelle auswählen</div>",
            unsafe_allow_html=True
        )

    back_button()


# =============================================================================
# 6. VOKABEL-QUIZ
# =============================================================================
elif st.session_state.view == 'quiz':
    page_header("🧠 Vokabel-Quiz")

    import random as _rnd
    import hashlib as _hl

    # -----------------------------------------------------------------------
    # VOKABELLISTEN (Schulwortschatz A2-B1)
    # -----------------------------------------------------------------------
    VOKABELN = {
        "en": [
            # B1-B2 Niveau: weniger offensichtliche Vokabeln
            ("Errungenschaft","achievement"),("Bekanntmachung","announcement"),
            ("Verhalten","behaviour"),("Grenze","boundary"),("Herausforderung","challenge"),
            ("Umstand","circumstance"),("Zusammenarbeit","collaboration"),
            ("Konsequenz","consequence"),("Beitrag","contribution"),("Überzeugung","conviction"),
            ("Entscheidend","crucial"),("Enttäuschung","disappointment"),
            ("Eindruck","impression"),("Einfluss","influence"),("Initiative","initiative"),
            ("Einblick","insight"),("Absicht","intention"),("Untersuchung","investigation"),
            ("Urteil","judgment"),("Wissen","knowledge"),("Führung","leadership"),
            ("Motivation","motivation"),("Gelegenheit","opportunity"),("Wahrnehmung","perception"),
            ("Perspektive","perspective"),("Vorliebe","preference"),("Priorität","priority"),
            ("Verfahren","procedure"),("Beziehung","relationship"),("Verantwortung","responsibility"),
            ("Lösung","solution"),("Strategie","strategy"),("Struktur","structure"),
            ("Vorschlag","suggestion"),("Unterstützung","support"),("Tendenz","tendency"),
            ("Verständnis","understanding"),("Wert","value"),("Verschiedenheit","variety"),
            ("Verletzlich","vulnerable"),("Überwindung","achievement"),("Bewusstsein","awareness"),
            ("Fähigkeit","capability"),("Komplexität","complexity"),("Widerspruch","contradiction"),
            ("Glaubwürdigkeit","credibility"),("Bestimmt","determined"),("Effizient","efficient"),
            ("Wesentlich","essential"),("Flexibel","flexible"),("Erheblich","significant"),
            ("Nachhaltig","sustainable"),("Transparent","transparent"),("Unbestreitbar","undeniable"),
            ("Unerwünscht","unwanted"),("Wertvoll","valuable"),("Weit verbreitet","widespread"),
            ("Abschwächen","mitigate"),("Voraussehen","anticipate"),("Einschätzen","assess"),
            ("Koordinieren","coordinate"),("Delegieren","delegate"),("Betonen","emphasise"),
            ("Erleichtern","facilitate"),("Identifizieren","identify"),("Integrieren","integrate"),
            ("Rechtfertigen","justify"),("Aufrechterhalten","maintain"),("Verhandeln","negotiate"),
            ("Optimieren","optimise"),("Überwinden","overcome"),("Priorisieren","prioritise"),
            ("Erkennen","recognise"),("Stärken","strengthen"),("Transformieren","transform"),
            ("Überprüfen","verify"),("Visualisieren","visualise"),("Erzielen","achieve"),
            ("Anpassen","adapt"),("Bewerten","evaluate"),("Implementieren","implement"),
        ],
        "fr": [
            ("Hund","chien"),("Katze","chat"),("Haus","maison"),("Schule","école"),
            ("Freund","ami"),("Familie","famille"),("Essen","nourriture"),("Wasser","eau"),
            ("Buch","livre"),("Zeit","temps"),("Jahr","année"),("Tag","jour"),
            ("Mensch","personne"),("Hand","main"),("Land","pays"),("Stadt","ville"),
            ("Arbeit","travail"),("Leben","vie"),("Kind","enfant"),("Wort","mot"),
            ("Straße","rue"),("Auto","voiture"),("Geld","argent"),("Tür","porte"),
            ("Tisch","table"),("Stuhl","chaise"),("Fenster","fenêtre"),("Bett","lit"),
            ("Küche","cuisine"),("Garten","jardin"),("Sonne","soleil"),("Mond","lune"),
            ("Regen","pluie"),("Wind","vent"),("Baum","arbre"),("Blume","fleur"),
            ("Vogel","oiseau"),("Fisch","poisson"),("Pferd","cheval"),("Kuh","vache"),
            ("Brot","pain"),("Milch","lait"),("Apfel","pomme"),("Fleisch","viande"),
            ("Musik","musique"),("Sport","sport"),("Film","film"),("Spiel","jeu"),
            ("Farbe","couleur"),("Rot","rouge"),("Blau","bleu"),("Grün","vert"),
            ("Groß","grand"),("Klein","petit"),("Neu","nouveau"),("Alt","vieux"),
            ("Gut","bien"),("Schlecht","mauvais"),("Schnell","rapide"),("Langsam","lent"),
            ("Öffnen","ouvrir"),("Schließen","fermer"),("Kaufen","acheter"),("Verkaufen","vendre"),
            ("Lernen","apprendre"),("Lehren","enseigner"),("Lesen","lire"),("Schreiben","écrire"),
            ("Laufen","courir"),("Gehen","marcher"),("Kommen","venir"),("Fahren","aller"),
            ("Sehen","voir"),("Hören","entendre"),("Sprechen","parler"),("Fragen","demander"),
            ("Antworten","répondre"),("Helfen","aider"),("Brauchen","avoir besoin"),("Wollen","vouloir"),
        ],
        "es": [
            ("Hund","perro"),("Katze","gato"),("Haus","casa"),("Schule","escuela"),
            ("Freund","amigo"),("Familie","familia"),("Essen","comida"),("Wasser","agua"),
            ("Buch","libro"),("Zeit","tiempo"),("Jahr","año"),("Tag","día"),
            ("Mensch","persona"),("Hand","mano"),("Land","país"),("Stadt","ciudad"),
            ("Arbeit","trabajo"),("Leben","vida"),("Kind","niño"),("Wort","palabra"),
            ("Straße","calle"),("Auto","coche"),("Geld","dinero"),("Tür","puerta"),
            ("Tisch","mesa"),("Stuhl","silla"),("Fenster","ventana"),("Bett","cama"),
            ("Küche","cocina"),("Garten","jardín"),("Sonne","sol"),("Mond","luna"),
            ("Regen","lluvia"),("Wind","viento"),("Baum","árbol"),("Blume","flor"),
            ("Vogel","pájaro"),("Fisch","pez"),("Pferd","caballo"),("Kuh","vaca"),
            ("Brot","pan"),("Milch","leche"),("Apfel","manzana"),("Fleisch","carne"),
            ("Musik","música"),("Sport","deporte"),("Film","película"),("Spiel","juego"),
            ("Farbe","color"),("Rot","rojo"),("Blau","azul"),("Grün","verde"),
            ("Groß","grande"),("Klein","pequeño"),("Neu","nuevo"),("Alt","viejo"),
            ("Gut","bueno"),("Schlecht","malo"),("Schnell","rápido"),("Langsam","lento"),
            ("Öffnen","abrir"),("Schließen","cerrar"),("Kaufen","comprar"),("Verkaufen","vender"),
            ("Lernen","aprender"),("Lehren","enseñar"),("Lesen","leer"),("Schreiben","escribir"),
            ("Laufen","correr"),("Gehen","caminar"),("Kommen","venir"),("Fahren","ir"),
            ("Sehen","ver"),("Hören","escuchar"),("Sprechen","hablar"),("Fragen","preguntar"),
            ("Antworten","responder"),("Helfen","ayudar"),("Brauchen","necesitar"),("Wollen","querer"),
        ],
    }

    SPRACHE_NAMEN = {"en": "🇬🇧 Englisch", "fr": "🇫🇷 Französisch", "es": "🇪🇸 Spanisch"}
    FRAGEN_PRO_SPRACHE = 5

    def tages_seed():
        """Gleicher Seed für alle Geräte am selben Tag → gleiche Vokabeln."""
        return int(_hl.md5(str(date.today()).encode()).hexdigest(), 16)

    def generiere_fragen():
        """Generiert 15 Fragen (5 je Sprache) — täglich gleich für alle."""
        _rnd.seed(tages_seed())
        fragen = []
        for spr, vokabeln in VOKABELN.items():
            auswahl = _rnd.sample(vokabeln, FRAGEN_PRO_SPRACHE)
            for de, fremd in auswahl:
                # 4 falsche Antworten aus derselben Sprache
                falsche_pool = [f for d, f in vokabeln if f != fremd]
                falsche = _rnd.sample(falsche_pool, 4)
                optionen = falsche + [fremd]
                _rnd.shuffle(optionen)
                fragen.append({
                    "sprache":  spr,
                    "frage_de": de,
                    "richtig":  fremd,
                    "optionen": optionen,
                })
        # Fragen nach Sprache gruppiert
        return fragen

    # -----------------------------------------------------------------------
    # PHASE 1: NAMENSAUSWAHL
    # -----------------------------------------------------------------------
    if st.session_state.quiz_phase == 'name':
        st.markdown("#### Wer spielt heute?")
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

        # Heutigen Highscore laden
        try:
            heute_res = supabase.table("quiz_ergebnisse").select("*").eq(
                "datum", str(date.today())).order("punkte", desc=True).execute()
            heute_scores = {r["name"]: r["punkte"] for r in heute_res.data}
        except Exception:
            heute_scores = {}

        # Bereits gespielt heute?
        cols = st.columns(2)
        for i, name in enumerate(PINNWAND_NAMEN):
            farbe  = PINNWAND_FARBEN.get(name, "#888")
            punkte = heute_scores.get(name)
            label  = f"✅ {name} ({punkte} Pkt.)" if punkte is not None else name
            with cols[i % 2]:
                if st.button(label, key=f"quiz_name_{name}",
                             use_container_width=True,
                             type="secondary" if punkte is not None else "primary"):
                    st.session_state.quiz_name   = name
                    st.session_state.quiz_fragen = generiere_fragen()
                    st.session_state.quiz_idx    = 0
                    st.session_state.quiz_punkte = {}
                    st.session_state.quiz_phase  = 'frage'
                    st.session_state.quiz_antwort = None
                    st.rerun()

        # Wochenrangliste
        try:
            from datetime import timedelta as _td2
            montag = date.today() - timedelta(days=date.today().weekday())
            week_res = supabase.table("quiz_ergebnisse").select("name,punkte,datum").gte(
                "datum", str(montag)).execute()
            if week_res.data:
                st.divider()
                st.markdown("#### 🏆 Woche")
                # Pro Name: Summe der BESTEN Ergebnisse (max 1 pro Tag)
                # Zuerst pro (name, datum) das Maximum nehmen, dann summieren
                best_per_day = {}
                for r in week_res.data:
                    key = (r["name"], r.get("datum", ""))
                    if key not in best_per_day or r["punkte"] > best_per_day[key]:
                        best_per_day[key] = r["punkte"]
                week_sum = {}
                for (n, _), p in best_per_day.items():
                    week_sum[n] = week_sum.get(n, 0) + p
                rang = sorted(week_sum.items(), key=lambda x: x[1], reverse=True)
                medals = ["🥇","🥈","🥉","4.","5."]
                for idx2, (n, p) in enumerate(rang):
                    farbe2 = PINNWAND_FARBEN.get(n, "#888")
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:8px 12px;border-radius:8px;margin-bottom:5px;'
                        f'background:white;border-left:4px solid {farbe2};'
                        f'box-shadow:0 1px 3px rgba(0,0,0,0.08);">'
                        f'<span style="color:#111;font-size:0.95rem;">{medals[idx2]} '
                        f'<b style="color:{farbe2};">{n}</b></span>'
                        f'<span style="font-weight:800;color:#111;">{p} <span style="color:{farbe2};">Pkt.</span></span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # PHASE 2: FRAGE STELLEN
    # -----------------------------------------------------------------------
    elif st.session_state.quiz_phase == 'frage':
        fragen  = st.session_state.quiz_fragen
        idx     = st.session_state.quiz_idx
        name    = st.session_state.quiz_name
        farbe_n = PINNWAND_FARBEN.get(name, "#FF4B4B")

        if idx >= len(fragen):
            st.session_state.quiz_phase = 'ergebnis'
            st.rerun()

        frage = fragen[idx]
        spr   = frage["sprache"]
        total = len(fragen)

        # Fortschrittsbalken
        fortschritt = idx / total
        st.markdown(
            f'<div style="background:#e0e0e0;border-radius:10px;height:10px;margin-bottom:12px;">'
            f'<div style="background:{farbe_n};width:{max(fortschritt*100,3):.0f}%;'
            f'height:10px;border-radius:10px;min-width:8px;"></div>'
            f'<div style="font-size:0.72rem;color:#666;text-align:right;margin-top:2px;">'
            f'Frage {idx+1} / {total}</div></div>',
            unsafe_allow_html=True
        )

        # Sprachen-Abschnitt Header
        if idx % FRAGEN_PRO_SPRACHE == 0:
            st.markdown(
                f'<div style="background:{farbe_n};color:white;border-radius:10px;'
                f'padding:8px 14px;margin-bottom:12px;font-weight:700;font-size:1rem;">'
                f'{SPRACHE_NAMEN[spr]}</div>',
                unsafe_allow_html=True
            )

        # Frage
        st.markdown(
            f'<div style="background:#f8f8f8;border-radius:12px;padding:16px;'
            f'text-align:center;margin-bottom:16px;border:1px solid #e8e8e8;">'
            f'<div style="font-size:0.78rem;color:#666 !important;margin-bottom:6px;">'
            f'Frage {idx+1} von {total} · {SPRACHE_NAMEN[spr]}</div>'
            f'<div style="font-size:1.4rem;font-weight:900;color:#111 !important;">{frage["frage_de"]}</div>'
            f'<div style="font-size:0.85rem;color:#555 !important;margin-top:4px;">Wie heißt das auf {SPRACHE_NAMEN[spr].split()[-1]}?</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Antwort-Buttons
        if st.session_state.quiz_antwort is None:
            for opt in frage["optionen"]:
                if st.button(opt, key=f"opt_{idx}_{opt}", use_container_width=True):
                    st.session_state.quiz_antwort = opt
                    if opt == frage["richtig"]:
                        spr_key = frage["sprache"]
                        st.session_state.quiz_punkte[spr_key] =                             st.session_state.quiz_punkte.get(spr_key, 0) + 1
                    st.rerun()
        else:
            # Auflösung
            gew = st.session_state.quiz_antwort == frage["richtig"]
            for opt in frage["optionen"]:
                if opt == frage["richtig"]:
                    bg = "#2E7D32"; txt = "white"; prefix = "✅ "
                elif opt == st.session_state.quiz_antwort and not gew:
                    bg = "#C62828"; txt = "white"; prefix = "❌ "
                else:
                    bg = "#f0f0f0"; txt = "#444"; prefix = ""
                st.markdown(
                    f'<div style="background:{bg};color:{txt} !important;border-radius:8px;'
                    f'padding:10px 16px;margin-bottom:6px;font-weight:600;">'
                    f'{prefix}{opt}</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if gew:
                st.success("🎉 Richtig!")
            else:
                st.error(f"Die richtige Antwort war: **{frage['richtig']}**")

            if st.button("Weiter →", use_container_width=True, type="primary",
                         key=f"weiter_{idx}"):
                st.session_state.quiz_idx    += 1
                st.session_state.quiz_antwort = None
                st.rerun()

    # -----------------------------------------------------------------------
    # PHASE 3: ERGEBNIS
    # -----------------------------------------------------------------------
    elif st.session_state.quiz_phase == 'ergebnis':
        name    = st.session_state.quiz_name
        punkte  = st.session_state.quiz_punkte
        gesamt  = sum(punkte.values())
        farbe_n = PINNWAND_FARBEN.get(name, "#FF4B4B")
        total   = FRAGEN_PRO_SPRACHE * 3

        # Ergebnis speichern (nur wenn tatsächlich gespielt wurde)
        if gesamt > 0 or idx >= total:
            try:
                # Erst prüfen ob bereits ein besseres Ergebnis existiert
                existing = supabase.table("quiz_ergebnisse").select("punkte").eq(
                    "datum", str(date.today())).eq("name", name).execute()
                best = existing.data[0]["punkte"] if existing.data else 0
                if gesamt >= best:
                    supabase.table("quiz_ergebnisse").upsert({
                        "datum":           str(date.today()),
                        "name":            name,
                        "punkte":          gesamt,
                        "sprachen_detail": punkte,
                    }, on_conflict="datum,name").execute()
            except Exception:
                pass

        # Ergebnis-Card
        prozent = gesamt / total * 100
        emoji   = "🏆" if prozent == 100 else "🎉" if prozent >= 70 else "💪" if prozent >= 40 else "📚"
        st.markdown(
            f'<div style="background:linear-gradient(135deg,{farbe_n},{farbe_n}cc);'
            f'color:white;border-radius:16px;padding:24px;text-align:center;'
            f'box-shadow:0 4px 14px rgba(0,0,0,0.15);margin-bottom:16px;">'
            f'<div style="font-size:3rem;">{emoji}</div>'
            f'<div style="font-weight:900;font-size:1.3rem;margin-top:8px;">{name}</div>'
            f'<div style="font-size:2.5rem;font-weight:900;margin:8px 0;">{gesamt}/{total}</div>'
            f'<div style="opacity:0.85;font-size:0.9rem;">Punkte heute</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Detailauswertung pro Sprache
        for spr, spr_name in SPRACHE_NAMEN.items():
            p = punkte.get(spr, 0)
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:8px 12px;background:#f8f8f8;border-radius:8px;margin-bottom:6px;">'
                f'<span style="font-size:0.95rem;color:#222 !important;">{spr_name}</span>'
                f'<span style="font-weight:700;color:{farbe_n} !important;">{p}/{FRAGEN_PRO_SPRACHE} Pkt.</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Tagesrangliste
        try:
            heute_res = supabase.table("quiz_ergebnisse").select("*").eq(
                "datum", str(date.today())).order("punkte", desc=True).execute()
            if heute_res.data:
                st.divider()
                st.markdown("#### 📊 Heute")
                medals = ["🥇","🥈","🥉","4.","5."]
                for idx2, r in enumerate(heute_res.data):
                    fn     = r["name"]
                    fp     = r["punkte"]
                    fb     = PINNWAND_FARBEN.get(fn, "#888")
                    is_me  = fn == name
                    bg2     = "#fff" if is_me else "#f8f8f8"
                    border2 = f"2px solid {fb}" if is_me else "1px solid #eee"
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:7px 12px;border-radius:8px;margin-bottom:4px;'
                        f'background:{bg2};border:{border2};">'
                        f'<span style="color:#222 !important;">{medals[idx2] if idx2 < 5 else str(idx2+1)+"."} '
                        f'<b style="color:{fb} !important;">{fn}</b>'
                        f'{"  ← du" if is_me else ""}</span>'
                        f'<span style="font-weight:700;color:{fb} !important;">{fp}/{total}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        except Exception:
            pass

        if st.button("← Hauptmenü", use_container_width=True, key="quiz_home", type="primary"):
            st.session_state.view       = 'start'
            st.session_state.quiz_phase = 'name'
            st.rerun()

    if st.session_state.quiz_phase == 'name':
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