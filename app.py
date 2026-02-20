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
    /* 1. SEITENABSTÄNDE */
    .block-container { 
        padding-top: 1.5rem !important; 
    }
    
    /* 2. STARTSEITE: ÜBERSCHRIFT (60% Größe = 2.2rem, Weiß auf Schwarz) */
    .main-header {
        font-size: 2.2rem !important; 
        font-weight: 900 !important;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 15px;
        background-color: #000000; 
        color: #FFFFFF !important;
        padding: 12px;
        border-radius: 10px;
        line-height: 1.1;
    }

    /* 3. STARTBILD: 80% der vorherigen Breite (64% der Gesamtbreite) */
    [data-testid="stImage"] > img {
        width: 64% !important;
        margin-left: auto; margin-right: auto;
        display: block; border-radius: 10px;
    }

    /* 4. KALENDER-BUTTONS: ROT mit WEISSER Schrift */
    .fc-button-primary {
        background-color: #FF4B4B !important; /* Streamlit Rot */
        border-color: #FF4B4B !important;
        color: #FFFFFF !important;
        font-size: 0.85rem !important;
        font-weight: bold !important;
        text-transform: capitalize !important;
        padding: 5px 8px !important;
    }
    .fc-button-primary:hover {
        background-color: #FF2B2B !important;
        border-color: #FF2B2B !important;
    }
    .fc-button-active {
        background-color: #B91D1D !important; /* Dunkleres Rot für aktiven Status */
        border-color: #B91D1D !important;
    }

    /* 5. MONATSANZEIGE: Sauber zentriert */
    .fc-toolbar-title { 
        font-size: 1.2rem !important; 
        font-weight: bold !important;
        color: #31333F !important;
    }

    /* 6. EINTRÄGE: Zweizeilig (Name / Fach) */
    .fc-event-title {
        font-size: 0.75rem !important;
        white-space: pre-wrap !important; 
        line-height: 1.1 !important;
        font-weight: bold !important;
        padding: 2px !important;
    }
    
    /* Wochenenden (Grau) & Ferien (Zartgrün) */
    .fc-day-sat, .fc-day-sun { background-color: #F0F2F6 !important; }
    
    /* Toolbar Layout Optimierung */
    .fc-header-toolbar {
        margin-bottom: 1rem !important;
        display: flex !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
        gap: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialisierung
if 'started' not in st.session_state: st.session_state.started = False
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    st.markdown('<p class="main-header">Klausuren-<br>Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): 
        st.image("startbild.jpg")
    else:
        st.info("Bitte 'startbild.jpg' hochladen.")
    
    st.write("")
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP (Kalenderansicht) ---
else:
    # Daten laden
    try:
        response = supabase.table("klausuren").select("*").execute()
        data = response.data
        df = pd.DataFrame(data)
    except Exception:
        data, df = [], pd.DataFrame()

    # SIDEBAR: NEUER EINTRAG
    with st.sidebar:
        st.header("Neuer Eintrag")
        with st.form("new_form", clear_on_submit=True):
            c = st.selectbox("Kind", CHILDREN)
            s = st.selectbox("Fach", list(SUBJECTS.keys()))
            d = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            n = st.text_input("Notiz (optional)")
            if st.form_submit_button("Speichern"):
                # Speichern als zweizeiliger Titel
                title_str = f"{c}\n{s}"
                supabase.table("klausuren").insert({
                    "datum": d.strftime('%d.%m.%Y'), "titel": title_str,
                    "start_date": str(d), "color": SUBJECTS[s], "child": c, "note": n
                }).execute()
                st.rerun()
        
        st.divider()
        if st.button("Zur Startseite"):
            st.session_state.started = False
            st.rerun()

    # FERIEN (Zartgrün #C8E6C9)
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
    for d_row in data:
        calendar_events.append({
            "id": str(d_row["id"]), 
            "title": d_row["titel"], 
            "start": d_row["start_date"],
            "backgroundColor": d_row["color"], 
            "allDay": True,
            "textColor": "black" if d_row["color"] == "#FFD700" else "white"
        })

    # KALENDER OPTIONEN
    cal_options = {
        "headerToolbar": {
            "left": "prev,next today", 
            "center": "title", 
            "right": "dayGridMonth,listWeek"
        },
        "buttonText": {
            "today": "Heu", 
            "month": "Mon", 
            "list": "Lis"
        },
        "initialView": "dayGridMonth", 
        "locale": "de", 
        "firstDay": 1, 
        "height": "auto"
    }
    
    state = calendar(events=calendar_events + holidays, options=cal_options, key="main_calendar")

    # BEARBEITEN / LÖSCHEN LOGIK (nach Klick auf Event)
    if state.get("eventClick"):
        st.session_state.edit_id = state["eventClick"]["event"].get("id")

    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        st.subheader("Eintrag bearbeiten")
        
        # Den gewählten Eintrag finden
        edit_row = df[df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
        
        with st.form("edit_form"):
            new_c = st.selectbox("Kind", CHILDREN, index=CHILDREN.index(edit_row['child']))
            # Fach extrahieren aus der zweiten Zeile des Titels
            current_s_name = edit_row['titel'].split('\n')[-1]
            s_list = list(SUBJECTS.keys())
            new_s = st.selectbox("Fach", s_list, index=s_list.index(current_s_name) if current_s_name in s_list else 0)
            
            new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY")
            new_n = st.text_input("Notiz", value=edit_row['note'])
            
            c1, c2, c3 = st.columns([2, 2, 1])
            if c1.form_submit_button("💾 Speichern"):
                supabase.table("klausuren").update({
                    "datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}",
                    "start_date": str(new_d), "color": SUBJECTS[new_s], "child": new_c, "note": new_n
                }).eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
            
            if c2.form_submit_button("🗑️ Löschen"):
                supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                st.session_state.edit_id = None
                st.rerun()
            
            if c3.form_submit_button("X"):
                st.session_state.edit_id = None
                st.rerun()

    # Übersichtstabelle ganz unten
    if not df.empty:
        st.divider()
        df_table = df.copy()
        df_table['Anzeige'] = df_table['titel'].str.replace('\n', ': ')
        st.table(df_table.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'}))