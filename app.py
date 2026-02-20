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
CHILDREN = ["Mila", "Jojo", "Mikko"]
SUBJECTS = {
    "Englisch": "#3399FF", "Französisch": "#FF66B2", "Mathematik": "#00CC66",
    "Deutsch": "#FFD700", "Musik": "#FF9900", "Biologie": "#228B22",
    "Chemie": "#00CCCC", "Kunst": "#9966FF", "Philosophie": "#A0A0A0",
    "Geschichte": "#CC6600", "Physik": "#33CCFF", "Spanisch": "#FF3333",
    "WiPo": "#008080"
}

st.set_page_config(page_title="Klausuren-Planer", page_icon="📅", layout="centered")

# --- CUSTOM DESIGN (CSS) ---
st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    
    /* Startseiten-Überschrift */
    .main-header {
        font-size: 3.0rem !important;
        font-weight: 900 !important;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 10px;
        background-color: #000000; 
        color: #FFFFFF !important;
        padding: 15px;
        border-radius: 10px;
        line-height: 1.1;
    }

    /* Startbild-Größe */
    [data-testid="stImage"] > img {
        width: 70% !important;
        margin-left: auto; margin-right: auto;
        display: block; border-radius: 10px;
    }

    /* Kalender-Zellen & Zeilenumbruch für Name/Fach */
    .fc-event-title {
        font-size: 0.7rem !important;
        white-space: pre-wrap !important; /* Wichtig für Zeilenumbruch */
        line-height: 1.2 !important;
        font-weight: bold !important;
    }
    
    /* Monatsanzeige verkleinert */
    .fc-toolbar-title { font-size: 1.1rem !important; }

    /* Wochenenden & Ferien */
    .fc-day-sat, .fc-day-sun { background-color: #F0F0F0 !important; }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialisierung
if 'started' not in st.session_state: st.session_state.started = False
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    st.markdown('<p class="main-header">Klausuren-<br>Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): st.image("startbild.jpg")
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP ---
else:
    # Daten laden
    response = supabase.table("klausuren").select("*").execute()
    data = response.data
    df = pd.DataFrame(data)

    # --- SIDEBAR: NEUER EINTRAG ---
    with st.sidebar:
        st.header("Neuer Eintrag")
        with st.form("new_form", clear_on_submit=True):
            c = st.selectbox("Kind", CHILDREN)
            s = st.selectbox("Fach", list(SUBJECTS.keys()))
            d = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            n = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                # Titel wird zweizeilig gespeichert: Name + Umbruch + Fach
                title_str = f"{c}\n{s}"
                supabase.table("klausuren").insert({
                    "datum": d.strftime('%d.%m.%Y'), "titel": title_str,
                    "start_date": str(d), "color": SUBJECTS[s], "child": c, "note": n
                }).execute()
                st.rerun()
        if st.button("Zur Startseite"):
            st.session_state.started = False
            st.rerun()

    # --- FERIEN-DATEN ---
    zart_gruen = "#C8E6C9"
    holidays = [
        {"title": "Osterferien", "start": "2025-04-11", "end": "2025-04-27", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien", "start": "2025-07-28", "end": "2025-09-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbstferien", "start": "2025-10-20", "end": "2025-11-01", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnachtsferien", "start": "2025-12-19", "end": "2026-01-08", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Osterferien '26", "start": "2026-03-26", "end": "2026-04-12", "backgroundColor": zart_gruen, "display": "background"}
    ]

    # Events aufbereiten
    calendar_events = []
    for d in data:
        calendar_events.append({
            "id": str(d["id"]), "title": d["titel"], "start": d["start_date"],
            "backgroundColor": d["color"], "allDay": True,
            "textColor": "black" if d["color"] == "#FFD700" else "white"
        })

    # Kalender anzeigen
    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listWeek"},
        "buttonText": {"today": "H", "month": "M", "list": "L"},
        "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "height": "auto"
    }
    
    state = calendar(events=calendar_events + holidays, options=cal_options, key="main_calendar")

    # --- BEARBEITEN / LÖSCHEN LOGIK ---
    if state.get("eventClick"):
        st.session_state.edit_id = state["eventClick"]["event"].get("id")

    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        st.subheader("Eintrag bearbeiten")
        
        # Aktuelle Daten des gewählten Eintrags holen
        edit_row = df[df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
        
        with st.form("edit_form"):
            new_c = st.selectbox("Kind", CHILDREN, index=CHILDREN.index(edit_row['child']))
            # Fach finden (Rückwärts-Suche der Farbe oder Name aus Titel extrahieren)
            current_subject = edit_row['titel'].split('\n')[-1]
            subject_list = list(SUBJECTS.keys())
            new_s = st.selectbox("Fach", subject_list, index=subject_list.index(current_subject) if current_subject in subject_list else 0)
            new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY")
            new_n = st.text_input("Notiz", value=edit_row['note'])
            
            col1, col2, col3 = st.columns([2, 2, 1])
            if col1.form_submit_button("💾 Update"):
                supabase.table("klausuren").update({
                    "datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}",
                    "start_date": str(new_d), "color": SUBJECTS[new_s], "child": new_c, "note": new_n
                }).eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
            
            if col2.form_submit_button("🗑️ Löschen"):
                supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
                
            if col3.form_submit_button("X"):
                st.session_state.edit_id = None
                st.rerun()

    # Übersichtstabelle
    if not df.empty:
        st.divider()
        # Für die Tabelle den Umbruch durch ein Leerzeichen ersetzen
        df_table = df.copy()
        df_table['Anzeige'] = df_table['titel'].str.replace('\n', ': ')
        st.table(df_table.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'}))