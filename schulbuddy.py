import streamlit as st
from anthropic import Anthropic

# ── Fächer-Konfiguration ──────────────────────────────────────────────────────
FAECHER = {
    "Mathematik":   {"icon": "🧮", "color": "#a87df8",
        "topics": ["Bruchrechnung", "Gleichungen", "Funktionen", "Geometrie",
                   "Pythagoras", "Wahrscheinlichkeit", "Trigonometrie",
                   "Differentialrechnung", "Integralrechnung", "Vektorrechnung",
                   "Stochastik", "Analytische Geometrie"],
        "prompt": (
            "Du bist ein cooler Mathe-Assistent fuer Gymnasiasten (Level: {level}). "
            "Frech und jugendlich, aber paedagogisch: zeige NIE einfach die Loesung, "
            "sondern erklaere den Denkweg Schritt fuer Schritt. Stelle Rueckfragen, "
            "gib Tipps. Passe Erklaerungen ans Level an. "
            "Nutze LaTeX-Notation fuer Formeln wo sinnvoll. Antworte auf Deutsch."
        )
    },
    "Deutsch":      {"icon": "📖", "color": "#f25ca2",
        "topics": ["Erörterung", "Sachtextanalyse", "Gedichtanalyse",
                   "Dramenanalyse", "Grammatik", "Rechtschreibung",
                   "Kreatives Schreiben", "Präsentation", "Sprachgeschichte"],
        "prompt": (
            "Du bist ein hilfreicher Deutsch-Assistent fuer Gymnasiasten (Level: {level}). "
            "Motivierend und paedagogisch. Schreibe keine fertigen Aufsaetze oder Analysen, "
            "sondern erklaere Aufbau, Argumentation und Stilmittel. "
            "Gib konkrete Hinweise und Beispiele. Antworte auf Deutsch."
        )
    },
    "Englisch":     {"icon": "🇬🇧", "color": "#38d9f5",
        "topics": ["Grammatik", "Vokabeln", "Essay schreiben", "Reading Comprehension",
                   "Literaturanalyse", "Mediation", "Bewerbungsschreiben", "Speaking"],
        "prompt": (
            "Du bist ein cooler Englisch-Tutor fuer deutsche Gymnasiasten (Level: {level}). "
            "Freundlich und paedagogisch. Schreibe keine fertigen Texte oder Uebersetzungen, "
            "sondern erklaere Struktur und Grammatik. Mische Deutsch und Englisch je nach Bedarf. "
            "Passe dich ans Niveau an."
        )
    },
    "Französisch":  {"icon": "🇫🇷", "color": "#ffe566",
        "topics": ["Vokabeln", "Grammatik", "Konjugation", "Texte schreiben",
                   "Hörverstehen", "Literatur", "DELF-Vorbereitung"],
        "prompt": (
            "Du bist ein motivierender Franzoesisch-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere Grammatikregeln mit Beispielen, hilf beim Vokabellernen mit Eselsbruecken. "
            "Schreibe keine fertigen Texte. Nutze gelegentlich franzoesische Phrasen mit Erklaerung. "
            "Antworte auf Deutsch."
        )
    },
    "Spanisch":     {"icon": "🇪🇸", "color": "#ff9a5c",
        "topics": ["Vokabeln", "Grammatik", "Konjugation", "Texte schreiben",
                   "Hörverstehen", "Literatur", "DELE-Vorbereitung"],
        "prompt": (
            "Du bist ein motivierender Spanisch-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere Grammatikregeln mit Beispielen, hilf beim Vokabellernen mit Eselsbruecken. "
            "Schreibe keine fertigen Texte. Nutze gelegentlich spanische Phrasen mit deutscher Erklaerung. "
            "Antworte auf Deutsch."
        )
    },
    "Physik":       {"icon": "⚡", "color": "#42e8a0",
        "topics": ["Mechanik", "Optik", "Thermodynamik", "Elektrizitätslehre",
                   "Magnetismus", "Atomphysik", "Quantenphysik",
                   "Schwingungen & Wellen", "Relativitätstheorie"],
        "prompt": (
            "Du bist ein begeisterter Physik-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere Konzepte mit Alltagsbeispielen. Zeige keine fertigen Loesungen, "
            "sondern erklaere den Loesungsansatz. Nutze Formeln korrekt. "
            "Antworte auf Deutsch."
        )
    },
    "Chemie":       {"icon": "⚗️", "color": "#ff6b6b",
        "topics": ["Atombau", "Bindungslehre", "Säuren & Basen", "Redoxreaktionen",
                   "Organische Chemie", "Stöchiometrie", "Elektrochemie"],
        "prompt": (
            "Du bist ein cooler Chemie-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere chemische Konzepte anschaulich mit Alltagsbeispielen. "
            "Keine fertigen Loesungen - erklaere den Denkprozess. "
            "Nutze chemische Formeln korrekt. Antworte auf Deutsch."
        )
    },
    "Biologie":     {"icon": "🌿", "color": "#7ecb8f",
        "topics": ["Zellbiologie", "Genetik", "Evolution", "Ökologie",
                   "Stoffwechsel", "Neurobiologie", "Immunsystem", "Botanik"],
        "prompt": (
            "Du bist ein neugieriger Biologie-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere biologische Prozesse bildhaft und spannend. "
            "Keine fertigen Loesungen, sondern Erklaerungen und Tipps. "
            "Passe Komplexitaet ans Level an. Antworte auf Deutsch."
        )
    },
    "Geographie":   {"icon": "🌍", "color": "#5cb8ff",
        "topics": ["Kartenkunde", "Klimazonen", "Bevölkerungsgeographie",
                   "Wirtschaftsgeographie", "Globalisierung",
                   "Nachhaltigkeit", "Meteorologie"],
        "prompt": (
            "Du bist ein weltgewandter Geographie-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere geographische Zusammenhaenge anschaulich. "
            "Hilf beim Verstehen von Karten und Klimadaten. Keine fertigen Aufsaetze. "
            "Antworte auf Deutsch."
        )
    },
    "Geschichte":   {"icon": "📜", "color": "#c9a84c",
        "topics": ["Antike", "Mittelalter", "Frühe Neuzeit", "Industrialisierung",
                   "Erster Weltkrieg", "NS-Zeit", "Zweiter Weltkrieg",
                   "Kalter Krieg", "Quellenanalyse"],
        "prompt": (
            "Du bist ein spannender Geschichte-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere historische Zusammenhaenge lebendig. Hilf bei Quellenanalyse durch Erklaerung "
            "des Vorgehens, nicht durch fertige Texte. Antworte auf Deutsch."
        )
    },
    "Informatik":   {"icon": "💻", "color": "#a0e4ff",
        "topics": ["Programmierung", "Algorithmen", "Datenstrukturen",
                   "Datenbanken", "Netzwerke", "Kryptographie",
                   "Künstliche Intelligenz", "Web-Entwicklung"],
        "prompt": (
            "Du bist ein smarter Informatik-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere Algorithmen und Konzepte klar. Bei Programmieraufgaben: gib Hinweise "
            "und erklaere den Loesungsansatz, schreibe nicht einfach fertigen Code. "
            "Nutze Code-Beispiele zur Erklaerung. Antworte auf Deutsch."
        )
    },
    "Musik":        {"icon": "🎵", "color": "#f8a4d8",
        "topics": ["Musiktheorie", "Notenlernen", "Harmonielehre",
                   "Epochen & Stile", "Komposition", "Analyse", "Instrumente"],
        "prompt": (
            "Du bist ein kreativer Musik-Assistent fuer Gymnasiasten (Level: {level}). "
            "Erklaere Musiktheorie verstaendlich. Hilf beim Notenlernen und Analysieren. "
            "Motivierend und kreativ. Antworte auf Deutsch."
        )
    },
}

LEVELS = {
    "Unterstufe (Kl. 5–7)":   "Unterstufe Klasse 5-7",
    "Mittelstufe (Kl. 8–9)":  "Mittelstufe Klasse 8-9",
    "Oberstufe (Kl. 10–11)":  "Oberstufe Klasse 10-11",
    "Abitur (Kl. 12–13)":     "Abitur Klasse 12-13",
}

# ── Session-State initialisieren ──────────────────────────────────────────────
def init_state():
    if "sb_fach"    not in st.session_state: st.session_state.sb_fach    = None
    if "sb_level"   not in st.session_state: st.session_state.sb_level   = None
    if "sb_history" not in st.session_state: st.session_state.sb_history = []

# ── Seite rendern ─────────────────────────────────────────────────────────────
def show():
    init_state()

    # API-Key aus Streamlit Secrets
    try:
        client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        st.error("⚠️ Kein API-Key gefunden. Bitte ANTHROPIC_API_KEY in den Streamlit Secrets hinterlegen.")
        st.stop()

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .hh-title { font-size: 1.4rem; font-weight: 900; margin-bottom: 4px; }
    .hh-sub   { font-size: 0.82rem; color: #888; margin-bottom: 18px; }
    .fach-chip {
        display: inline-block;
        padding: 6px 14px; margin: 4px;
        border-radius: 20px; font-size: 0.8rem; font-weight: 700;
        cursor: pointer; border: 2px solid;
        transition: all .2s;
    }
    .topic-pill {
        display: inline-block;
        padding: 4px 12px; margin: 3px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
        background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15);
        cursor: pointer;
    }
    .chat-user { background: #1F3864; color: white; border-radius: 12px 12px 4px 12px;
                 padding: 10px 14px; margin: 6px 0; font-size: 0.88rem; }
    .chat-bot  { background: #2a2a3e; color: #f0ecff; border-radius: 12px 12px 12px 4px;
                 padding: 10px 14px; margin: 6px 0; font-size: 0.88rem; line-height: 1.6; }
    .level-badge { font-size: 0.72rem; color: #aaa; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    # ── Schritt 1: Fach wählen ────────────────────────────────────────────────
    if st.session_state.sb_fach is None:
        st.markdown('<div class="hh-title">📚 SchulBuddy</div>', unsafe_allow_html=True)
        st.markdown('<div class="hh-sub">Welches Fach beschäftigt dich gerade?</div>', unsafe_allow_html=True)

        cols = st.columns(3)
        for i, (fach, info) in enumerate(FAECHER.items()):
            with cols[i % 3]:
                if st.button(
                    f"{info['icon']} {fach}",
                    key=f"fach_{fach}",
                    use_container_width=True
                ):
                    st.session_state.sb_fach    = fach
                    st.session_state.sb_level   = None
                    st.session_state.sb_history = []
                    st.rerun()
        return

    # ── Schritt 2: Level wählen ───────────────────────────────────────────────
    if st.session_state.sb_level is None:
        fach = st.session_state.sb_fach
        info = FAECHER[fach]
        st.markdown(f'<div class="hh-title">{info["icon"]} {fach}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hh-sub">Welche Klassenstufe bist du?</div>', unsafe_allow_html=True)

        cols = st.columns(2)
        for i, (label, val) in enumerate(LEVELS.items()):
            with cols[i % 2]:
                if st.button(label, key=f"level_{label}", use_container_width=True):
                    st.session_state.sb_level = val
                    st.rerun()

        if st.button("← Fach wechseln", key="sb_back_to_fach"):
            st.session_state.sb_fach = None
            st.rerun()
        return

    # ── Schritt 3: Chat ───────────────────────────────────────────────────────
    fach  = st.session_state.sb_fach
    level = st.session_state.sb_level
    info  = FAECHER[fach]

    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Fach", key="sb_back_chat"):
            st.session_state.sb_fach    = None
            st.session_state.sb_level   = None
            st.session_state.sb_history = []
            st.rerun()
    with col2:
        st.markdown(
            f'<div style="text-align:center;">'
            f'<span style="font-size:1.1rem;font-weight:900;color:{info["color"]}">'
            f'{info["icon"]} {fach}</span>'
            f'<span class="level-badge"> · {level}</span></div>',
            unsafe_allow_html=True
        )
    with col3:
        if st.button("🗑️ Reset", key="sb_reset_chat"):
            st.session_state.sb_history = []
            st.rerun()

    st.divider()

    # Themen-Chips
    st.markdown("**Themen-Schnellauswahl:**")
    topic_cols = st.columns(4)
    for i, topic in enumerate(info["topics"]):
        with topic_cols[i % 4]:
            if st.button(topic, key=f"topic_{topic}", use_container_width=True):
                frage = f"Kannst du mir {topic} erklären?"
                st.session_state.sb_history.append({"role": "user", "content": frage})
                system_prompt = info["prompt"].format(level=level)
                with st.spinner("Denke nach..."):
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system=system_prompt,
                        messages=st.session_state.sb_history
                    )
                answer = response.content[0].text
                st.session_state.sb_history.append({"role": "assistant", "content": answer})
                st.rerun()

    st.divider()

    # Begrüßung wenn History leer
    if not st.session_state.sb_history:
        begruessung = {
            "Mathematik":  "Hey! Bereit für Mathe? Was ist die aktuelle Herausforderung? 🧮",
            "Deutsch":     "Hi! Was steht auf dem Programm - Aufsatz, Analyse oder Grammatik? 📖",
            "Englisch":    "Hey! What's up? Woran arbeiten wir heute? 🇬🇧",
            "Französisch": "Salut! Was macht dir gerade am meisten zu schaffen? 🇫🇷",
            "Spanisch":    "Hola! Vokabeln, Grammatik oder Texte - womit starten wir? 🇪🇸",
            "Physik":      "Hey! Von Mechanik bis Quantenphysik - was soll ich erklären? ⚡",
            "Chemie":      "Hi! Welches chemische Rätsel lösen wir heute? ⚗️",
            "Biologie":    "Hey! Zellen, Gene, Evolution - womit kann ich helfen? 🌿",
            "Geographie":  "Hi! Von Klimazonen bis Globalisierung - was liegt an? 🌍",
            "Geschichte":  "Hey! Welches Kapitel der Geschichte beschäftigt dich? 📜",
            "Informatik":  "Hi! Code, Algorithmen, Konzepte - womit starten wir? 💻",
            "Musik":       "Hey! Theorie, Noten oder Analyse - was brauchst du? 🎵",
        }
        st.info(begruessung.get(fach, "Hey! Womit kann ich dir helfen?"))

    # Chat-Verlauf anzeigen
    for msg in st.session_state.sb_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])

    # Eingabe
    user_input = st.chat_input(f"Deine Frage zu {fach}...")
    if user_input:
        st.session_state.sb_history.append({"role": "user", "content": user_input})
        system_prompt = info["prompt"].format(level=level)
        with st.spinner(""):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                messages=st.session_state.sb_history
            )
        answer = response.content[0].text
        st.session_state.sb_history.append({"role": "assistant", "content": answer})
        st.rerun()
