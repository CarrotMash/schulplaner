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
TIMES = {1: "07:50-08:35", 2: "08:40-09:25", 3: "09:40-10:25", 4: "10:30-11:15", 5: "11:30-12:15", 6: "12:20-13:05", 7: "13:35-14:20", 8: "14:25-15:10"}

FERIEN_DATA = {
    2026: [{"Ferien": "Osterferien", "Zeitraum": "26.03.2026 - 11.04.2026"}, {"Ferien": "Sommerferien", "Zeitraum": "13.07.2026 - 22.08.2026"}, {"Ferien": "Herbstferien", "Zeitraum": "12.10.2026 - 24.10.2026"}, {"Ferien": "Weihnachtsferien", "Zeitraum": "21.12.2026 - 06.01.2027"}],
    2027: [{"Ferien": "Osterferien", "Zeitraum": "22.03.2027 - 03.04.2027"}, {"Ferien": "Sommerferien", "Zeitraum": "12.07.2027 - 21.08.2027"}, {"Ferien": "Herbstferien", "Zeitraum": "11.10.2027 - 23.10.2027"}, {"Ferien": "Weihnachtsferien", "Zeitraum": "20.12.2027 - 05.01.2028"}]
}

st.set_page_config(page_title="Schulplaner", page_icon="📅", layout="centered")

# --- CUSTOM DESIGN ---
st.markdown("""
    <style>
    .block-container { padding-top: 2.7rem !important; }
    .main-header { font-size: 2.2rem !important; font-weight: 900 !important; text-align: center; margin-top: -10px; margin-bottom: 20px; background-color: #000000; color: #FFFFFF !important; padding: 12px; border-radius: 10px; line-height: 1.1; white-space: nowrap; }
    [data-testid="stImage"] > img { width: 64% !important; margin-left: auto; margin-right: auto; display: block; border-radius: 10px; }
    .fc-button-primary { background-color: #FF4B4B !important; border-color: #FF4B4B !important; color: #FFFFFF !important; font-weight: bold !important; font-size: 0.85rem !important; }
    .fc-list-event-time { display: none !important; }
    .fc-event-title { font-size: 0.8rem !important; white-space: pre-wrap !important; font-weight: bold !important; }
    .day-header { text-align: center; border-radius: 5px; padding: 8px; margin-bottom: 10px; font-weight: bold; color: #FFFFFF !important; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .bus-card { background: white; border: 1px solid #ddd; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #FF4B4B; }
    .delay { color: #FF4B4B; font-weight: bold; }
    .ontime { color: #2E7D32; font-weight: bold; }
    
    /* Klassen-Kasten */
    .class-box {
        background-color: #000000;
        color: #FFFFFF !important;
        padding: 5px 10px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
        width: 100%;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISIERUNG ---
if 'view' not in st.session_state: st.session_state.view = 'start'
if 'cal_key' not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = "Mila"
if 'day_offset' not in st.session_state: st.session_state.day_offset = 0

def get_bus_departures(stop_id):
    try:
        # Nutzung der VBN/HAFAS API als stabilere Alternative
        url = f"https://v6.vbn.transport.rest/stops/{stop_id}/departures?duration=120&results=10"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get('departures', [])
        return None
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
        st.header("Schulplaner")
        if st.button("← Hauptmenü"): st.session_state.view = 'start'; st.rerun()
        st.divider()
        with st.form("sb_form", clear_on_submit=True):
            sc = st.selectbox("Kind", list(CHILD_COLORS.keys())); ss = st.selectbox("Fach", SUBJECTS)
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY"); sn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}", "start_date": str(sd), "color": CHILD_COLORS[sc], "child": sc, "note": sn}).execute()
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()

    zart_gruen = "#C8E6C9"
    holidays = [{"title": "Oster", "start": "2025-04-11", "end": "2025-04-26", "backgroundColor": zart_gruen, "display": "background"}, {"title": "Sommer", "start": "2025-07-28", "end": "2025-09-06", "backgroundColor": zart_gruen, "display": "background"}, {"title": "Herbst", "start": "2025-10-20", "end": "2025-10-31", "backgroundColor": zart_gruen, "display": "background"}, {"title": "Weihnacht", "start": "2025-12-19", "end": "2026-01-06", "backgroundColor": zart_gruen, "display": "background"}]
    cal_ev = [{"id": str(d["id"]), "title": d["titel"], "start": d["start_date"], "backgroundColor": d["color"], "allDay": True, "textColor": "white"} for d in k_data]
    
    state = calendar(events=cal_ev + holidays, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}, "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", "selectable": True, "timeZone": "UTC", "displayEventTime": False}, key=st.session_state.cal_key)

    if state.get("dateClick"): st.session_state.selected_date = state["dateClick"]["date"][:10]; st.session_state.edit_id = None; st.rerun()
    if state.get("eventClick"): st.session_state.edit_id = state["eventClick"]["event"].get("id"); st.session_state.selected_date = None; st.rerun()

    if st.session_state.get('selected_date'):
        with st.form("q_f"):
            st.write(f"**Neu am {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}**")
            qc = st.selectbox("Kind", list(CHILD_COLORS.keys())); qs = st.selectbox("Fach", SUBJECTS); qn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'), "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date, "color": CHILD_COLORS[qc], "child": qc, "note": qn}).execute()
                st.session_state.selected_date = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
            if st.form_submit_button("Abbrechen"): st.session_state.selected_date = None; st.rerun()

    if st.session_state.get('edit_id') and st.session_state.edit_id != "undefined":
        try:
            edit_row = k_df[k_df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("ed_f"):
                new_c = st.selectbox("Kind", list(CHILD_COLORS.keys()), index=list(CHILD_COLORS.keys()).index(edit_row['child'])); curr_s = edit_row['titel'].split('\n')[-1]
                new_s = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(curr_s) if curr_s in SUBJECTS else 0); new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY"); new_n = st.text_input("Notiz", value=edit_row['note'])
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Speichern"):
                    supabase.table("klausuren").update({"datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}", "start_date": str(new_d), "color": CHILD_COLORS[new_c], "child": new_c, "note": new_n}).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c2.form_submit_button("🗑️ Löschen"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute(); st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
        except: st.session_state.edit_id = None
    if not k_df.empty:
        df_t = k_df.copy(); df_t['Anzeige'] = df_t['titel'].str.replace('\n', ': ')
        st.dataframe(df_t.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'}), hide_index=True, use_container_width=True)

# --- 3. STUNDENPLÄNE ---
elif st.session_state.view == 'stundenplan':
    st.markdown(f'<div class="main-header">Schulplaner Stundenpläne</div>', unsafe_allow_html=True)
    c_cols = st.columns(3)
    for i, name in enumerate(CHILD_COLORS.keys()):
        if c_cols[i].button(name, use_container_width=True, type="secondary" if st.session_state.stundenplan_child != name else "primary"):
            st.session_state.stundenplan_child = name; st.rerun()

    cur_c = st.session_state.stundenplan_child
    try:
        k_info = supabase.table("kinder_info").select("klasse").eq("child", cur_c).execute().data
        cur_klasse = k_info[0]['klasse'] if k_info else "Klasse ?"
    except: cur_klasse = "Klasse ?"

    # Die Navigations-Zeile
    t_col1, t_col2, t_col3 = st.columns([1, 2, 1])
    with t_col1:
        if st.button("◀", key="prev_day", use_container_width=True): st.session_state.day_offset -= 1; st.rerun()
    with t_col2:
        # Horizontale Anordnung im mittleren Bereich
        m_c1, m_c2 = st.columns([0.8, 0.2])
        m_c1.markdown(f"<div class='class-box'>{cur_klasse}</div>", unsafe_allow_html=True)
        if m_c2.button("✏️", key="edit_grade"): st.session_state.editing_grade = True
    with t_col3:
        if st.button("▶", key="next_day", use_container_width=True): st.session_state.day_offset += 1; st.rerun()

    if st.session_state.get('editing_grade'):
        with st.form("grade_form"):
            new_g = st.text_input("Klasse anpassen:", value=cur_klasse)
            if st.form_submit_button("Übernehmen"):
                supabase.table("kinder_info").upsert({"child": cur_c, "klasse": new_g}).execute()
                st.session_state.editing_grade = False; st.rerun()

    res = supabase.table("stundenplaene").select("*").eq("child", cur_c).execute()
    plan_dict = {(item['tag'], int(item['stunde'])): item for item in res.data}
    start_idx = (datetime.now().weekday() if datetime.now().weekday() < 5 else 0 + st.session_state.day_offset) % 5
    disp_days = [DAYS[(start_idx + i) % 5] for i in range(3)]
    
    cols = st.columns(3)
    for i, day in enumerate(disp_days):
        with cols[i]:
            st.markdown(f"<div class='day-header' style='background:{CHILD_COLORS[cur_c]};'>{day}</div>", unsafe_allow_html=True)
            for std in range(1, 9):
                lesson = plan_dict.get((day, std))
                fach = lesson['fach'] if lesson else "---"
                if st.button(f"{fach}", key=f"p_{cur_c}_{day}_{std}_{i}", use_container_width=True):
                    st.session_state.edit_cell = {"day": day, "std": std, "fach": fach, "id": lesson['id'] if lesson else None}
    
    if 'edit_cell' in st.session_state:
        ec = st.session_state.edit_cell
        with st.form("ed_p"):
            new_f = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(ec['fach']) if ec['fach'] in SUBJECTS else 0)
            if st.form_submit_button("Speichern"):
                if ec['id']: supabase.table("stundenplaene").update({"fach": new_f}).eq("id", ec['id']).execute()
                else: supabase.table("stundenplaene").insert({"child": cur_c, "tag": ec['day'], "stunde": ec['std'], "fach": new_f}).execute()
                del st.session_state.edit_cell; st.rerun()
            if st.form_submit_button("Abbrechen"): del st.session_state.edit_cell; st.rerun()
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()

# --- 4. BUS-CHECK ---
elif st.session_state.view == 'bus':
    st.markdown('<div class="main-header">Schulplaner Bus</div>', unsafe_allow_html=True)
    stops = {"Seefischmarkt (Schule ➔ Zuhause)": "de:01002:73144", "Amboßweg (Zuhause ➔ Schule)": "de:01002:73151", "Linas Diek (Zuhause ➔ Schule)": "de:01002:73152"}
    selection = st.selectbox("Haltestelle wählen:", list(stops.keys()))
    if st.button("🔄 Aktualisieren", use_container_width=True): st.rerun()
    departures = get_bus_departures(stops[selection])
    if departures is None: st.error("Daten aktuell nicht verfügbar (Server-Wartung).")
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
    st.markdown('<div class="main-header">Ferien Schleswig-Holstein</div>', unsafe_allow_html=True)
    jahr = st.radio("Jahr:", [2026, 2027], horizontal=True)
    st.dataframe(pd.DataFrame(FERIEN_DATA[jahr]), hide_index=True, use_container_width=True)
    st.caption("Alle Angaben ohne Gewähr")
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()