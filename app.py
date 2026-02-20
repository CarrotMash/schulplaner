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

# --- KONFIGURATION: KINDER-FARBEN & FÄCHER ---
CHILD_COLORS = {"Mila": "#FF85A1", "Jojo": "#8B0000", "Mikko": "#2E7D32"}
SUBJECTS = ["Englisch", "Französisch", "Mathematik", "Deutsch", "Musik", "Biologie", "Chemie", "Kunst", "Philosophie", "Geschichte", "Physik", "Spanisch", "WiPo"]

st.set_page_config(page_title="Klausuren-Planer", page_icon="📅", layout="centered")

# --- CUSTOM DESIGN (CSS) ---
st.markdown("""
    <style>
    /* 1. SEITENABSTAND: Schutz gegen Abschneiden oben */
    .block-container { 
        padding-top: 6.5rem !important; 
    }
    
    /* 2. STARTSEITE: ÜBERSCHRIFT (1.8rem = nochmals 10% kleiner) */
    .main-header {
        font-size: 1.8rem !important; 
        font-weight: 900 !important;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 15px;
        background-color: #000000; 
        color: #FFFFFF !important;
        padding: 10px;
        border-radius: 10px;
        white-space: nowrap;
    }

    /* 3. STARTBILD: Um weitere 30% verkleinert (ca. 40% Gesamtbreite) */
    [data-testid="stImage"] > img {
        width: 40% !important;
        max-height: 140px !important;
        margin-left: auto; margin-right: auto;
        display: block; border-radius: 10px;
    }

    /* 4. KALENDER-NAVIGATION: Ausrichtung & Abstände */
    .fc-header-toolbar {
        margin-top: 20px !important;
        margin-bottom: 2.0rem !important;
        display: flex !important;
        align-items: center !important;
    }
    .fc-toolbar-chunk:nth-child(1) {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 6px !important;
    }

    /* 5. BUTTONS STYLING (Rot/Weiß) */
    .fc-button-primary {
        background-color: #FF4B4B !important;
        border-color: #FF4B4B !important;
        color: #FFFFFF !important;
        font-size: 0.85rem !important;
        font-weight: bold !important;
    }

    /* 6. LISTE: "all-day" / "ganztägig" entfernen */
    .fc-list-event-time { display: none !important; }

    .fc-toolbar-title { font-size: 1.25rem !important; font-weight: bold !important; }
    .fc-event-title { font-size: 0.75rem !important; white-space: pre-wrap !important; font-weight: bold !important; }
    .fc-day-sat, .fc-day-sun { background-color: #F0F2F6 !important; }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialisierung (Wichtig für Stabilität)
if 'started' not in st.session_state: st.session_state.started = False
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'selected_date' not in st.session_state: st.session_state.selected_date = None
if 'cal_key' not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())

# --- 1. STARTBILDSCHIRM ---
if st.session_state.started == False:
    st.markdown('<p class="main-header">Klausuren-Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): 
        st.image("startbild.jpg")
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    if st.button("JETZT STARTEN", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.rerun()

# --- 2. HAUPT-APP ---
else:
    # Daten laden
    try:
        response = supabase.table("klausuren").select("*").execute()
        data, df = response.data, pd.DataFrame(response.data)
    except:
        data, df = [], pd.DataFrame()

    with st.sidebar:
        st.header("Menü")
        if st.button("Abmelden / Startseite"):
            st.session_state.started = False
            st.rerun()

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
        calendar_events.append({
            "id": str(d_row["id"]), "title": d_row["titel"], "start": d_row["start_date"],
            "backgroundColor": d_row["color"], "allDay": True, "textColor": "white"
        })

    # KALENDER OPTIONEN
    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"},
        "buttonText": {"today": "Heute", "month": "Monat", "list": "Liste"},
        "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", 
        "selectable": True, "timeZone": "UTC", "displayEventTime": False
    }
    
    # Kalender-Widget mit dynamischem Key für Force-Refresh
    state = calendar(events=calendar_events + holidays, options=cal_options, key=st.session_state.cal_key)

    # --- LOGIK: DATE/EVENT CLICK ---
    if state.get("dateClick"):
        st.session_state.selected_date = state["dateClick"]["date"][:10]
        st.session_state.edit_id = None 
    if state.get("eventClick"):
        st.session_state.edit_id = state["eventClick"]["event"].get("id")
        st.session_state.selected_date = None

    # NEUER EINTRAG
    if st.session_state.selected_date:
        st.divider()
        with st.form("quick_new_form"):
            st.write(f"**Neu am {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}**")
            qc = st.selectbox("Kind", list(CHILD_COLORS.keys())); qs = st.selectbox("Fach", SUBJECTS); qn = st.text_input("Notiz")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'), "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date, "color": CHILD_COLORS[qc], "child": qc, "note": qn}).execute()
                st.session_state.selected_date = None
                st.session_state.cal_key = str(uuid.uuid4()) # Zwingt Kalender zum Neuladen
                st.rerun()
            if c2.form_submit_button("Abbrechen"):
                st.session_state.selected_date = None; st.rerun()

    # BEARBEITEN / LÖSCHEN
    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        try:
            edit_row = df[df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("edit_form"):
                new_c = st.selectbox("Kind", list(CHILD_COLORS.keys()), index=list(CHILD_COLORS.keys()).index(edit_row['child']))
                curr_s = edit_row['titel'].split('\n')[-1]
                new_s = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(curr_s) if curr_s in SUBJECTS else 0)
                new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY")
                new_n = st.text_input("Notiz", value=edit_row['note'])
                c1, c2, c3 = st.columns([2, 2, 1])
                if c1.form_submit_button("Speichern"):
                    supabase.table("klausuren").update({"datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}", "start_date": str(new_d), "color": CHILD_COLORS[new_c], "child": new_c, "note": new_n}).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c2.form_submit_button("🗑️ Löschen"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None
                    st.session_state.cal_key = str(uuid.uuid4()) # ESSENZIELL: Ändert den Key vor dem Rerun
                    st.toast("Eintrag gelöscht!")
                    st.rerun()
                if c3.form_submit_button("X"):
                    st.session_state.edit_id = None; st.rerun()
        except: st.session_state.edit_id = None

    # Tabelle ganz unten (ohne die "0")
    if not df.empty:
        st.divider()
        df_table = df.copy(); df_table['Anzeige'] = df_table['titel'].str.replace('\n', ': ')
        df_final = df_table.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'})
        st.dataframe(df_final, hide_index=True, use_container_width=True)