import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, date
import zoneinfo
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
TIMES = {1: "07:50-08:35", 2: "08:40-09:25", 3: "09:40-10:25", 4: "10:30-11:15", 5: "11:30-12:15", 6: "12:20-13:05", 7: "13:35-14:20"}

FERIEN_DATA = {
    2026: [
        {"Ferien": "Osterferien", "Zeitraum": "26.03.2026 - 11.04.2026"},
        {"Ferien": "Sommerferien", "Zeitraum": "13.07.2026 - 22.08.2026"},
        {"Ferien": "Herbstferien", "Zeitraum": "12.10.2026 - 24.10.2026"},
        {"Ferien": "Weihnachtsferien", "Zeitraum": "21.12.2026 - 06.01.2027"}
    ],
    2027: [
        {"Ferien": "Osterferien", "Zeitraum": "22.03.2027 - 03.04.2027"},
        {"Ferien": "Sommerferien", "Zeitraum": "12.07.2027 - 21.08.2027"},
        {"Ferien": "Herbstferien", "Zeitraum": "11.10.2027 - 23.10.2027"},
        {"Ferien": "Weihnachtsferien", "Zeitraum": "20.12.2027 - 05.01.2028"}
    ]
}

# --- SESSION STATE INITIALISIERUNG ---
if 'view' not in st.session_state: st.session_state.view = 'start'
if 'cal_key' not in st.session_state: st.session_state.cal_key = str(uuid.uuid4())
if 'stundenplan_child' not in st.session_state: st.session_state.stundenplan_child = "Mila"
if 'editing_grade' not in st.session_state: st.session_state.editing_grade = False
if 'selected_date' not in st.session_state: st.session_state.selected_date = None
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

st.set_page_config(page_title="Schulplaner", page_icon="📅", layout="centered")

# PWA-Manifest
st.markdown(
    '''
    <link rel="manifest" href="data:application/json;base64,eyJuYW1lIjogIlNjaHVscGxhbmVyIiwgInNob3J0X25hbWUiOiAiU2NodWxwbGFuZXIiLCAiZGVzY3JpcHRpb24iOiAiRmFtaWxpZW4tU2NodWxwbGFuZXIiLCAic3RhcnRfdXJsIjogIi8iLCAiZGlzcGxheSI6ICJzdGFuZGFsb25lIiwgIm9yaWVudGF0aW9uIjogInBvcnRyYWl0IiwgImJhY2tncm91bmRfY29sb3IiOiAiI0ZGRkZGRiIsICJ0aGVtZV9jb2xvciI6ICIjRkY0QjRCIiwgImljb25zIjogW3sic3JjIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvZmx1ZW50dWktZW1vamkvbWFpbi9hc3NldHMvU3BpcmFsJTIwY2FsZW5kYXIvM0Qvc3BpcmFsX2NhbGVuZGFyXzNkLnBuZyIsICJzaXplcyI6ICIyNTZ4MjU2IiwgInR5cGUiOiAiaW1hZ2UvcG5nIiwgInB1cnBvc2UiOiAiYW55IG1hc2thYmxlIn1dfQ==">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#FF4B4B">
    <script>
    window.addEventListener('beforeinstallprompt', function(e) {
        e.preventDefault();
        window.deferredPrompt = e;
        setTimeout(function() {
            if (window.deferredPrompt) {
                window.deferredPrompt.prompt();
                window.deferredPrompt.userChoice.then(function() {
                    window.deferredPrompt = null;
                });
            }
        }, 3000);
    });
    </script>
    ''',
    unsafe_allow_html=True
)


# --- CUSTOM DESIGN (CSS) ---
st.markdown("""
    <style>
    .block-container { padding-top: 2.7rem !important; padding-bottom: 5rem !important; }

    .main-header {
        font-size: 2.2rem !important; font-weight: 900 !important;
        text-align: center; margin-top: -10px; margin-bottom: 20px;
        background-color: #000000; color: #FFFFFF !important;
        padding: 12px; border-radius: 10px; line-height: 1.1; white-space: nowrap;
    }

    [data-testid="stImage"] > img {
        width: 35% !important; margin-left: auto; margin-right: auto;
        display: block; border-radius: 10px;
    }

    .fc-button-primary {
        background-color: #FF4B4B !important; border-color: #FF4B4B !important;
        color: #FFFFFF !important; font-weight: bold !important;
        font-size: 0.8rem !important; text-transform: capitalize !important;
    }
    .fc-button-active { background-color: #B91D1D !important; border-color: #B91D1D !important; }
    .fc-toolbar-title { font-size: 1.1rem !important; font-weight: bold !important; }
    .fc-event-title { font-size: 0.75rem !important; white-space: pre-wrap !important; font-weight: bold !important; line-height: 1.1 !important; }
    .fc-day-sat, .fc-day-sun { background-color: #F0F2F6 !important; }
    .fc-list-event-time { display: none !important; }

    /* Einheitliche Button-Höhe im Bus-Check */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
        height: 60px !important;
        white-space: normal !important;
        line-height: 1.3 !important;
        font-size: 0.85rem !important;
    }

    .bus-card {
        background: white; border: 1px solid #ddd; padding: 12px;
        border-radius: 10px; margin-bottom: 10px;
        border-left: 6px solid #FF4B4B;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .delay { color: #FF4B4B; font-weight: bold; }
    .ontime { color: #2E7D32; font-weight: bold; }
    /* Streamlit-UI-Elemente ausblenden */
    #MainMenu                                { display: none !important; }
    footer                                   { display: none !important; }
    header                                   { display: none !important; }
    [data-testid="stDeployButton"]           { display: none !important; }
    [data-testid="stToolbar"]                { display: none !important; }
    [data-testid="stDecoration"]             { display: none !important; }
    [data-testid="stMainMenuPopover"]        { display: none !important; }
    .viewerBadge_container__r5tak           { display: none !important; }
    .viewerBadge_link__qRIco                { display: none !important; }
    /* "Manage App"-Badge unten rechts */
    [data-testid="manage-app-button"]        { display: none !important; }
    ._profileContainer_gzau3_53             { display: none !important; }
    ._container_gzau3_1                     { display: none !important; }
    /* Toolbar-Buttons oben rechts (Share, Favorit, Stift, GitHub) */
    [data-testid="stActionButton"]           { display: none !important; }
    [data-testid="baseButton-headerNoPadding"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)





# Streamlit-UI per JavaScript dauerhaft entfernen (MutationObserver)
st.markdown("""
<script>
(function() {
    function removeStreamlitUI() {
        // Alle bekannten Selektoren für Streamlit-UI-Elemente
        var selectors = [
            '[data-testid="manage-app-button"]',
            '[data-testid="stDeployButton"]',
            '[data-testid="stToolbar"]',
            '[data-testid="stMainMenuPopover"]',
            '[data-testid="stActionButton"]',
            '._container_gzau3_1',
            '._profileContainer_gzau3_53',
            '.viewerBadge_container__r5tak',
            '#MainMenu',
            'footer',
            'header'
        ];
        selectors.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.remove();
            });
        });
    }

    // Sofort ausführen
    removeStreamlitUI();

    // Auch nach DOM-Änderungen (Streamlit rendert asynchron nach)
    var observer = new MutationObserver(function() {
        removeStreamlitUI();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)


# =============================================================================
# --- 1. DASHBOARD ---
# =============================================================================
if st.session_state.view == 'start':
    st.markdown('<p class="main-header">Schulplaner</p>', unsafe_allow_html=True)
    if os.path.exists("startbild.jpg"):
        st.image("startbild.jpg")

    # --- Klausur-Frühwarnung: Banner wenn Klausur in ≤ 2 Tagen ---
    try:
        from datetime import timedelta
        res_warn = supabase.table("klausuren").select("*").execute()
        heute = date.today()
        bald = []
        for k in res_warn.data:
            try:
                k_date = date.fromisoformat(k["start_date"])
                delta = (k_date - heute).days
                if 0 <= delta <= 2:
                    bald.append((delta, k))
            except Exception:
                pass
        if bald:
            bald.sort(key=lambda x: x[0])
            for delta, k in bald:
                titel = k["titel"].replace("\n", " · ")
                if delta == 0:
                    wann = "⚡ **heute!**"
                elif delta == 1:
                    wann = "⏰ **morgen**"
                else:
                    wann = "📅 **übermorgen**"
                st.warning(f"🔔 Klausur {wann}: **{titel}**")
    except Exception:
        pass

    st.write("")
    # 2x2 Button-Grid: vollständig via HTML/CSS – Streamlit-Spalten wrappen auf Smartphone
    # Buttons lösen session_state-Wechsel via query_params-Trick nicht aus,
    # daher: reines HTML mit st.markdown + separate unsichtbare st.buttons als Trigger
    if 'nav' not in st.session_state:
        st.session_state.nav = None

    st.markdown("""
    <style>
    .menu-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        width: 100%;
        margin: 0 0 12px 0;
    }
    .menu-btn {
        background-color: #FF4B4B;
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 16px 8px;
        font-size: 0.95rem;
        font-weight: 700;
        width: 100%;
        cursor: pointer;
        text-align: center;
        line-height: 1.3;
    }
    .menu-btn:active { background-color: #c0392b; }
    /* Streamlit-Spalten niemals umbrechen */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }
    /* native Streamlit-Buttons verkleinern */
    [data-testid="stHorizontalBlock"] button {
        font-size: 0.78rem !important;
        padding: 0.4rem 0.2rem !important;
        white-space: normal !important;
        line-height: 1.2 !important;
        min-height: 56px !important;
    }
    /* Streamlit-UI-Elemente ausblenden */
    #MainMenu                                { display: none !important; }
    footer                                   { display: none !important; }
    header                                   { display: none !important; }
    [data-testid="stDeployButton"]           { display: none !important; }
    [data-testid="stToolbar"]                { display: none !important; }
    [data-testid="stDecoration"]             { display: none !important; }
    [data-testid="stMainMenuPopover"]        { display: none !important; }
    .viewerBadge_container__r5tak           { display: none !important; }
    .viewerBadge_link__qRIco                { display: none !important; }
    /* "Manage App"-Badge unten rechts */
    [data-testid="manage-app-button"]        { display: none !important; }
    ._profileContainer_gzau3_53             { display: none !important; }
    ._container_gzau3_1                     { display: none !important; }
    /* Toolbar-Buttons oben rechts (Share, Favorit, Stift, GitHub) */
    [data-testid="stActionButton"]           { display: none !important; }
    [data-testid="baseButton-headerNoPadding"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    r1a, r1b = st.columns(2)
    with r1a:
        if st.button("📅 KLAUSUREN", use_container_width=True, type="primary", key="btn_kl"):
            st.session_state.view = 'klausuren'; st.rerun()
    with r1b:
        if st.button("🏫 STUNDENPLÄNE", use_container_width=True, type="primary", key="btn_sp"):
            st.session_state.view = 'stundenplan'; st.rerun()
    r2a, r2b = st.columns(2)
    with r2a:
        if st.button("🚌 BUS-CHECK", use_container_width=True, type="primary", key="btn_bc"):
            st.session_state.view = 'bus'; st.rerun()
    with r2b:
        if st.button("🌴 FERIEN", use_container_width=True, type="primary", key="btn_fe"):
            st.session_state.view = 'ferien'; st.rerun()

    # Abstandspuffer damit "Manage App"-Badge die Buttons nicht überlagert
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)


# =============================================================================
# --- 2. KLAUSUREN ---
# =============================================================================
elif st.session_state.view == 'klausuren':
    try:
        res = supabase.table("klausuren").select("*").execute()
        k_data, k_df = res.data, pd.DataFrame(res.data)
    except:
        k_data, k_df = [], pd.DataFrame()

    with st.sidebar:
        st.header("Klausuren")
        if st.button("← Hauptmenü"):
            st.session_state.view = 'start'; st.rerun()
        with st.form("sb_form", clear_on_submit=True):
            sc = st.selectbox("Kind", list(CHILD_COLORS.keys()))
            ss = st.selectbox("Fach", SUBJECTS)
            sd = st.date_input("Datum", date.today(), format="DD.MM.YYYY")
            sn = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                supabase.table("klausuren").insert({
                    "datum": sd.strftime('%d.%m.%Y'), "titel": f"{sc}\n{ss}",
                    "start_date": str(sd), "color": CHILD_COLORS[sc], "child": sc, "note": sn
                }).execute()
                st.session_state.cal_key = str(uuid.uuid4()); st.rerun()

    zart_gruen = "#C8E6C9"
    holidays = [
        {"title": "Osterferien", "start": "2025-04-11", "end": "2025-04-26", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien", "start": "2025-07-28", "end": "2025-09-06", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Herbstferien", "start": "2025-10-20", "end": "2025-10-31", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Weihnachtsferien", "start": "2025-12-19", "end": "2026-01-06", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Osterferien '26", "start": "2026-03-26", "end": "2026-04-11", "backgroundColor": zart_gruen, "display": "background"},
        {"title": "Sommerferien '26", "start": "2026-07-13", "end": "2026-08-22", "backgroundColor": zart_gruen, "display": "background"},
    ]

    cal_ev = [{"id": str(d["id"]), "title": d["titel"], "start": d["start_date"],
               "backgroundColor": d["color"], "allDay": True, "textColor": "white"} for d in k_data]

    state = calendar(
        events=cal_ev + holidays,
        options={
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listMonth"},
            "buttonText": {"today": "Heute", "month": "Monat", "list": "Liste"},
            "initialView": "dayGridMonth", "locale": "de", "firstDay": 1,
            "weekends": False, "height": "auto", "selectable": True,
            "timeZone": "UTC", "displayEventTime": False
        },
        key=st.session_state.cal_key
    )

    if state.get("dateClick"):
        nd = state["dateClick"]["date"][:10]
        if st.session_state.selected_date != nd:
            st.session_state.selected_date = nd; st.session_state.edit_id = None; st.rerun()
    if state.get("eventClick"):
        ni = state["eventClick"]["event"].get("id")
        if st.session_state.edit_id != ni:
            st.session_state.edit_id = ni; st.session_state.selected_date = None; st.rerun()

    if st.session_state.selected_date:
        st.divider()
        st.write(f"**Neu am {datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y')}**")
        with st.form("q_f", clear_on_submit=True):
            qc = st.selectbox("Kind", list(CHILD_COLORS.keys()))
            qs = st.selectbox("Fach", SUBJECTS)
            qn = st.text_input("Notiz")
            if st.form_submit_button("💾 Speichern", use_container_width=True):
                supabase.table("klausuren").insert({
                    "datum": datetime.strptime(st.session_state.selected_date, '%Y-%m-%d').strftime('%d.%m.%Y'),
                    "titel": f"{qc}\n{qs}", "start_date": st.session_state.selected_date,
                    "color": CHILD_COLORS[qc], "child": qc, "note": qn
                }).execute()
                st.session_state.selected_date = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
        if st.button("✕ Abbrechen", use_container_width=True, key="btn_cancel_new"):
            st.session_state.selected_date = None; st.rerun()

    if st.session_state.edit_id and st.session_state.edit_id != "undefined":
        st.divider()
        try:
            edit_row = k_df[k_df['id'].astype(str) == str(st.session_state.edit_id)].iloc[0]
            with st.form("ed_f"):
                st.write("**Bearbeiten**")
                new_c = st.selectbox("Kind", list(CHILD_COLORS.keys()),
                                     index=list(CHILD_COLORS.keys()).index(edit_row['child']))
                curr_s = edit_row['titel'].split('\n')[-1]
                new_s = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(curr_s) if curr_s in SUBJECTS else 0)
                new_d = st.date_input("Datum", datetime.strptime(edit_row['start_date'], '%Y-%m-%d'), format="DD.MM.YYYY")
                new_n = st.text_input("Notiz", value=edit_row['note'])
                c1, c2, c3 = st.columns([2, 2, 1])
                if c1.form_submit_button("💾 Speichern"):
                    supabase.table("klausuren").update({
                        "datum": new_d.strftime('%d.%m.%Y'), "titel": f"{new_c}\n{new_s}",
                        "start_date": str(new_d), "color": CHILD_COLORS[new_c], "child": new_c, "note": new_n
                    }).eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c2.form_submit_button("🗑️ Löschen"):
                    supabase.table("klausuren").delete().eq("id", st.session_state.edit_id).execute()
                    st.session_state.edit_id = None; st.session_state.cal_key = str(uuid.uuid4()); st.rerun()
                if c3.form_submit_button("X"):
                    st.session_state.edit_id = None; st.rerun()
        except:
            st.session_state.edit_id = None

    st.divider()
    if not k_df.empty:
        df_t = k_df.copy()
        df_t['Anzeige'] = df_t['titel'].str.replace('\n', ': ')
        df_t['start_date_dt'] = pd.to_datetime(df_t['start_date']).dt.date
        df_t = df_t[df_t['start_date_dt'] >= date.today()]
        if not df_t.empty:
            st.dataframe(
                df_t.sort_values(by='start_date')[['datum', 'Anzeige']].rename(columns={'datum': 'Wann', 'Anzeige': 'Wer & Was'}),
                hide_index=True, use_container_width=True
            )
        else:
            st.info("Keine bevorstehenden Klausuren.")
    else:
        st.info("Keine Einträge vorhanden.")

    if st.button("← Hauptmenü", use_container_width=True):
        st.session_state.view = 'start'; st.rerun()


# =============================================================================
# --- 3. STUNDENPLÄNE ---
# =============================================================================
elif st.session_state.view == 'stundenplan':
    st.markdown('<p class="main-header">Stundenpläne</p>', unsafe_allow_html=True)

    c_cols = st.columns(3)
    for i, name in enumerate(CHILD_COLORS.keys()):
        btn_type = "primary" if st.session_state.stundenplan_child == name else "secondary"
        if c_cols[i].button(name, key=f"child_sel_{name}", use_container_width=True, type=btn_type):
            st.session_state.stundenplan_child = name; st.session_state.editing_grade = False; st.rerun()

    cur_c = st.session_state.stundenplan_child

    try:
        k_info = supabase.table("kinder_info").select("klasse").eq("child", cur_c).execute().data
        cur_klasse = k_info[0]['klasse'] if k_info else "Klasse ?"
    except:
        cur_klasse = "Klasse ?"

    if not st.session_state.editing_grade:
        if st.button(f"✏️ {cur_klasse}", use_container_width=True):
            st.session_state.editing_grade = True; st.rerun()
    else:
        with st.form("grade_form"):
            new_g = st.text_input("Klasse anpassen:", value=cur_klasse)
            if st.form_submit_button("Speichern"):
                supabase.table("kinder_info").upsert({"child": cur_c, "klasse": new_g}).execute()
                st.session_state.editing_grade = False; st.rerun()

    res = supabase.table("stundenplaene").select("*").eq("child", cur_c).execute()
    plan_dict = {(item['tag'], int(item['stunde'])): item for item in res.data}

    for day in DAYS:
        with st.expander(f"**{day}**", expanded=False):
            for std in range(1, 8):
                lesson = plan_dict.get((day, std))
                fach = lesson['fach'] if lesson else "---"
                col_t, col_f = st.columns([1, 4])
                col_t.markdown(f"<small>{std}. Std<br>{TIMES[std]}</small>", unsafe_allow_html=True)
                if col_f.button(f"{fach}", key=f"p_sc_{cur_c}_{day}_{std}", use_container_width=True):
                    st.session_state.edit_cell = {"day": day, "std": std, "fach": fach, "id": lesson['id'] if lesson else None}

    if 'edit_cell' in st.session_state:
        ec = st.session_state.edit_cell
        st.divider()
        with st.form("ed_p"):
            st.write(f"📌 **{ec['day']}, {ec['std']}. Stunde**")
            new_f = st.selectbox("Fach", SUBJECTS, index=SUBJECTS.index(ec['fach']) if ec['fach'] in SUBJECTS else 0)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Speichern"):
                if ec['id']:
                    supabase.table("stundenplaene").update({"fach": new_f}).eq("id", ec['id']).execute()
                else:
                    supabase.table("stundenplaene").insert({"child": cur_c, "tag": ec['day'], "stunde": ec['std'], "fach": new_f}).execute()
                del st.session_state.edit_cell; st.rerun()
            if c2.form_submit_button("Abbrechen"):
                del st.session_state.edit_cell; st.rerun()

    if st.button("← Hauptmenü", use_container_width=True):
        st.session_state.view = 'start'; st.rerun()


# =============================================================================
# --- 4. BUS-CHECK (Echtzeit-Fenster 120 Min., Haltestelle zuerst wählen) ---
# =============================================================================
elif st.session_state.view == 'bus':
    st.markdown('<p class="main-header">Bus-Check</p>', unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # FAHRPLANDATEN  –  Quelle: VKP Fahrplan 2025, Mo–Fr
    #
    # Format: (Abfahrtszeit, Linie, Ausstieg/Endpunkt, Hinweis)
    #
    # SEEFISCHMARKT → Richtung Schönkirchen / Schönberg
    #   200/201 Ausstieg: Linas Diek
    #   210     Ausstieg: Amboßweg
    #
    # LINAS DIEK  → Kiel  (Linie 200/201, Ausstieg Seefischmarkt)
    # AMBOßWEG    → Kiel  (Linie 210, Ausstieg Seefischmarkt)
    # -----------------------------------------------------------------------

    # (abfahrt, linie, ausstieg, hinweis)
    SEEFISCHMARKT = [
        ("06:37", "200", "Linas Diek",  ""),
        ("06:52", "200", "Linas Diek",  ""),
        ("07:05", "201", "Linas Diek",  "direkt, schneller"),
        ("07:07", "200", "Linas Diek",  ""),
        ("07:20", "201", "Linas Diek",  "direkt, schneller"),
        ("07:22", "200", "Linas Diek",  ""),
        ("07:37", "200", "Linas Diek",  ""),
        ("07:52", "200", "Linas Diek",  ""),
        ("08:05", "201", "Linas Diek",  "direkt, schneller"),
        ("08:07", "200", "Linas Diek",  ""),
        ("08:20", "201", "Linas Diek",  "direkt, schneller"),
        ("08:22", "200", "Linas Diek",  ""),
        ("08:37", "200", "Linas Diek",  ""),
        ("08:52", "200", "Linas Diek",  ""),
        ("09:05", "201", "Linas Diek",  "direkt, schneller"),
        ("09:22", "200", "Linas Diek",  ""),
        ("09:52", "200", "Linas Diek",  ""),
        ("10:05", "201", "Linas Diek",  "direkt, schneller"),
        ("10:22", "200", "Linas Diek",  ""),
        ("10:52", "200", "Linas Diek",  ""),
        ("11:05", "201", "Linas Diek",  "direkt, schneller"),
        ("11:22", "200", "Linas Diek",  ""),
        ("11:37", "210", "Amboßweg",    ""),
        ("11:52", "200", "Linas Diek",  ""),
        ("12:05", "201", "Linas Diek",  "direkt, schneller"),
        ("12:22", "200", "Linas Diek",  ""),
        ("12:37", "210", "Amboßweg",    ""),
        ("12:52", "200", "Linas Diek",  ""),
        ("13:05", "201", "Linas Diek",  "direkt, schneller"),
        ("13:22", "200", "Linas Diek",  ""),
        ("13:37", "210", "Amboßweg",    ""),
        ("13:52", "200", "Linas Diek",  ""),
        ("14:05", "201", "Linas Diek",  "direkt, schneller"),
        ("14:08", "200", "Linas Diek",  ""),
        ("14:22", "200", "Linas Diek",  ""),
        ("14:37", "210", "Amboßweg",    ""),
        ("14:52", "200", "Linas Diek",  ""),
        ("15:05", "201", "Linas Diek",  "direkt, schneller"),
        ("15:07", "200", "Linas Diek",  ""),
        ("15:22", "200", "Linas Diek",  ""),
        ("15:37", "210", "Amboßweg",    ""),
        ("15:52", "200", "Linas Diek",  ""),
        ("16:00", "200", "Linas Diek",  ""),
    ]

    # Quelle: VKP PDF 200i.pdf, Rückfahrten Mo–Fr, Seiten 7–9
    # Spalte "Schönkirchen, Lina's Diek", direkt abgelesen, Stand 21.11.2024
    # Linie 201 = Fahrt-Nr 201xx (direkte Route ohne Söhren, ~4 Min bis Seefischmarkt)
    # Linie 200 = Fahrt-Nr 200xx (via Söhren/Steinbergskamp, ~7 Min bis Seefischmarkt)
    # [E] = nur an Schultagen  [30] = 30er-Route (umgekehrte Haltefolge)
    LINAS_DIEK = [
        ("05:18", "200", "Seefischmarkt", ""),   # 20001 [30], via Söhren
        ("05:31", "201", "Seefischmarkt", ""),   # 20103, direkt
        ("06:15", "201", "Seefischmarkt", ""),   # 20105, direkt
        ("06:38", "200", "Seefischmarkt", ""),   # 20003 [30], via Söhren
        ("06:45", "201", "Seefischmarkt", ""),   # 20107, direkt
        ("07:30", "201", "Seefischmarkt", ""),   # 20109 [E], direkt
        ("07:33", "200", "Seefischmarkt", ""),   # 20011 [E], via Söhren
        ("08:09", "201", "Seefischmarkt", ""),   # 20113, direkt
        ("08:15", "201", "Seefischmarkt", ""),   # 20111, direkt
        ("09:30", "201", "Seefischmarkt", ""),   # 20115, direkt
        ("09:43", "200", "Seefischmarkt", ""),   # 20015, via Steinbergskamp
        ("10:30", "201", "Seefischmarkt", ""),   # 20117, direkt
        ("10:43", "200", "Seefischmarkt", ""),   # 20017, via Steinbergskamp
        ("11:30", "201", "Seefischmarkt", ""),   # 20121, direkt
        ("11:43", "200", "Seefischmarkt", ""),   # 20019, via Steinbergskamp
        ("12:30", "201", "Seefischmarkt", ""),   # 20123, direkt
        ("12:43", "200", "Seefischmarkt", ""),   # 20023, via Steinbergskamp
        ("13:30", "201", "Seefischmarkt", ""),   # 20125, direkt
        ("13:43", "200", "Seefischmarkt", ""),   # 20025 [E], via Steinbergskamp
        ("14:30", "201", "Seefischmarkt", ""),   # 20127, direkt
        ("14:38", "200", "Seefischmarkt", ""),   # 20029, via Söhren
        ("15:30", "201", "Seefischmarkt", ""),   # 20129, direkt
        ("15:43", "200", "Seefischmarkt", ""),   # 20035, via Steinbergskamp
        ("16:10", "201", "Seefischmarkt", ""),   # 20131, direkt
        ("16:30", "201", "Seefischmarkt", ""),   # 20133, direkt
        ("16:43", "200", "Seefischmarkt", ""),   # 20043, via Söhren
        ("17:10", "201", "Seefischmarkt", ""),   # 20135 [E], direkt
        ("17:30", "201", "Seefischmarkt", ""),   # 20137, direkt
        ("17:38", "200", "Seefischmarkt", ""),   # 20051, via Söhren
        ("18:30", "201", "Seefischmarkt", ""),   # 20141, direkt
    ]

    # Quelle: VKP PDF 210i.pdf, Spalte "Schönkirchen, Amboßweg", Richtung Kiel, Mo–Fr
    AMBOSSWEG = [
        ("06:07", "210", "Seefischmarkt", ""),
        ("07:07", "210", "Seefischmarkt", ""),
        ("08:17", "210", "Seefischmarkt", ""),
        ("12:22", "210", "Seefischmarkt", ""),
        ("14:22", "210", "Seefischmarkt", ""),
    ]

    # -----------------------------------------------------------------------
    # DARSTELLUNG
    # -----------------------------------------------------------------------

    LINE_COLORS  = {"200": "#C62828", "201": "#1565C0", "210": "#2E7D32"}
    LINE_BGLIGHT = {"200": "#FFEBEE", "201": "#E3F2FD", "210": "#E8F5E9"}

    def bus_card(zeit_str, linie, ausstieg, hinweis, diff_min, ist_naechste):
        farbe = LINE_COLORS.get(linie, "#555")
        bg    = LINE_BGLIGHT.get(linie, "#fafafa") if ist_naechste else "white"
        rand  = f"2px solid {farbe}" if ist_naechste else "1px solid #e8e8e8"

        badge    = f'<span style="background:{farbe};color:white;font-size:0.7rem;padding:2px 8px;border-radius:10px;margin-left:8px;">▶ Nächste</span>' if ist_naechste else ""
        if diff_min == 0:
            cd = f'<span style="color:{farbe};font-weight:bold;font-size:0.85rem;">jetzt!</span>'
        elif 0 < diff_min <= 120:
            cd = f'<span style="color:{farbe};font-size:0.85rem;">in <b>{diff_min} Min.</b></span>'
        else:
            cd = ""
        hw = f'<div style="font-size:0.75rem;color:#999;margin-top:2px;">ℹ️ {hinweis}</div>' if hinweis else ""

        html = (
            f'<div style="background:{bg};border:{rand};border-left:6px solid {farbe};border-radius:10px;padding:11px 14px 9px 14px;margin-bottom:9px;box-shadow:1px 2px 5px rgba(0,0,0,0.06);">' +
            f'<div style="display:flex;align-items:center;justify-content:space-between;">' +
            f'<div><span style="font-size:1.4rem;font-weight:900;color:{farbe};">{zeit_str}</span>' +
            f'<span style="font-size:0.9rem;font-weight:700;background:{farbe};color:white;padding:2px 8px;border-radius:6px;margin-left:8px;">Linie {linie}</span>' +
            f'{badge}</div><div>{cd}</div></div>' +
            f'<div style="margin-top:5px;font-size:0.9rem;color:#444;">🚏 Ausstieg: <b>{ausstieg}</b></div>' +
            f'{hw}</div>'
        )
        st.markdown(html, unsafe_allow_html=True)

    def zeige_naechste_120min(fahrplan, haltestellenname, richtung):
        from datetime import timedelta
        now    = datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).replace(tzinfo=None)
        cutoff = now.replace(second=0, microsecond=0)

        # Wochentag-Namen für Ausgaben
        WT = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

        # Nächsten Werktag berechnen
        def naechster_werktag(von):
            tage = 3 if von.weekday() == 4 else (2 if von.weekday() == 5 else 1)
            t = von + timedelta(days=tage)
            return t

        if now.weekday() >= 5:
            nwt = naechster_werktag(now)
            st.warning(
                f"⚠️ Dieser Fahrplan gilt nur Montag–Freitag. "
                f"Nächste Fahrten ab **{WT[nwt.weekday()]}, {nwt.strftime('%d.%m.')}**."
            )

        # Fahrplan nach Zeit sortieren, damit Reihenfolge garantiert stimmt
        fahrplan_sorted = sorted(fahrplan, key=lambda x: x[0])

        treffer = []
        for zeit_str, linie, ausstieg, hinweis in fahrplan_sorted:
            h, m    = map(int, zeit_str.split(":"))
            abfahrt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff    = int((abfahrt - cutoff).total_seconds() / 60)
            if 0 <= diff <= 120:
                treffer.append((zeit_str, linie, ausstieg, hinweis, diff))

        st.caption(
            f"📍 **{haltestellenname}** ➔ {richtung} &nbsp;|&nbsp; "
            f"nächste 120 Min. ab {now.strftime('%H:%M')} Uhr &nbsp;|&nbsp; Mo–Fr &nbsp;|&nbsp; Quelle: VKP 2025"
        )

        if not treffer:
            # Suche: noch heute später?
            naechste_heute = None
            for zeit_str, linie, ausstieg, hinweis in fahrplan_sorted:
                h, m    = map(int, zeit_str.split(":"))
                abfahrt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                diff    = int((abfahrt - cutoff).total_seconds() / 60)
                if diff > 120:
                    naechste_heute = (zeit_str, linie, ausstieg, hinweis)
                    break

            if naechste_heute:
                z, li, au, hi = naechste_heute
                hinweis_txt = f" · _{hi}_" if hi else ""
                st.info(
                    f"Keine Abfahrten in den nächsten 120 Minuten.\n\n"
                    f"🕐 **Nächste Abfahrt heute:** {z} Uhr · Linie {li} · Ausstieg {au}{hinweis_txt}"
                )
            else:
                # Kein Bus mehr heute → erste Fahrt nächsten Werktag
                nwt = naechster_werktag(now)
                ez, el, ea, eh = fahrplan[0]
                hinweis_txt = f" · _{eh}_" if eh else ""
                st.info(
                    f"Heute keine weiteren Abfahrten mehr.\n\n"
                    f"🕐 **Erste Fahrt {WT[nwt.weekday()]}, {nwt.strftime('%d.%m.')}:** "
                    f"{ez} Uhr · Linie {el} · Ausstieg {ea}{hinweis_txt}"
                )
            return

        for i, (zeit_str, linie, ausstieg, hinweis, diff_min) in enumerate(treffer):
            ist_naechste = (i == 0)
            bus_card(zeit_str, linie, ausstieg, hinweis, diff_min, ist_naechste)

    # -----------------------------------------------------------------------
    # HALTESTELLE WÄHLEN
    # -----------------------------------------------------------------------
    if 'bus_halt' not in st.session_state:
        st.session_state.bus_halt = None

    # Haltestellen-Buttons: gleiche Höhe via CSS, Zeilenumbruch via HTML
    btn_labels = {
        "seefisch": ("🏠", "Seefischmarkt", "→ Schönkirchen"),
        "linas":    ("🏫", "Linas Diek",    "→ Seefischmarkt"),
        "amboss":   ("🏫", "Amboßweg",      "→ Seefischmarkt"),
    }
    c1, c2, c3 = st.columns(3)
    for col, key in zip([c1, c2, c3], ["seefisch", "linas", "amboss"]):
        icon, zeile1, zeile2 = btn_labels[key]
        aktiv = st.session_state.bus_halt == key
        with col:
            if st.button(
                f"{icon} {zeile1} {zeile2}",
                key=f"bus_btn_{key}",
                use_container_width=True,
                type="primary" if aktiv else "secondary"
            ):
                st.session_state.bus_halt = key; st.rerun()

    st.divider()

    if st.session_state.bus_halt == "seefisch":
        zeige_naechste_120min(SEEFISCHMARKT, "Seefischmarkt", "Richtung Schönkirchen / Schönberg")
    elif st.session_state.bus_halt == "linas":
        zeige_naechste_120min(LINAS_DIEK, "Linas Diek", "Richtung Kiel")
    elif st.session_state.bus_halt == "amboss":
        zeige_naechste_120min(AMBOSSWEG, "Amboßweg", "Richtung Kiel")
    else:
        st.markdown(
            "<div style='text-align:center;color:#aaa;padding:30px 0;font-size:1rem;'>"
            "⬆️ Bitte Haltestelle auswählen</div>",
            unsafe_allow_html=True
        )

    if st.button("← Hauptmenü", use_container_width=True):
        st.session_state.bus_halt = None
        st.session_state.view = 'start'; st.rerun()


# =============================================================================
# --- 5. FERIEN ---
# =============================================================================
elif st.session_state.view == 'ferien':
    st.markdown('<p class="main-header">Ferien S-H</p>', unsafe_allow_html=True)
    jahr = st.radio("Jahr:", [2026, 2027], horizontal=True)
    st.dataframe(pd.DataFrame(FERIEN_DATA[jahr]), hide_index=True, use_container_width=True)
    st.caption("Alle Angaben ohne Gewähr")
    if st.button("← Hauptmenü", use_container_width=True):
        st.session_state.view = 'start'; st.rerun()