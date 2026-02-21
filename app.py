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
SUBJECTS = ["Englisch", "Französisch", "Mathematik", "Deutsch", "Musik", "Biologie", "Chemie", "Kunst", "Philosophie", "Geschichte", "Physik", "Spanisch", "WiPo", "Geografie", "Sport", "Religion", "Freistunde"]
DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
TIMES = {1: "07:50-08:35", 2: "08:40-09:25", 3: "09:40-10:25", 4: "10:30-11:15", 5: "11:30-12:15", 6: "12:20-13:05", 7: "13:35-14:20", 8: "14:25-15:10"}

# --- FERIENDATEN SH 2026/2027 ---
FERIEN_SH = [
    {"Jahr": 2026, "Ferien": "Osterferien", "Zeitraum": "26.03. - 11.04."},
    {"Jahr": 2026, "Ferien": "Sommerferien", "Zeitraum": "13.07. - 22.08."},
    {"Jahr": 2026, "Ferien": "Herbstferien", "Zeitraum": "12.10. - 24.10."},
    {"Jahr": 2026, "Ferien": "Weihnachtsferien", "Zeitraum": "21.12. - 06.01."},
    {"Jahr": 2027, "Ferien": "Osterferien", "Zeitraum": "22.03. - 03.04."},
    {"Jahr": 2027, "Ferien": "Sommerferien", "Zeitraum": "12.07. - 21.08."},
    {"Jahr": 2027, "Ferien": "Herbstferien", "Zeitraum": "11.10. - 23.10."},
    {"Jahr": 2027, "Ferien": "Weihnachtsferien", "Zeitraum": "20.12. - 05.01."}
]

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
    .day-header { text-align: center; border-radius: 5px; padding: 8px; margin-bottom: 10px; font-weight: bold; color: #FFFFFF !important; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .time-label { font-size: 0.7rem; color: #444; margin-bottom: 0px; line-height: 1.1; font-weight: bold; }
    
    /* Bus-Sektion Button Styling */
    .bus-info { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #FF4B4B; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialisierung
if 'view' not in st.session_state: st.session_state.view = 'start'
if 'cal_key' not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = "Mila"
if 'day_offset' not in st.session_state: st.session_state.day_offset = 0

def get_today_index():
    idx = datetime.now().weekday()
    return idx if idx < 5 else 0

# --- 1. DASHBOARD (STARTSEITE) ---
if st.session_state.view == 'start':
    st.markdown('<p class="main-header">Klausuren-Planer</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"): st.image("startbild.jpg")
    st.write("")
    
    # 2x2 Raster
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        if st.button("📅 KLAUSUREN", use_container_width=True, type="primary"):
            st.session_state.view = 'klausuren'; st.rerun()
    with row1_col2:
        if st.button("🏫 PLÄNE", use_container_width=True, type="primary"):
            st.session_state.view = 'stundenplan'; st.rerun()
    with row2_col1:
        if st.button("🚌 BUS-CHECK", use_container_width=True, type="primary"):
            st.session_state.view = 'bus'; st.rerun()
    with row2_col2:
        if st.button("🌴 FERIEN", use_container_width=True, type="primary"):
            st.session_state.view = 'ferien'; st.rerun()

# --- 2. KLAUSUREN-BEREICH ---
elif st.session_state.view == 'klausuren':
    try:
        response = supabase.table("klausuren").select("*").execute()
        k_data, k_df = response.data, pd.DataFrame(response.data)
    except:
        k_data, k_df = [], pd.DataFrame()

    with st.sidebar:
        st.header("Neuer Eintrag")
        with st.form("sb_form", clear_on_submit=True):
            sc = st.selectbox("Kind", list(CHILD_COLORS.keys())); ss = st.selectbox("Fach", SUBJECTS)
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY"); sn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}", "start_date": str(sd), "color": CHILD_COLORS[sc], "child": sc, "note": sn}).execute()
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
        st.divider()
        if st.button("← Hauptmenü"): st.session_state.view = 'start'; st.rerun()

    zart_gruen = "#C8E6C9"
    holidays = [{"title": "Oster", "start": "2025-04-11", "end": "2025-04-26", "backgroundColor": zart_gruen, "display": "background"},
                {"title": "Sommer", "start": "2025-07-28", "end": "2025-09-06", "backgroundColor": zart_gruen, "display": "background"},
                {"title": "Herbst", "start": "2025-10-20", "end": "2025-10-31", "backgroundColor": zart_gruen, "display": "background"},
                {"title": "Weihnacht", "start": "2025-12-19", "end": "2026-01-06", "backgroundColor": zart_gruen, "display": "background"}]
    
    cal_events = []
    for d in k_data:
        cal_events.append({"id": str(d["id"]), "title": d["titel"], "start": d["start_date"], "backgroundColor": d["color"], "allDay": True, "textColor": "white"})

    state = calendar(events=cal_events + holidays, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"}, "initialView": "dayGridMonth", "locale": "de", "firstDay": 1, "weekends": False, "height": "auto", "selectable": True, "timeZone": "UTC", "displayEventTime": False, "noEventsText": "Keine Einträge vorhanden"}, key=st.session_state.cal_key)

    if state.get("dateClick"): st.session_state.selected_date = state["dateClick"]["date"][:10]; st.session_state.edit_id = None 
    if state.get("eventClick"): st.session_state.edit_id = state["eventClick"]["event"].get("id"); st.session_state.selected_date = None

    if st.session_state.selected_date:
        st.divider()
        with st.form("quick_f"):
            st.write(f"**Neu: {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}**")
            qc = st.selectbox("Kind", list(CHILD_COLORS.keys())); qs = st.selectbox("Fach", SUBJECTS); qn = st.text_input("Notiz")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({"datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'), "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date, "color": CHILD_COLORS[qc], "child": qc, "note": qn}).execute()
                st.session_state.selected_date = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
            if c2.form_submit_button("Abbrechen"): st.session_state.selected_date = None; st.rerun()

    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        try:
            edit_row = k_df[k_df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("edit_f"):
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
                if c3.form_submit_button("X"): st.session_state.edit_id = None; st.rerun()
        except: st.session_state.edit_id = None

    if not k_df.empty:
        st.divider()
        df_table = k_df.copy(); df_table['Anzeige'] = df_table['titel'].str.replace('\n', ': ')
        st.dataframe(df_table.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum':'Wann', 'Anzeige':'Wer & Was'}), hide_index=True, use_container_width=True)

# --- 3. STUNDENPLAN-BEREICH ---
elif st.session_state.view == 'stundenplan':
    st.markdown('<div style="background-color:black; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold; font-size:1.5rem; margin-bottom:15px;">🏫 Stundenpläne</div>', unsafe_allow_html=True)
    c_cols = st.columns(3)
    for i, name in enumerate(CHILD_COLORS.keys()):
        if c_cols[i].button(name, use_container_width=True, type="secondary" if st.session_state.stundenplan_child != name else "primary"):
            st.session_state.stundenplan_child = name; st.rerun()

    current_child = st.session_state.stundenplan_child
    child_color = CHILD_COLORS[current_child]
    
    res = supabase.table("stundenplaene").select("*").eq("child", current_child).execute()
    plan_dict = {(item['tag'], int(item['stunde'])): item for item in res.data}

    t_col1, t_col2, t_col3 = st.columns([1, 2, 1])
    if t_col1.button("◀", use_container_width=True): st.session_state.day_offset -= 1; st.rerun()
    t_col2.markdown(f"<center><small>Blättern</small></center>", unsafe_allow_html=True)
    if t_col3.button("▶", use_container_width=True): st.session_state.day_offset += 1; st.rerun()

    start_idx = (get_today_index() + st.session_state.day_offset) % 5
    display_days = [DAYS[(start_idx + i) % 5] for i in range(3)]

    cols = st.columns(3)
    for i, day in enumerate(display_days):
        with cols[i]:
            st.markdown(f"<div class='day-header' style='background:{child_color};'>{day}</div>", unsafe_allow_html=True)
            for std in range(1, 9):
                lesson = plan_dict.get((day, std))
                fach = lesson['fach'] if lesson else "---"
                if st.button(f"{fach}", key=f"btn_{day}_{std}_{i}", help=f"{std}. Std: {TIMES[std]}", use_container_width=True):
                    st.session_state.edit_cell = {"day": day, "std": std, "fach": fach, "id": lesson['id'] if lesson else None}

    if 'edit_cell' in st.session_state:
        ec = st.session_state.edit_cell
        st.divider()
        with st.form("edit_plan_f"):
            st.write(f"📌 **{ec['day']}, {ec['std']}. Std**")
            new_f = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(ec['fach']) if ec['fach'] in SUBJECTS else 0)
            if st.form_submit_button("Speichern"):
                if ec['id']: supabase.table("stundenplaene").update({"fach": new_f}).eq("id", ec['id']).execute()
                else: supabase.table("stundenplaene").insert({"child": current_child, "tag": ec['day'], "stunde": ec['std'], "fach": new_f}).execute()
                del st.session_state.edit_cell; st.rerun()
            if st.form_submit_button("Abbrechen"): del st.session_state.edit_cell; st.rerun()

    st.write("")
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.session_state.day_offset = 0; st.rerun()

# --- 4. BUS-CHECK BEREICH ---
elif st.session_state.view == 'bus':
    st.markdown('<div style="background-color:black; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold; font-size:1.5rem; margin-bottom:15px;">🚌 Bus-Check</div>', unsafe_allow_html=True)
    
    st.info("Tippe auf eine Haltestelle, um die Live-Abfahrten (NAH.SH) zu sehen.")
    
    # Haltestelle 1: Schule
    st.markdown("<div class='bus-info'><b>Schule -> Nach Hause</b><br>Kiel Seefischmarkt (Ri. Schönberg)</div>", unsafe_allow_html=True)
    st.link_button("➔ Abfahrten Seefischmarkt", "https://www.nah.sh/de/fahrplan/abfahrtsmonitor/?stop=Kiel%2C+Seefischmarkt", use_container_width=True)
    
    st.write("")
    
    # Haltestelle 2 & 3: Zuhause
    st.markdown("<div class='bus-info'><b>Zuhause -> Kiel / Schule</b><br>Schönkirchen (Ri. Kiel ZOB)</div>", unsafe_allow_html=True)
    st.link_button("➔ Abfahrten Amboßweg", "https://www.nah.sh/de/fahrplan/abfahrtsmonitor/?stop=Sch%C3%B6nkirchen%2C+Ambo%C3%9Fweg", use_container_width=True)
    st.link_button("➔ Abfahrten Linas Diek", "https://www.nah.sh/de/fahrplan/abfahrtsmonitor/?stop=Sch%C3%B6nkirchen%2C+Linas+Diek", use_container_width=True)
    
    st.write("")
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()

# --- 5. FERIEN BEREICH ---
elif st.session_state.view == 'ferien':
    st.markdown('<div style="background-color:black; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold; font-size:1.5rem; margin-bottom:15px;">🌴 Ferien SH</div>', unsafe_allow_html=True)
    
    jahr = st.radio("Jahr wählen:", [2026, 2027], horizontal=True)
    
    f_df = pd.DataFrame(FERIEN_SH)
    filtered_df = f_df[f_df['Jahr'] == jahr][['Ferien', 'Zeitraum']]
    
    st.table(filtered_df)
    
    st.info("Daten für Schleswig-Holstein. Alle Angaben ohne Gewähr.")
    
    if st.button("← Hauptmenü", use_container_width=True): st.session_state.view = 'start'; st.rerun()