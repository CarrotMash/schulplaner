import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
import json
import os

# --- KONFIGURATION: Fröhliche Farben mit gutem Kontrast ---
CHILDREN = ["Milschi", "Jojo", "Toto"]
SUBJECTS = {
    "Englisch": "#3399FF",    # Kräftiges Blau
    "Französisch": "#FF66B2", # Rosa
    "Mathematik": "#00CC66",  # Saftiges Grün
    "Deutsch": "#FFD700",     # Gold/Gelb
    "Musik": "#FF9900",       # Orange
    "Biologie": "#228B22",    # Waldgrün
    "Chemie": "#00CCCC",      # Türkis
    "Kunst": "#9966FF",       # Lila
    "Philosophie": "#A0A0A0", # Grau
    "Geschichte": "#CC6600",  # Braun
    "Physik": "#33CCFF",      # Hellblau
    "Spanisch": "#FF3333",    # Rot
    "WiPo": "#008080"         # Petrol
}

DB_FILE = "exams_data.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- UI SETUP ---
st.set_page_config(page_title="Schul-Planer", layout="centered")

# Session State für den Start-Button
if 'started' not in st.session_state:
    st.session_state.started = False

import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
import json
import os

# --- KONFIGURATION: Farben & Kinder ---
CHILDREN = ["Milschi", "Jojo", "Toto"]
SUBJECTS = {
    "Englisch": "#3399FF",    # Kräftiges Blau
    "Französisch": "#FF66B2", # Rosa
    "Mathematik": "#00CC66",  # Saftiges Grün
    "Deutsch": "#FFD700",     # Gold/Gelb (Schwarze Schrift)
    "Musik": "#FF9900",       # Orange
    "Biologie": "#228B22",    # Waldgrün
    "Chemie": "#00CCCC",      # Türkis
    "Kunst": "#9966FF",       # Lila
    "Philosophie": "#A0A0A0", # Grau
    "Geschichte": "#CC6600",  # Braun
    "Physik": "#33CCFF",      # Hellblau
    "Spanisch": "#FF3333",    # Rot
    "WiPo": "#008080"         # Petrol
}

DB_FILE = "exams_data.json"

# --- HELFER-FUNKTIONEN ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- UI SETUP ---
st.set_page_config(page_title="Schul-Planer", layout="centered")

# Session State für den Start-Bildschirm
if 'started' not in st.session_state:
    st.session_state.started = False

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    st.title("Willkommen beim Schul-Planer!")
    
    # Startbild anzeigen
    if os.path.exists("startbild.jpg"):
        st.image("startbild.jpg", use_container_width=True)
    else:
        st.info("Hier erscheint das Startbild (startbild.jpg)")

    st.write("### Alles im Griff bei Milschi, Jojo und Toto?")
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP ---
else:
    st.title("📅 Termine & Klausuren")

    # --- SIDEBAR: EINGABE ---
    with st.sidebar:
        st.header("Neue Klausur")
        child = st.selectbox("Kind", CHILDREN)
        subject = st.selectbox("Fach", list(SUBJECTS.keys()))
        
        # Datums-Eingabe im Format DD.MM.YYYY
        exam_date = st.date_input("Datum wählen", date.today(), format="DD.MM.YYYY")
        
        note = st.text_input("Notiz (optional)")
        
        if st.button("Speichern"):
            current_data = load_data()
            new_exam = {
                "title": f"{child}: {subject}",
                "start": str(exam_date),
                "end": str(exam_date),
                "backgroundColor": SUBJECTS[subject],
                "borderColor": "#333333",
                "textColor": "black" if SUBJECTS[subject] == "#FFD700" else "white",
                "allDay": True,
                "extendedProps": {"child": child, "note": note}
            }
            current_data.append(new_exam)
            save_data(current_data)
            st.success(f"Eingetragen für {exam_date.strftime('%d.%m.%Y')}!")
            st.rerun()

        st.divider()
        if st.button("Zurück zum Startbild"):
            st.session_state.started = False
            st.rerun()
        
        if st.button("Alle Daten löschen"):
            if st.checkbox("Ja, wirklich alles löschen"):
                save_data([])
                st.rerun()

    # --- FERIEN & FEIERTAGS-LOGIK (Schleswig-Holstein) ---
    # Hinweis: 'end' ist exklusiv, daher +1 Tag zum offiziellen Ferienende
    holidays = [
        # 2025
        {"title": "Osterferien", "start": "2025-04-11", "end": "2025-04-27", "backgroundColor": "#FFDEAD", "display": "background"},
        {"title": "Sommerferien", "start": "2025-07-28", "end": "2025-09-08", "backgroundColor": "#FFDEAD", "display": "background"},
        {"title": "Herbstferien", "start": "2025-10-20", "end": "2025-11-01", "backgroundColor": "#FFDEAD", "display": "background"},
        {"title": "Weihnachtsferien", "start": "2025-12-19", "end": "2026-01-08", "backgroundColor": "#FFDEAD", "display": "background"},
        # 2026
        {"title": "Osterferien '26", "start": "2026-03-26", "end": "2026-04-12", "backgroundColor": "#FFDEAD", "display": "background"},
        {"title": "Sommerferien '26", "start": "2026-07-13", "end": "2026-08-24", "backgroundColor": "#FFDEAD", "display": "background"},
        {"title": "Herbstferien '26", "start": "2026-10-12", "end": "2026-10-26", "backgroundColor": "#FFDEAD", "display": "background"},
        {"title": "Weihnachtsferien '26", "start": "2026-12-21", "end": "2027-01-08", "backgroundColor": "#FFDEAD", "display": "background"},
        # Feiertage
        {"title": "Tag d. Dt. Einheit", "start": "2025-10-03", "end": "2025-10-04", "backgroundColor": "#E0E0E0", "display": "background"},
        {"title": "Reformationstag", "start": "2025-10-31", "end": "2025-11-01", "backgroundColor": "#E0E0E0", "display": "background"},
    ]

    # --- KALENDER ANZEIGE ---
    all_events = load_data() + holidays
    
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next",
            "center": "title",
            "right": "dayGridMonth,listWeek"
        },
        "initialView": "dayGridMonth",
        "locale": "de",
        "firstDay": 1,
    }

    calendar(events=all_events, options=calendar_options)

    # --- TABELLE DER KLAUSUREN (DD.MM.YYYY) ---
    st.divider()
    st.subheader("Anstehende Klausuren (Übersicht)")
    
    raw_data = load_data()
    if raw_data:
        df = pd.DataFrame(raw_data)
        # Datum formatieren
        df['Datum'] = pd.to_datetime(df['start']).dt.strftime('%d.%m.%Y')
        # Tabelle sortieren und verschönern
        df_display = df[['Datum', 'title']].sort_values(by='Datum')
        df_display.columns = ['Datum', 'Was & Wer']
        
        # Anzeige als Tabelle ohne Index
        st.table(df_display)
    else:
        st.info("Noch keine Klausuren eingetragen. Nutze die linke Seitenleiste!")