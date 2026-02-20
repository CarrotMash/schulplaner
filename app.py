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

# --- KONFIGURATION: Namen & Fächer ---
CHILDREN = ["Mila", "Jojo", "Mikko"]
SUBJECTS = {
    "Englisch": "#3399FF", "Französisch": "#FF66B2", "Mathematik": "#00CC66",
    "Deutsch": "#FFD700", "Musik": "#FF9900", "Biologie": "#228B22",
    "Chemie": "#00CCCC", "Kunst": "#9966FF", "Philosophie": "#A0A0A0",
    "Geschichte": "#CC6600", "Physik": "#33CCFF", "Spanisch": "#FF3333",
    "WiPo": "#008080"
}

# --- BROWSER-EINSTELLUNGEN ---
heute_obj = datetime.now()
st.set_page_config(
    page_title=f"Klausuren-Planer {heute_obj.strftime('%d.%m.')}", 
    page_icon="📅", 
    layout="centered"
)

# --- CUSTOM DESIGN (CSS) ---
st.markdown("""
    <style>
    /* Hintergrund für Wochenenden im Kalender (Grau) */
    .fc-day-sat, .fc-day-sun {
        background-color: #F0F0F0 !important;
    }
    /* Event-Titel: Textumbruch erlauben & Fettschrift */
    .fc-event-title {
        font-size: 0.85rem !important;
        white-space: normal !important;
        font-weight: bold !important;
        padding: 1px !important;
    }
    /* Startseite Titel-Styling */
    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
        margin-top: -20px;
        color: #31333F;
    }
    /* Toolbar-Buttons Styling */
    .fc-button {
        text-transform: capitalize !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State für den Start-Bildschirm
if 'started' not in st.session_state:
    st.session_state.started = False

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    st.markdown('<p class="main-header">Willkommen beim Klausuren-Planer</p>', unsafe_allow_html=True)
    
    if os.path.exists("startbild.jpg"):
        st.image("startbild.jpg", use_container_width=True)
    else:
        st.info("Bitte 'startbild.jpg' auf GitHub hochladen.")
    
    st.write("---")
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP (Kalenderansicht) ---
else:
    st.markdown('<p class="main-header" style="text-align:left;">📅 Klausuren-Planer</p>', unsafe_allow_html=True)

    # Daten aus Supabase laden
    try:
        response = supabase.table("klausuren").select("*").execute()
        data = response.data
        df = pd.DataFrame(data)
    except Exception:
        data = []
        df = pd.DataFrame()

    # --- SIDEBAR: EINTRAG HINZUFÜGEN ---
    with st.sidebar:
        st.header("Neuer Eintrag")
        with st.form("input_form", clear_on_submit=True):
            child = st.selectbox("Kind", CHILDREN)
            subject = st.selectbox("Fach", list(SUBJECTS.keys()))
            exam_date = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            note = st.text_input("Notiz (optional)")
            submitted = st.form_submit_button("Speichern")
            
            if submitted:
                new_entry = {
                    "datum": exam_date.strftime('%d.%m.%Y'),
                    "titel": f"{child}: {subject}",
                    "start_date": str(exam_date),
                    "color": SUBJECTS[subject],
                    "child": child,
                    "note": note
                }
                supabase.table("klausuren").insert(new_entry).execute()
                st.success("Erfolgreich gespeichert!")
                st.rerun()
        
        st.divider()
        if st.button("Abmelden / Startseite"):
            st.session_state.started = False
            st.rerun()

    # --- FERIEN & FREIE TAGE (Zartes Grün) ---
    # Hintergrundfarbe für Ferien (zartes Frühlingsgrün)
    zart_gruen = "#C8E6C9"
    holidays = [
        # 2025
        {"title": "Osterferien", "start": "2025-04-11", "end": "2025-04-27", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Pfingsten", "start": "2025-05-30", "end": "2025-05-31", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien", "start": "2025-07-28", "end": "2025-09-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbstferien", "start": "2025-10-20", "end": "2025-11-01", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnachtsferien", "start": "2025-12-19", "end": "2026-01-08", "backgroundColor": zart_gruen, "display": "background"},
        # 2026
        {"title": "Osterferien '26", "start": "2026-03-26", "end": "2026-04-12", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien '26", "start": "2026-07-13", "end": "2026-08-24", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbstferien '26", "start": "2026-10-12", "end": "2026-10-26", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnachtsferien '26", "start": "2026-12-21", "end": "2027-01-08", "backgroundColor": zart_gruen, "display": "background"},
    ]

    # Kalender-Events aufbereiten
    calendar_events = []
    for d in data:
        calendar_events.append({
            "id": str(d["id"]),
            "title": d["titel"],
            "start": d["start_date"],
            "end": d["start_date"],
            "backgroundColor": d["color"],
            "allDay": True,
            "textColor": "black" if d["color"] == "#FFD700" else "white",
            "extendedProps": {"id": d["id"]}
        })

    # --- KALENDER OPTIONEN (DEUTSCH & NAVIGATION) ---
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today", # Navigation links
            "center": "title",
            "right": "dayGridMonth,listWeek"
        },
        "buttonText": {
            "today": "Heute",
            "month": "Monat",
            "list": "Liste"
        },
        "initialView": "dayGridMonth",
        "locale": "de",
        "firstDay": 1, # Montag als Wochenstart
        "height": "auto",
        "navLinks": True
    }

    # Kalender anzeigen
    state = calendar(events=calendar_events + holidays, options=calendar_options, key="main_calendar")

    # --- INTERAKTION: KLICK AUF EVENT ZUM LÖSCHEN ---
    if state.get("eventClick"):
        clicked_event = state["eventClick"]["event"]
        e_id = clicked_event.get("id")
        
        # Nur bearbeitbar, wenn es kein Ferien-Hintergrund ist
        if e_id and e_id != "undefined":
            st.divider()
            st.subheader("Eintrag löschen")
            if st.button(f"🗑️ '{clicked_event['title']}' unwiderruflich löschen", use_container_width=True):
                supabase.table("klausuren").delete().eq("id", e_id).execute()
                st.toast("Eintrag gelöscht!")
                st.rerun()

    # --- TABELLEN-ÜBERSICHT ---
    if not df.empty:
        st.divider()
        st.subheader("Übersicht")
        df_sorted = df.sort_values(by='start_date')
        st.table(df_sorted[['datum', 'titel']].rename(columns={'datum': 'Wann', 'titel': 'Wer & Was'}))