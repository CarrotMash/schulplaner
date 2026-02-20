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
CHILDREN = ["Mila", "Jojo", "Toto"]
SUBJECTS = {
    "Englisch": "#3399FF", "Französisch": "#FF66B2", "Mathematik": "#00CC66",
    "Deutsch": "#FFD700", "Musik": "#FF9900", "Biologie": "#228B22",
    "Chemie": "#00CCCC", "Kunst": "#9966FF", "Philosophie": "#A0A0A0",
    "Geschichte": "#CC6600", "Physik": "#33CCFF", "Spanisch": "#FF3333",
    "WiPo": "#008080"
}

# Dynamisches Icon mit Datum für den Browsertab
heute_tag = datetime.now().day
st.set_page_config(
    page_title=f"Schul-Planer {datetime.now().strftime('%d.%m.')}", 
    page_icon="📅", 
    layout="centered"
)

# --- CUSTOM CSS FÜR OPTIMIERUNGEN ---
st.markdown(f"""
    <style>
    /* Überschrift verkleinern, damit kein Umbruch entsteht */
    .small-title {{
        font-size: 1.6rem !important;
        font-weight: bold;
        color: #31333F;
        margin-bottom: 10px;
        white-space: nowrap;
    }}
    /* Kalender-Einträge: Textumbruch erlauben und Schriftgröße anpassen */
    .fc-event-title {{
        font-size: 0.85rem !important;
        white-space: normal !important;
        font-weight: 500 !important;
        padding: 1px !important;
    }}
    /* Wochenenden farblich absetzen (leichtes Grau) */
    .fc-day-sat, .fc-day-sun {{
        background-color: #f9f9f9 !important;
    }}
    /* Buttons im Kalender auf Deutsch (falls CSS nötig) */
    .fc-today-button {{ text-transform: capitalize; }}
    </style>
    """, unsafe_allow_html=True)

if 'started' not in st.session_state:
    st.session_state.started = False

# --- STARTBILDSCHIRM ---
if not st.session_state.started:
    st.markdown("<h2 style='text-align: center;'>Willkommen beim Klausuren-Planer!</h2>", unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"):
        st.image("startbild.jpg", use_container_width=True)
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- HAUPT-APP ---
else:
    st.markdown('<p class="small-title">📅 Tests & Klausuren</p>', unsafe_allow_html=True)

    # Daten laden
    response = supabase.table("klausuren").select("*").execute()
    data = response.data
    df = pd.DataFrame(data)

    # --- SIDEBAR: NEUE EINTRÄGE ---
    with st.sidebar:
        st.header("Neue Klausur")
        with st.form("input_form", clear_on_submit=True):
            child = st.selectbox("Kind", CHILDREN)
            subject = st.selectbox("Fach", list(SUBJECTS.keys()))
            exam_date = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            note = st.text_input("Notiz")
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
                st.success("Gespeichert!")
                st.rerun()
        
        st.divider()
        if st.button("Zurück zum Startbild"):
            st.session_state.started = False
            st.rerun()

    # --- FERIEN (Zartes Grün) ---
    zart_gruen = "#E8F5E9"
    holidays = [
        {"title": "Osterferien", "start": "2025-04-11", "end": "2025-04-27", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien", "start": "2025-07-28", "end": "2025-09-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbstferien", "start": "2025-10-20", "end": "2025-11-01", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnachtsferien", "start": "2025-12-19", "end": "2026-01-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Osterferien '26", "start": "2026-03-26", "end": "2026-04-12", "backgroundColor": zart_gruen, "display": "background"},
    ]

    # Events für Kalender vorbereiten
    calendar_events = []
    for d in data:
        calendar_events.append({
            "id": d["id"],
            "title": d["titel"],
            "start": d["start_date"],
            "end": d["start_date"],
            "backgroundColor": d["color"],
            "allDay": True,
            "textColor": "black" if d["color"] == "#FFD700" else "white",
            "extendedProps": {"note": d["note"], "id": d["id"]}
        })

    # --- KALENDER OPTIONEN (DEUTSCH) ---
    calendar_options = {
        "headerToolbar": {
            "left": "prev,today,next",
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
        "firstDay": 1,
        "height": "auto",
        "navLinks": True
    }

    # Kalender anzeigen und Klick-Events abfangen
    state = calendar(events=calendar_events + holidays, options=calendar_options, key="main_calendar")

    # --- BEARBEITEN / LÖSCHEN LOGIK ---
    if state.get("eventClick"):
        clicked_event = state["eventClick"]["event"]
        event_id = clicked_event["id"]
        event_title = clicked_event["title"]
        
        # Nur bearbeitbar, wenn es keine Ferien sind (Ferien haben keine ID aus der DB)
        if event_id:
            st.divider()
            st.subheader(f"Eintrag bearbeiten: {event_title}")
            
            with st.expander("Details ansehen / Ändern", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Eintrag löschen", use_container_width=True):
                        supabase.table("klausuren").delete().eq("id", event_id).execute()
                        st.warning("Eintrag gelöscht!")
                        st.rerun()
                with col2:
                    st.info("Zum Ändern: Löschen und neu anlegen (einfachste Methode).")

    # Tabelle anzeigen
    st.divider()
    st.subheader("Übersicht aller Termine")
    if not df.empty:
        df_sorted = df.sort_values(by='start_date')

        st.table(df_sorted[['datum', 'titel']])
