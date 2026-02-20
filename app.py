import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date, timedelta
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

st.set_page_config(page_title="Klausuren-Planer", page_icon="📅", layout="centered")

# --- CUSTOM DESIGN (CSS) ---
st.markdown("""
    <style>
    /* 1. SEITENABSTAND: Noch weiter vergrößert für absolute Sichtbarkeit */
    .block-container { 
        padding-top: 5.5rem !important; 
        padding-bottom: 0rem !important;
    }
    
    /* 2. ÜBERSCHRIFT STARTSEITE (einzeilig, schwarz/weiß) */
    .main-header {
        font-size: 2.0rem !important; 
        font-weight: 900 !important;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 20px;
        background-color: #000000; 
        color: #FFFFFF !important;
        padding: 12px;
        border-radius: 10px;
        line-height: 1.1;
        white-space: nowrap;
    }

    /* 3. STARTBILD: 58% Breite */
    [data-testid="stImage"] > img {
        width: 58% !important;
        margin-left: auto; margin-right: auto;
        display: block; border-radius: 10px;
    }

    /* 4. KALENDER-NAVIGATION: Heute unter Pfeilen & extra Abstand nach oben */
    .fc-header-toolbar {
        margin-top: 35px !important;
        margin-bottom: 2.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
    }
    .fc-toolbar-chunk:nth-child(1) {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 8px !important;
    }

    /* 5. BUTTONS STYLING (Rot/Weiß) */
    .fc-button-primary {
        background-color: #FF4B4B !important;
        border-color: #FF4B4B !important;
        color: #FFFFFF !important;
        font-size: 0.85rem !important;
        font-weight: bold !important;
    }
    .fc-button-active {
        background-color: #B91D1D !important;
        border-color: #B91D1D !important;
    }

    /* Titel (Monat) & Einträge */
    .fc-toolbar-title { font-size: 1.3rem !important; font-weight: bold !important; }
    .fc-event-title { font-size: 0.8rem !important; white-space: pre-wrap !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# Session State
if 'started' not in st.session_state: st.session_state.started = False
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'selected_date' not in st.session_state: st.session_state.selected_date = None

# --- 1. STARTBILDSCHIRM ---
if not st.session_state.started:
    st.markdown('<p class="main-header">Klausuren-Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): 
        st.image("startbild.jpg")
    st.write("")
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP ---
else:
    try:
        response = supabase.table("klausuren").select("*").execute()
        data, df = response.data, pd.DataFrame(response.data)
    except:
        data, df = [], pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Neuer Eintrag")
        with st.form("sidebar_form", clear_on_submit=True):
            sc = st.selectbox("Kind", CHILDREN); ss = st.selectbox("Fach", list(SUBJECTS.keys()))
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY"); sn = st.text_input("Notiz (optional)")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}", "start_date": str(sd), "color": SUBJECTS[ss], "child": sc, "note": sn}).execute()
                st.rerun()
        if st.button("Zur Startseite"):
            st.session_state.started = False; st.rerun()

    # FERIEN (Zartgrün)
    zart_gruen = "#C8E6C9"
    holidays = [
        {"title": "Oster", "start": "2025-04-11", "end": "2025-04-26", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommer", "start": "2025-07-28", "end": "2025-09-06", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbst", "start": "2025-10-20", "end": "2025-10-31", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnacht", "start": "2025-12-19", "end": "2026-01-06", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Oster '26", "start": "2026-03-26", "end": "2026-04-11", "backgroundColor": zart_gruen, "display": "background"}
    ]

    calendar_events = []
    for d_row in data:
        calendar_events.append({"id": str(d_row["id"]), "title": d_row["titel"], "start": d_row["start_date"], "backgroundColor": d_row["color"], "allDay": True, "textColor": "black" if d_row["color"] == "#FFD700" else "white"})

    # KALENDER OPTIONEN (Ohne Wochenende)
    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listWeek"},
        "buttonText": {"today": "Heute", "month": "Mon", "list": "Lis"},
        "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", "selectable": True,
    }
    
    state = calendar(events=calendar_events + holidays, options=cal_options, key="main_calendar")

    # LOGIK: DATE CLICK (Fix für Datums-Shift)
    if state.get("dateClick"):
        # Wir nehmen den Datums-String direkt und ignorieren alles nach dem 'T', um Verschiebungen zu vermeiden
        raw_date = str(state["dateClick"]["date"])
        st.session_state.selected_date = raw_date.split("T")[0]
        st.session_state.edit_id = None 

    if state.get("eventClick"):
        st.session_state.edit_id = state["eventClick"]["event"].get("id")
        st.session_state.selected_date = None

    # SCHNELL-EINTRAG UNTER KALENDER
    if st.session_state.selected_date:
        st.divider()
        st.subheader(f"Neu: {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}")
        with st.form("quick_new_form"):
            qc = st.selectbox("Kind", CHILDREN); qs = st.selectbox("Fach", list(SUBJECTS.keys())); qn = st.text_input("Notiz")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'), "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date, "color": SUBJECTS[qs], "child": qc, "note": qn}).execute()
                st.session_state.selected_date = None; st.rerun()
            if c2.form_submit_button("Abbrechen"):
                st.session_state.selected_date = None; st.rerun()

    # BEARBEITEN / LÖSCHEN UNTER KALENDER
    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        st.subheader("Eintrag bearbeiten")
        try:
            edit_row = df[df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("edit_form"):
                new_c = st.selectbox("Kind", CHILDREN, index=CHILDREN.index(edit_row['child']))
                curr_s = edit_row['titel'].split('\n')[-1]
                s_list = list(SUBJECTS.keys())
                new_s = st.selectbox("Fach", s_list, index=s_list.index(curr_s) if curr_s in s_list else 0)
                new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY")
                new_n = st.text_input("Notiz", value=edit_row['note'])
                c1, c2, c3 = st.columns([2, 2, 1])
                if c1.form_submit_button("Speichern"): # Geändert von Save
                    supabase.table("klausuren").update({"datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}", "start_date": str(new_d), "color": SUBJECTS[new_s], "child": new_c, "note": new_n}).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.rerun()
                if c2.form_submit_button("🗑️ Löschen"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.rerun()
                if c3.form_submit_button("X"):
                    st.session_state.edit_id = None; st.rerun()
        except: st.session_state.edit_id = None

    # Tabelle
    if not df.empty:
        st.divider()
        df_table = df.copy(); df_table['Anzeige'] = df_table['titel'].str.replace('\n', ': ')
        st.table(df_table.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'}))