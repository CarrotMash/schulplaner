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
SUBJECTS = [
    "Englisch", "Französisch", "Mathematik", "Deutsch", "Musik", 
    "Biologie", "Chemie", "Kunst", "Philosophie", "Geschichte", 
    "Physik", "Spanisch", "WiPo", "Sport", "Religion", "Freistunde"
]
DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
TIMES = {
    1: "07:50 - 08:35", 2: "08:40 - 09:25", 3: "09:40 - 10:25", 4: "10:30 - 11:15",
    5: "11:30 - 12:15", 6: "12:20 - 13:05", 7: "13:35 - 14:20", 8: "14:25 - 15:10"
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
    .time-label { font-size: 0.75rem; color: #666; margin-bottom: 0px; line-height: 1.2; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialisierung
if 'view' not in st.session_state: st.session_state.view = 'start'
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'selected_date' not in st.session_state: st.session_state.selected_date = None
if 'cal_key' not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = "Mila"
if 'started' not in st.session_state: st.session_state.started = False

# --- HELFER: DATEN LADEN (ROBUST GEGEN LEERE TABELLEN) ---
def get_stundenplan(child):
    try:
        res = supabase.table("stundenplaene").select("*").eq("child", child).execute()
        # Wichtig: DataFrame explizit mit Spalten erstellen, falls res.data leer ist
        df = pd.DataFrame(res.data)
        for col in ["id", "child", "tag", "stunde", "fach"]:
            if col not in df.columns:
                df[col] = None
        return df
    except:
        return pd.DataFrame(columns=["id", "child", "tag", "stunde", "fach"])

# --- 1. STARTSEITE ---
if st.session_state.view == 'start':
    st.markdown('<p class="main-header">Klausuren-Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): st.image("startbild.jpg")
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 KLAUSUREN", use_container_width=True, type="primary"):
            st.session_state.view = 'klausuren'
            st.rerun()
    with col2:
        if st.button("🏫 STUNDENPLÄNE", use_container_width=True, type="primary"):
            st.session_state.view = 'stundenplan'
            st.rerun()

# --- 2. KLAUSUREN-BEREICH ---
elif st.session_state.view == 'klausuren':
    try:
        response = supabase.table("klausuren").select("*").execute()
        data, df = response.data, pd.DataFrame(response.data)
    except:
        data, df = [], pd.DataFrame()

    with st.sidebar:
        st.header("Klausuren")
        if st.button("← Hauptmenü"):
            st.session_state.view = 'start'
            st.rerun()
        st.divider()
        with st.form("sb_form", clear_on_submit=True):
            sc = st.selectbox("Kind", list(CHILD_COLORS.keys()))
            ss = st.selectbox("Fach", SUBJECTS)
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            sn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}", "start_date": str(sd), "color": CHILD_COLORS[sc], "child": sc, "note": sn}).execute()
                st.session_state.cal_key = str(uuid.uuid4())
                st.rerun()

    # Kalender
    zart_gruen = "#C8E6C9"
    holidays = [{"title": "Oster", "start": "2025-04-11", "end": "2025-04-26", "backgroundColor": zart_gruen, "display": "background"},
                {"title": "Sommer", "start": "2025-07-28", "end": "2025-09-06", "backgroundColor": zart_gruen, "display": "background"},
                {"title": "Herbst", "start": "2025-10-20", "end": "2025-10-31", "backgroundColor": zart_gruen, "display": "background"},
                {"title": "Weihnacht", "start": "2025-12-19", "end": "2026-01-06", "backgroundColor": zart_gruen, "display": "background"}]
    
    calendar_events = []
    for d_row in data:
        calendar_events.append({"id": str(d_row["id"]), "title": d_row["titel"], "start": d_row["start_date"], "backgroundColor": d_row["color"], "allDay": True, "textColor": "white"})

    state = calendar(events=calendar_events + holidays, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}, "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", "selectable": True, "timeZone": "UTC", "displayEventTime": False, "noEventsText": "Keine Einträge vorhanden"}, key=st.session_state.cal_key)

    if state.get("dateClick"):
        st.session_state.selected_date = state["dateClick"]["date"][:10]
        st.session_state.edit_id = None 
    if state.get("eventClick"):
        st.session_state.edit_id = state["eventClick"]["event"].get("id")
        st.session_state.selected_date = None

    # Formulare unter Kalender
    if st.session_state.selected_date:
        st.divider()
        with st.form("quick_form"):
            st.write(f"**Neu: {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}**")
            qc = st.selectbox("Kind", list(CHILD_COLORS.keys())); qs = st.selectbox("Fach", SUBJECTS); qn = st.text_input("Notiz")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'), "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date, "color": CHILD_COLORS[qc], "child": qc, "note": qn}).execute()
                st.session_state.selected_date = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
            if c2.form_submit_button("Abbrechen"):
                st.session_state.selected_date = None; st.rerun()

    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        try:
            edit_row = df[df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("edit_form"):
                st.write("**Bearbeiten**")
                new_c = st.selectbox("Kind", list(CHILD_COLORS.keys()), index=list(CHILD_COLORS.keys()).index(edit_row['child']))
                curr_s = edit_row['titel'].split('\n')[-1]
                new_s = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(curr_s) if curr_s in SUBJECTS else 0)
                new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY")
                new_n = st.text_input("Notiz", value=edit_row['note'])
                c1, c2, c3 = st.columns([2, 2, 1])
                if c1.form_submit_button("💾 Speichern"):
                    supabase.table("klausuren").update({"datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}", "start_date": str(new_d), "color": CHILD_COLORS[new_c], "child": new_c, "note": new_n}).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c2.form_submit_button("🗑️"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c3.form_submit_button("X"):
                    st.session_state.edit_id = None; st.rerun()
        except: st.session_state.edit_id = None

    if not df.empty:
        st.divider()
        df_table = df.copy(); df_table['Anzeige'] = df_table['titel'].str.replace('\n', ': ')
        df_final = df_table.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'})
        st.dataframe(df_final, hide_index=True, use_container_width=True)
    else: st.info("Keine Einträge vorhanden")

# --- 3. STUNDENPLAN-BEREICH ---
elif st.session_state.view == 'stundenplan':
    st.markdown(f'<div style="background-color:black; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold; font-size:1.5rem; margin-bottom:15px;">🏫 Stundenpläne</div>', unsafe_allow_html=True)
    
    c_col1, c_col2, c_col3 = st.columns(3)
    if c_col1.button("Mila", use_container_width=True): st.session_state.stundenplan_child = "Mila"
    if c_col2.button("Jojo", use_container_width=True): st.session_state.stundenplan_child = "Jojo"
    if c_col3.button("Mikko", use_container_width=True): st.session_state.stundenplan_child = "Mikko"

    current_child = st.session_state.stundenplan_child
    st.write(f"### Plan für {current_child}")

    plan_df = get_stundenplan(current_child)

    for day in DAYS:
        with st.expander(f"📅 {day}", expanded=False):
            for std in range(1, 9):
                # Sicherer Abgleich
                match = plan_df[(plan_df['tag'] == day) & (plan_df['stunde'] == std)]
                current_fach = match.iloc[0]['fach'] if not match.empty else "---"
                
                c_time, c_btn = st.columns([1, 3])
                c_time.markdown(f"<p class='time-label'>{std}. Std<br>{TIMES[std]}</p>", unsafe_allow_html=True)
                if c_btn.button(f"{current_fach}", key=f"p_{current_child}_{day}_{std}", use_container_width=True):
                    st.session_state.edit_lesson = {"day": day, "std": std, "fach": current_fach}

    if 'edit_lesson' in st.session_state:
        el = st.session_state.edit_lesson
        st.divider()
        with st.form("edit_plan_form"):
            st.write(f"**{el['day']}, {el['std']}. Std ändern**")
            new_f = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(el['fach']) if el['fach'] in SUBJECTS else 0)
            cc1, cc2 = st.columns(2)
            if cc1.form_submit_button("Speichern"):
                match = plan_df[(plan_df['tag'] == el['day']) & (plan_df['stunde'] == el['std'])]
                if not match.empty:
                    supabase.table("stundenplaene").update({"fach": new_f}).eq("id", int(match.iloc[0]['id'])).execute()
                else:
                    supabase.table("stundenplaene").insert({"child": current_child, "tag": el['day'], "stunde": el['std'], "fach": new_f}).execute()
                del st.session_state.edit_lesson
                st.rerun()
            if cc2.form_submit_button("Abbrechen"):
                del st.session_state.edit_lesson
                st.rerun()

    if st.button("← Hauptmenü", use_container_width=True):
        st.session_state.view = 'start'
        st.rerun()