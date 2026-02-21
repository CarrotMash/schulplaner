import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
from supabase import create_client
import os
import uuid

# --- DATENBANK VERBINDUNG ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- KONFIGURATION ---
CHILD_COLORS = {"Mila": "#FF85A1", "Jojo": "#8B0000", "Mikko": "#2E7D32"}
SUBJECTS = ["Englisch", "Französisch", "Mathematik", "Deutsch", "Musik", "Biologie", "Chemie", "Kunst", "Philosophie", "Geschichte", "Physik", "Spanisch", "WiPo", "Sport", "Religion", "Freistunde"]
DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
TIMES = {
    1: "07:50-08:35", 2: "08:40-09:25", 3: "09:40-10:25", 4: "10:30-11:15",
    5: "11:30-12:15", 6: "12:20-13:05", 7: "13:35-14:20", 8: "14:25-15:10"
}

st.set_page_config(page_title="Klausuren-Planer", page_icon="📅", layout="centered")

# --- CUSTOM DESIGN (CSS) ---
st.markdown("""
    <style>
    .block-container { padding-top: 2.7rem !important; padding-bottom: 0rem !important; }
    .main-header { font-size: 2.2rem !important; font-weight: 900 !important; text-align: center; margin-top: -10px; margin-bottom: 20px; background-color: #000000; color: #FFFFFF !important; padding: 12px; border-radius: 10px; line-height: 1.1; white-space: nowrap; }
    [data-testid="stImage"] > img { width: 64% !important; margin-left: auto; margin-right: auto; display: block; border-radius: 10px; }
    .fc-header-toolbar { margin-top: 10px !important; margin-bottom: 1.5rem !important; display: flex !important; align-items: center; justify-content: space-between !important; }
    .fc-toolbar-chunk:nth-child(1) { display: flex !important; flex-direction: column !important; align-items: center !important; gap: 6px !important; }
    .fc-button-primary { background-color: #FF4B4B !important; border-color: #FF4B4B !important; color: #FFFFFF !important; font-weight: bold !important; font-size: 0.85rem !important; }
    .fc-list-event-time { display: none !important; }
    .fc-event-title { font-size: 0.8rem !important; white-space: pre-wrap !important; font-weight: bold !important; }
    
    /* Stundenplan Mobile Optimierung */
    .std-card { background: #f8f9fa; border-left: 5px solid #FF4B4B; padding: 5px; margin-bottom: 5px; border-radius: 4px; }
    .std-num { font-size: 0.7rem; color: #888; font-weight: bold; }
    .std-fach { font-size: 1rem; font-weight: bold; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialisierung
if 'view' not in st.session_state: st.session_state.view = 'start'
if 'cal_key' not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = "Mila"
if 'day_offset' not in st.session_state: st.session_state.day_offset = 0

# Hilfsfunktion für den aktuellen Wochentag (0=Mo, 4=Fr)
def get_today_index():
    idx = datetime.now().weekday()
    return idx if idx < 5 else 0 # Sa/So springt auf Montag

# --- 1. STARTSEITE ---
if st.session_state.view == 'start':
    st.markdown('<p class="main-header">Klausuren-Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): st.image("startbild.jpg")
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("📅 KLAUSUREN", use_container_width=True, type="primary"):
        st.session_state.view = 'klausuren'; st.rerun()
    if c2.button("🏫 STUNDENPLÄNE", use_container_width=True, type="primary"):
        st.session_state.view = 'stundenplan'; st.rerun()

# --- 2. KLAUSUREN-BEREICH (ALTBEWÄHRT) ---
elif st.session_state.view == 'klausuren':
    res = supabase.table("klausuren").select("*").execute()
    k_data = res.data
    
    with st.sidebar:
        st.header("Klausuren")
        if st.button("← Hauptmenü"): st.session_state.view = 'start'; st.rerun()
        with st.form("sb_form", clear_on_submit=True):
            sc = st.selectbox("Kind", list(CHILD_COLORS.keys())); ss = st.selectbox("Fach", SUBJECTS)
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY"); sn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}", "start_date": str(sd), "color": CHILD_COLORS[sc], "child": sc, "note": sn}).execute()
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()

    zart_gruen = "#C8E6C9"
    holidays = [{"title": "Oster", "start": "2025-04-11", "end": "2025-04-26", "backgroundColor": zart_gruen, "display": "background"}]
    
    cal_events = []
    for d in k_data:
        cal_events.append({"id": str(d["id"]), "title": d["titel"], "start": d["start_date"], "backgroundColor": d["color"], "allDay": True, "textColor": "white"})

    state = calendar(events=cal_events + holidays, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}, "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", "selectable": True, "timeZone": "UTC", "displayEventTime": False}, key=st.session_state.cal_key)

    # Einfaches Löschen-Formular unter Kalender falls Event geklickt
    if state.get("eventClick"):
        eid = state["eventClick"]["event"].get("id")
        if eid:
            if st.button(f"🗑️ Eintrag löschen", use_container_width=True):
                supabase.table("klausuren").delete().eq("id", eid).execute()
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()

# --- 3. NEUER STUNDENPLAN-ANSATZ (OHNE PANDAS FILTER) ---
elif st.session_state.view == 'stundenplan':
    st.markdown(f'<div style="background-color:black; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold; font-size:1.5rem; margin-bottom:15px;">🏫 Stundenpläne</div>', unsafe_allow_html=True)
    
    # Kind-Auswahl
    c_cols = st.columns(3)
    for i, name in enumerate(CHILD_COLORS.keys()):
        if c_cols[i].button(name, use_container_width=True, type="secondary" if st.session_state.stundenplan_child != name else "primary"):
            st.session_state.stundenplan_child = name; st.rerun()

    current_child = st.session_state.stundenplan_child
    
    # Daten laden und in ein einfaches Dictionary umwandeln: (Tag, Stunde) -> Fach
    res = supabase.table("stundenplaene").select("*").eq("child", current_child).execute()
    plan_dict = {}
    id_dict = {}
    for item in res.data:
        key = (item['tag'], int(item['stunde']))
        plan_dict[key] = item['fach']
        id_dict[key] = item['id']

    # Navigation durch die Tage
    t_col1, t_col2, t_col3 = st.columns([1, 2, 1])
    if t_col1.button("◀", use_container_width=True): st.session_state.day_offset -= 1; st.rerun()
    t_col2.markdown(f"<center><b>Fokus-Tag verschieben</b></center>", unsafe_allow_html=True)
    if t_col3.button("▶", use_container_width=True): st.session_state.day_offset += 1; st.rerun()

    # Berechne die 3 anzuzeigenden Tage
    start_idx = (get_today_index() + st.session_state.day_offset) % 5
    display_days = [DAYS[(start_idx + i) % 5] for i in range(3)]

    # Anzeige der 3 Tage nebeneinander (oder untereinander auf sehr kleinen Handys)
    cols = st.columns(3)
    for i, day in enumerate(display_days):
        with cols[i]:
            st.markdown(f"<div style='text-align:center; background:#eee; border-radius:5px; padding:5px; margin-bottom:10px;'><b>{day}</b></div>", unsafe_allow_html=True)
            for std in range(1, 9):
                fach = plan_dict.get((day, std), "---")
                if st.button(f"{fach}", key=f"btn_{day}_{std}_{i}", help=TIMES[std], use_container_width=True):
                    st.session_state.edit_cell = {"day": day, "std": std, "fach": fach, "id": id_dict.get((day, std))}

    # Bearbeitungs-Bereich
    if 'edit_cell' in st.session_state:
        ec = st.session_state.edit_cell
        st.divider()
        with st.form("edit_stundenplan"):
            st.write(f"📌 **{ec['day']}, {ec['std']}. Stunde** ({TIMES[ec['std']]})")
            new_f = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(ec['fach']) if ec['fach'] in SUBJECTS else 0)
            if st.form_submit_button("Speichern"):
                if ec['id']:
                    supabase.table("stundenplaene").update({"fach": new_f}).eq("id", ec['id']).execute()
                else:
                    supabase.table("stundenplaene").insert({"child": current_child, "tag": ec['day'], "stunde": ec['std'], "fach": new_f}).execute()
                del st.session_state.edit_cell; st.rerun()
            if st.form_submit_button("Abbrechen"):
                del st.session_state.edit_cell; st.rerun()

    st.write("")
    if st.button("← Hauptmenü", use_container_width=True):
        st.session_state.view = 'start'; st.session_state.day_offset = 0; st.rerun()