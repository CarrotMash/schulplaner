import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
from supabase import create_client
import os

# --- DATENBANK VERBINDUNG ---
# Diese Daten zieht sich die App aus den Streamlit Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- KONFIGURATION: Fächer & Farben ---
CHILDREN = ["Mila", "Jojo", "Mikko"]
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
    page_title=f"Klausuren-Planer {heute_obj.strftime('%d.%m.')}", 
    page_icon="📅", 
    layout="centered"
)

# --- CUSTOM CSS FÜR SMARTPHONE-OPTIMIERUNG ---
st.markdown(f"""
    <style>
    /* Titel verkleinern, um Umbruch zu vermeiden */
    .app-title {{
        font-size: 1.5rem !important;
        font-weight: bold;
        color: #31333F;
        margin-bottom: 5px;
        white-space: nowrap;
    }}
    /* Kalender-Einträge: Textumbruch erlauben & Schriftgröße */
    .fc-event-title {{
        font-size: 0.8rem !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        font-weight: 500 !important;
        padding: 1px !important;
    }}
    /* Wochenenden dezent grau hinterlegen */
    .fc-day-sat, .fc-day-sun {{
        background-color: #F0F2F6 !important;
    }}
    /* Toolbar-Buttons Styling */
    .fc-button {{
        text-transform: capitalize !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# Session State für den Start-Button
if 'started' not in st.session_state:
    st.session_state.started = False

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    st.markdown("<h2 style='text-align: center;'>Willkommen beim Klausuren-Planer!</h2>", unsafe_allow_html=True)
    
    if os.path.exists("startbild.jpg"):
        st.image("startbild.jpg", use_container_width=True)
    else:
        st.info("Bitte 'startbild.jpg' auf GitHub hochladen.")
    
    st.write("---")
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP ---
else:
    st.markdown('<p class="app-title">📅 Tests & Klausuren</p>', unsafe_allow_html=True)

    # Daten aus Supabase laden
    try:
        response = supabase.table("klausuren").select("*").execute()
        data = response.data
        df = pd.DataFrame(data)
    except Exception as e:
        st.error("Verbindung zur Datenbank fehlgeschlagen.")
        data = []
        df = pd.DataFrame()

    # --- SIDEBAR: NEUE EINTRÄGE ---
    with st.sidebar:
        st.header("Eintrag hinzufügen")
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
        if st.button("Zurück zum Startbild"):
            st.session_state.started = False
            st.rerun()

    # --- FERIEN & FREIE TAGE (Zartes Grün) ---
    zart_gruen = "#E8F5E9"
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
            "extendedProps": {"note": d.get("note", ""), "id": d["id"]}
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
        "firstDay": 1, # Montag als Wochenstart
        "height": "auto",
        "navLinks": True
    }

    # Kalender anzeigen
    state = calendar(events=calendar_events + holidays, options=calendar_options, key="main_calendar")

    # --- INTERAKTION: KLICK AUF EVENT ---
    if state.get("eventClick"):
        clicked_event = state["eventClick"]["event"]
        e_id = clicked_event.get("id")
        
        # Nur bearbeitbar, wenn es kein Ferien-Hintergrund ist
        if e_id and e_id != "undefined":
            st.divider()
            st.subheader("Eintrag verwalten")
            st.write(f"**Gewählt:** {clicked_event['title']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Löschen", use_container_width=True):
                    supabase.table("klausuren").delete().eq("id", e_id).execute()
                    st.toast("Eintrag wurde gelöscht!")
                    st.rerun()
            with col2:
                st.info("Zum Ändern bitte löschen und neu anlegen.")

    # --- TABELLEN-ÜBERSICHT ---
    st.divider()
    st.subheader("Kommende Termine")
    if not df.empty:
        # Sortieren nach echtem Datum
        df_display = df.sort_values(by='start_date')
        # Nur Datum und Titel für die Tabelle
        st.table(df_display[['datum', 'titel']].rename(columns={'datum': 'Wann', 'titel': 'Wer & Was'}))
    else:
        st.write("Keine anstehenden Termine gefunden.")