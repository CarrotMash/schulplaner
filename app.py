import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
from supabase import create_client
import os

# --- DATENBANK VERBINDUNG ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- KONFIGURATION ---
CHILDREN = ["Milschi", "Jojo", "Toto"]
SUBJECTS = {
    "Englisch": "#3399FF", "Französisch": "#FF66B2", "Mathematik": "#00CC66",
    "Deutsch": "#FFD700", "Musik": "#FF9900", "Biologie": "#228B22",
    "Chemie": "#00CCCC", "Kunst": "#9966FF", "Philosophie": "#A0A0A0",
    "Geschichte": "#CC6600", "Physik": "#33CCFF", "Spanisch": "#FF3333",
    "WiPo": "#008080"
}

# --- BROWSER-KONFIGURATION ---
heute_obj = datetime.now()
st.set_page_config(
    page_title=f"Schul-Planer {heute_obj.strftime('%d.%m.')}", 
    page_icon="📅", 
    layout="centered"
)

# --- SMARTPHONE OPTIMIERUNG (CSS) ---
st.markdown("""
    <style>
    /* 1. Gesamten Inhalt weiter nach oben rücken */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    [data-testid="stAppViewContainer"] {
        padding-top: -50px !important;
    }
    
    /* 2. Startbild verkleinern (Maximalhöhe) */
    .stImage img {
        max-height: 250px;
        width: auto !important;
        margin-left: auto;
        margin-right: auto;
        display: block;
        border-radius: 10px;
    }

    /* 3. Kalender-Texte optimieren */
    .fc-event-title {
        font-size: 0.75rem !important;
        white-space: normal !important;
        line-height: 1 !important;
    }
    
    /* 4. Abstände im Kalender reduzieren */
    .fc-toolbar {
        margin-bottom: 0.5rem !important;
        font-size: 0.9rem !important;
    }

    /* 5. Wochenenden */
    .fc-day-sat, .fc-day-sun {
        background-color: #F0F2F6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'started' not in st.session_state:
    st.session_state.started = False

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    # Text höher ansetzen durch negatives Margin
    st.markdown("<h3 style='text-align: center; margin-top: -40px; margin-bottom: 10px;'>Willkommen beim Schul-Planer!</h3>", unsafe_allow_html=True)
    
    if os.path.exists("startbild.jpg"):
        st.image("startbild.jpg")
    
    st.write("") # Kleiner Platzhalter
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP (Kalenderansicht) ---
else:
    # Überschrift wurde entfernt, um Platz zu sparen
    
    # Daten laden
    try:
        response = supabase.table("klausuren").select("*").execute()
        data = response.data
        df = pd.DataFrame(data)
    except:
        data = []
        df = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Eintrag hinzufügen")
        with st.form("input_form", clear_on_submit=True):
            child = st.selectbox("Kind", CHILDREN)
            subject = st.selectbox("Fach", list(SUBJECTS.keys()))
            exam_date = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            note = st.text_input("Notiz (optional)")
            if st.form_submit_button("Speichern"):
                new_entry = {
                    "datum": exam_date.strftime('%d.%m.%Y'),
                    "titel": f"{child}: {subject}",
                    "start_date": str(exam_date),
                    "color": SUBJECTS[subject],
                    "child": child,
                    "note": note
                }
                supabase.table("klausuren").insert(new_entry).execute()
                st.rerun()
        
        if st.button("Abmelden / Startseite"):
            st.session_state.started = False
            st.rerun()

    # --- FERIEN ---
    zart_gruen = "#E8F5E9"
    holidays = [
        {"title": "Osterferien", "start": "2025-04-11", "end": "2025-04-27", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien", "start": "2025-07-28", "end": "2025-09-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbstferien", "start": "2025-10-20", "end": "2025-11-01", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnachtsferien", "start": "2025-12-19", "end": "2026-01-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Osterferien '26", "start": "2026-03-26", "end": "2026-04-12", "backgroundColor": zart_gruen, "display": "background"},
    ]

    # Events aufbereiten
    calendar_events = []
    for d in data:
        calendar_events.append({
            "id": str(d["id"]),
            "title": d["titel"],
            "start": d["start_date"],
            "end": d["start_date"],
            "backgroundColor": d["color"],
            "allDay": True,
            "textColor": "black" if d["color"] == "#FFD700" else "white"
        })

    calendar_options = {
        "headerToolbar": {"left": "prev,today,next", "center": "title", "right": "dayGridMonth,listWeek"},
        "buttonText": {"today": "Heute", "month": "Monat", "list": "Liste"},
        "initialView": "dayGridMonth",
        "locale": "de", "firstDay": 1, "height": "auto"
    }

    state = calendar(events=calendar_events + holidays, options=calendar_options, key="main_calendar")

    # Lösch-Logik bei Klick
    if state.get("eventClick"):
        e_id = state["eventClick"]["event"].get("id")
        if e_id and e_id != "undefined":
            st.divider()
            if st.button(f"🗑️ '{state['eventClick']['event']['title']}' löschen"):
                supabase.table("klausuren").delete().eq("id", e_id).execute()
                st.rerun()

    # Übersichtstabelle
    if not df.empty:
        st.divider()
        st.table(df.sort_values(by='start_date')[['datum', 'titel']].rename(columns={'datum': 'Wann', 'titel': 'Wer & Was'}))