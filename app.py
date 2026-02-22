import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
from supabase import create_client
import os
import uuid
import requests

# --- DATENBANK VERBINDUNG ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- KONFIGURATION ---
CHILD_COLORS = {"Mila": "#FF85A1", "Jojo": "#8B0000", "Mikko": "#2E7D32"}
SUBJECTS = ["Englisch", "Französisch", "Mathematik", "Deutsch", "Musik", "Biologie", "Chemie", "Kunst", "Philosophie", "Geschichte", "Physik", "Spanisch", "WiPo", "Geografie", "Sport", "Religion", "Freistunde"]
DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
TIMES = {
    1: "07:50-08:35", 2: "08:40-09:25", 3: "09:40-10:25", 4: "10:30-11:15",
    5: "11:30-12:15", 6: "12:20-13:05", 7: "13:35-14:20"
}

FERIEN_DATA = {
    2026: [{"Ferien": "Osterferien", "Zeitraum": "26.03.2026 - 11.04.2026"}, {"Ferien": "Sommerferien", "Zeitraum": "13.07.2026 - 22.08.2026"}, {"Ferien": "Herbstferien", "Zeitraum": "12.10.2026 - 24.10.2026"}, {"Ferien": "Weihnachtsferien", "Zeitraum": "21.12.2026 - 06.01.2027"}],
    2027: [{"Ferien": "Osterferien", "Zeitraum": "22.03.2027 - 03.04.2027"}, {"Ferien": "Sommerferien", "Zeitraum": "12.07.2027 - 21.08.2027"}, {"Ferien": "Herbstferien", "Zeitraum": "11.10.2027 - 23.10.2027"}, {"Ferien": "Weihnachtsferien", "Zeitraum": "20.12.2027 - 05.01.2028"}]
}

# --- INITIALISIERUNG ---
if 'view' not in st.session_state: st.session_state.view = 'start'
if 'cal_key' not in st.session_state: st.session_state.cal_key = "v1"
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = "Mila"
if 'editing_grade' not in st.session_state: st.session_state.editing_grade = False
if 'selected_date' not in st.session_state: st.session_state.selected_date = None
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

st.set_page_config(page_title="Schulplaner", page_icon="📅", layout="centered")

# --- BASIS CSS ---
st.markdown("""
    <style>
    .block-container { padding-top: 2.7rem !important; }
    .main-header { font-size: 2.2rem !important; font-weight: 900 !important; text-align: center; margin-top: -10px; margin-bottom: 20px; background-color: #000000; color: #FFFFFF !important; padding: 12px; border-radius: 10px; line-height: 1.1; white-space: nowrap; }
    [data-testid="stImage"] > img { width: 64% !important; margin-left: auto; margin-right: auto; display: block; border-radius: 10px; }
    
    .fc-button-primary { background-color: #FF4B4B !important; border-color: #FF4B4B !important; color: #FFFFFF !important; font-weight: bold !important; font-size: 0.8rem !important; text-transform: capitalize !important; }
    .fc-toolbar-title { font-size: 1.1rem !important; font-weight: bold !important; }
    .fc-event-title { font-size: 0.75rem !important; white-space: pre-wrap !important; font-weight: bold !important; line-height: 1.1 !important; }
    .fc-day-sat, .fc-day-sun { background-color: #F0F2F6 !important; }

    /* Namens-Auswahl nebeneinander */
    div[data-testid="stHorizontalBlock"]:has(button[key^="child_sel_"]) {
        display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key^="child_sel_"]) div[data-testid="column"] {
        flex: 1 1 0% !important; min-width: 0 !important;
    }

    .time-label { font-size: 0.65rem; color: #555; font-weight: bold; margin-bottom: 0px; line-height: 1.1; }
    
    .bus-card { background: white; border: 1px solid #ddd; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #FF4B4B; }
    .delay { color: #FF4B4B; font-weight: bold; }
    .ontime { color: #2E7D32; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_bus_departures(stop_id):
    try:
        url = f"https://v6.vbn.transport.rest/stops/{stop_id}/departures?duration=120&results=10"
        return requests.get(url, timeout=10).json().get('departures', [])
    except: return None

# --- 1. DASHBOARD ---
if st.session_state.view == 'start':
    st.markdown('<p class="main-header">Schulplaner</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): st.image("startbild.jpg")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📅 KLAUSUREN", use_container_width=True, type="primary"): st.session_state.view = 'klausuren'; st.rerun()
        if st.button("🚌 BUS-CHECK", use_container_width=True, type="primary"): st.session_state.view = 'bus'; st.rerun()
    with c2:
        if st.button("🏫 STUNDENPLÄNE", use_container_width=True, type="primary"): st.session_state.view = 'stundenplan'; st.rerun()
        if st.button("🌴 FERIEN", use_container_width=True, type="primary"): st.session_state.view = 'ferien'; st.rerun()

# --- 2. KLAUSUREN ---
elif st.session_state.view == 'klausuren':
    try:
        res = supabase.table("klausuren").select("*").execute()
        k_data, k_df = res.data, pd.DataFrame(res.data)
    except: k_data, k_df = [], pd.DataFrame()
    with st.sidebar:
        st.header("Klausuren")
        if st.button("← Hauptmenü"): st.session_state.view = 'start'; st.rerun()
        with st.form("sb_form", clear_on_submit=True):
            sc = st.selectbox("Kind", list(CHILD_COLORS.keys())); ss = st.selectbox("Fach", SUBJECTS)
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY"); sn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}", "start_date": str(sd), "color": CHILD_COLORS[sc], "child": sc, "note": sn}).execute()
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()

    cal_ev = [{"id": str(d["id"]), "title": d["titel"], "start": d["start_date"], "backgroundColor": d["color"], "allDay": True, "textColor": "white"} for d in k_data]
    state = calendar(events=cal_ev, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}, "buttonText": {"today": "Heute", "month": "Monat", "list": "Liste"}, "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", "selectable": True, "timeZone": "UTC", "displayEventTime": False}, key=st.session_state.cal_key)

    if state.get("dateClick"):
        nd = state["dateClick"]["date"][:10]
        if st.session_state.selected_date != nd: st.session_state.selected_date = nd; st.session_state.edit_id = None; st.rerun()
    if state.get("eventClick"):
        ni = state["eventClick"]["event"].get("id")
        if st.session_state.edit_id != ni: st.session_state.edit_id = ni; st.session_state.selected_date = None; st.rerun()

    if st.session_state.selected_date:
        with st.form("q_f"):
            st.write(f"**Neu am {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}**")
            qc = st.selectbox("Kind", list(CHILD_COLORS.keys())); qs = st.selectbox("Fach", SUBJECTS); qn = st.text_input("Notiz")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'), "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date, "color": CHILD_COLORS[qc], "child": qc, "note": qn}).execute()
                st.session_state.selected_date = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
            if c1.form_submit_button("Abbrechen"): st.session_state.selected_date = None; st.rerun()

    if st.session_state.edit_id:
        try:
            edit_row = k_df[k_df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("ed_f"):
                new_c = st.selectbox("Kind", list(CHILD_COLORS.keys()), index=list(CHILD_COLORS.keys()).index(edit_row['child'])); curr_s = edit_row['titel'].split('\n')[-1]
                new_s = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(curr_s) if curr_s in SUBJECTS else 0); new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY"); new_n = st.text_input("Notiz", value=edit_row['note'])
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Speichern"):
                    supabase.table("klausuren").update({"datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}", "start_date": str(new_d), "color": CHILD_COLORS[new_c], "child": new_c, "note": new_n}).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c1.form_submit_button("🗑️ Löschen"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute(); st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
        except: st.session_state.edit_id = None
    if not k_df.empty:
        st.divider(); df_t = k_df.copy(); df_t['Anzeige'] = df_t['titel'].str.replace('\n', ': ')
        st.dataframe(df_t.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'}), hide_index=True, use_container_width=True)

# --- 3. STUNDENPLÄNE ---
elif st.session_state.view == 'stundenplan':
    st.markdown('<p class="main-header">Stundenpläne</p>', unsafe_allow_html=True)
    
    # Kind-Auswahl nebeneinander
    c_cols = st.columns(3)
    for i, name in enumerate(CHILD_COLORS.keys()):
        if c_cols[i].button(name, key=f"child_sel_{name}", use_container_width=True, type="secondary" if st.session_state.stundenplan_child != name else "primary"):
            st.session_state.stundenplan_child = name; st.session_state.editing_grade = False; st.rerun()

    cur_c = st.session_state.stundenplan_child
    child_color = CHILD_COLORS[cur_c]

    # Dynamische Farbe für den Klassen-Button
    st.markdown(f"""
        <style>
        div[data-testid="stButton"] button[key="grade_btn"] {{
            background-color: {child_color} !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            font-size: 1.2rem !important;
            border: none !important;
            width: 100% !important;
            padding: 10px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2) !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    try:
        k_info = supabase.table("kinder_info").select("klasse").eq("child", cur_c).execute().data
        cur_klasse = k_info[0]['klasse'] if k_info else "Klasse ?"
    except: cur_klasse = "Klasse ?"

    # Interaktive Klasse
    if not st.session_state.editing_grade:
        if st.button(f"{cur_klasse}", key="grade_btn", use_container_width=True):
            st.session_state.editing_grade = True; st.rerun()
    else:
        with st.form("grade_form"):
            new_g = st.text_input("Klasse anpassen:", value=cur_klasse)
            if st.form_submit_button("Speichern"):
                supabase.table("kinder_info").upsert({"child": cur_c, "klasse": new_g}).execute()
                st.session_state.editing_grade = False; st.rerun()

    # Stundenplan Daten
    res = supabase.table("stundenplaene").select("*").eq("child", cur_c).execute()
    plan_dict = {(item['tag'], int(item['stunde'])): item for item in res.data}

    st.write("") # Kleiner Puffer

    # Aufklappbare Wochentage (Expander)
    for day in DAYS:
        # Hier nutzen wir Streamlit Expander für das Auf- und Zuklappen
        with st.expander(f"**{day}**", expanded=False):
            for std in range(1, 8):
                lesson = plan_dict.get((day, std))
                fach = lesson['fach'] if lesson else "---"
                col_t, col_f = st.columns([1, 4])
                col_t.markdown(f"<p class='time-label'>{std}. Std<br>{TIMES[std]}</p>", unsafe_allow_html=True)
                if col_f.button(f"{fach}", key=f"p_exp_{cur_c}_{day}_{std}", use_container_width=True):
                    st.session_state.edit_cell = {"day": day, "std": std, "fach": fach, "id": lesson['id'] if lesson else None}

    # Bearbeitungs-Dialog falls eine Stunde geklickt wurde
    if 'edit_cell' in st.session_state:
        ec = st.session_state.edit_cell
        st.divider()
        with st.form("ed_p"):
            st.write(f"📌 **{ec['day']}, {ec['std']}. Std ändern**")
            new_f = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(ec['fach']) if ec['fach'] in SUBJECTS else 0)
            if st.form_submit_button("Speichern"):
                if ec['id']: supabase.table("stundenplaene").update({"fach": new_f}).eq("id", ec['id']).execute()
                else: supabase.table("stundenplaene").insert({"child": cur_c, "tag": ec['day'], "stunde": ec['std'], "fach": new_f}).execute()
                del st.session_state.edit_cell; st.rerun()
            if st.form_submit_button("Abbrechen"): del st.session_state.edit_cell; st.rerun()

    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()

# --- 4. BUS-CHECK ---
elif st.session_state.view == 'bus':
    st.markdown('<p class="main-header">Bus-Check</p>', unsafe_allow_html=True)
    stops = {"Seefischmarkt (Schule ➔ Zuhause)": "de:01002:73144", "Amboßweg (Zuhause ➔ Schule)": "de:01002:73151", "Linas Diek (Zuhause ➔ Schule)": "de:01002:73152"}
    selection = st.selectbox("Haltestelle wählen:", list(stops.keys()))
    if st.button("🔄 Aktualisieren", use_container_width=True): st.rerun()
    departures = get_bus_departures(stops[selection])
    if departures is None: st.error("Daten aktuell nicht verfügbar.")
    elif not departures: st.info("Aktuell keine Abfahrten geplant.")
    else:
        for dep in departures:
            line = dep.get('line', {}).get('name', 'Bus'); direction = dep.get('direction', 'Unbekannt')
            p_time_str = dep.get('plannedDeparture')
            if p_time_str:
                p_time = datetime.fromisoformat(p_time_str.replace('Z', '+00:00'))
                delay_min = int(dep.get('delay', 0) / 60)
                st.markdown(f"""<div class="bus-card"><b>{line}</b> ➔ {direction}<br>Abfahrt: <b>{p_time.strftime('%H:%M')} Uhr</b> <span class="{'delay' if delay_min > 0 else 'ontime'}">({'+' + str(delay_min) if delay_min > 0 else 'pünktlich'})</span></div>""", unsafe_allow_html=True)
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()

# --- 5. FERIEN ---
elif st.session_state.view == 'ferien':
    st.markdown('<p class="main-header">Ferien S-H</p>', unsafe_allow_html=True)
    jahr = st.radio("Jahr:", [2026, 2027], horizontal=True)
    st.dataframe(pd.DataFrame(FERIEN_DATA[jahr]), hide_index=True, use_container_width=True)
    st.caption("Alle Angaben ohne Gewähr")
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()