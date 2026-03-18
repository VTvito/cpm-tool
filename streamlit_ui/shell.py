from __future__ import annotations

import sys
from pathlib import Path

# Garantisce che la root del progetto sia in sys.path su Streamlit Cloud,
# dove il working directory potrebbe non coincidere con la cartella del progetto.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from core.norms import is_using_placeholder


def configure_page(page_title: str, page_icon: str = "🧩") -> None:
    st.set_page_config(
        page_title=f"{page_title} · CPM",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="auto",
    )
    _inject_styles()
    _render_sidebar()


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        /* ─── Design tokens ─────────────────────────────────── */
        :root {
            --c-bg:          #f2f5f9;
            --c-surface:     #ffffff;
            --c-surface-alt: #eaeff5;
            --c-border:      #c8d5e0;
            --c-border-l:    #dce6ee;
            --c-ink:         #0e1d2a;
            --c-muted:       #2d4555;
            --c-primary:     #1a4f72;
            --c-primary-h:   #0e3451;
            --c-primary-l:   #2874a6;
            --c-accent:      #9d4106;
            --c-success:     #1a6b42;
            --c-danger:      #862015;
            --c-shadow:      0 2px 8px  rgba(14, 29, 42, 0.07);
            --c-shadow-md:   0 4px 18px rgba(14, 29, 42, 0.09);
            --c-shadow-lg:   0 8px 32px rgba(14, 29, 42, 0.12);
            --r-sm: 8px;
            --r:    12px;
            --r-lg: 18px;
        }

        /* ─── Base ───────────────────────────────────────────── */
        /* Nascondi header sticky Streamlit (copre i titoli) e barra colore */
        header[data-testid="stHeader"],
        div[data-testid="stDecoration"] {
            display: none !important;
        }

        .stApp {
            background: var(--c-bg);
            color: var(--c-ink);
            font-family: "Segoe UI", "Inter", system-ui, -apple-system, Arial, sans-serif;
        }

        .block-container {
            max-width: 1320px;
            padding-top: 1.8rem;
            padding-bottom: 2rem;
        }

        /* ─── Typography ─────────────────────────────────────── */
        h1, h2, h3 {
            font-family: Georgia, "Times New Roman", serif;
            color: var(--c-ink);
            letter-spacing: -0.022em;
            overflow: visible !important;
            white-space: normal !important;
            line-height: 1.4 !important;
        }

        h1 { font-size: 2.2rem; }
        h2 { font-size: 1.55rem; }
        h3 { font-size: 1.18rem; }

        /* Heading containers: mai troncare */
        div[data-testid="stHeading"],
        div[data-testid="stHeadingWithActionElements"] {
            overflow: visible !important;
            white-space: normal !important;
        }

        p,
        .stMarkdown p,
        label[data-testid="stWidgetLabel"] {
            color: var(--c-muted) !important;
            font-size: 0.94rem;
        }

        /* Caption: contrasto WCAG-AA (#1a2d3a su bianco — ratio ~12:1) */
        div[data-testid="stCaptionContainer"] p {
            color: #1a2d3a !important;
            font-size: 0.88rem !important;
        }

        /* ─── Sidebar ────────────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(170deg, #12253a 0%, #1b3a60 100%);
            border-right: none;
        }

        section[data-testid="stSidebar"] > div {
            min-width: 14.5rem;
            max-width: 14.5rem;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] label {
            color: #bbd3e8 !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #e0f0fd !important;
        }

        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.12);
        }

        section[data-testid="stSidebar"] .stAlert {
            border-radius: var(--r-sm) !important;
        }

        /* Avviso norme placeholder — visibile su sfondo navy */
        section[data-testid="stSidebar"] div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
            background: rgba(255, 180, 0, 0.22) !important;
            border: 1px solid rgba(255, 180, 0, 0.60) !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) p,
        section[data-testid="stSidebar"] div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) strong {
            color: #ffe08a !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
            background: rgba(39, 174, 96, 0.22) !important;
            border: 1px solid rgba(100, 210, 140, 0.60) !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) p {
            color: #a8f0c0 !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.10) !important;
            border-radius: var(--r-sm) !important;
            padding: 0.45rem 0.55rem !important;
            min-height: unset !important;
            transition: background 0.15s ease, border-color 0.15s ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a:hover {
            background: rgba(255, 255, 255, 0.13) !important;
            border-color: rgba(255, 255, 255, 0.20) !important;
            transform: none !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a p {
            color: #cce3f5 !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }

        /* ─── Alerts ─────────────────────────────────────────── */
        .stAlert {
            border-radius: var(--r);
            border-width: 1px;
            box-shadow: none;
        }

        /* ─── Metrics ────────────────────────────────────────── */
        div[data-testid="stMetric"] {
            background: var(--c-surface);
            border: 1px solid var(--c-border-l);
            border-radius: var(--r);
            padding: 0.8rem 0.95rem;
            box-shadow: var(--c-shadow);
            overflow: visible;
        }

        div[data-testid="stMetricLabel"] * {
            color: var(--c-muted) !important;
            font-weight: 600;
            font-size: 0.8rem !important;
            text-transform: uppercase;
            letter-spacing: 0.055em;
        }

        div[data-testid="stMetricValue"] * {
            color: var(--c-ink) !important;
            font-weight: 700;
            font-size: clamp(0.82rem, 2.3vw, 1.55rem) !important;
            overflow-wrap: break-word;
            word-break: break-word;
            white-space: normal;
        }

        /* ─── Buttons ────────────────────────────────────────── */
        .stButton > button,
        .stDownloadButton > button {
            border-radius: var(--r-sm);
            font-weight: 600;
            min-height: 2.7rem;
            transition: background 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease,
                        border-color 0.15s ease;
            box-shadow: none;
            border: 1px solid var(--c-border);
            background: var(--c-surface);
            color: var(--c-ink);
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"],
        .stFormSubmitButton button,
        button[data-testid="stBaseButton-primaryFormSubmit"],
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(180deg, #2271a8 0%, var(--c-primary) 100%) !important;
            color: #ffffff !important;
            border-color: transparent !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton button:hover,
        button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            box-shadow: 0 4px 14px rgba(26, 79, 114, 0.30) !important;
            transform: translateY(-1px);
        }

        .stButton > button:not([kind="primary"]):hover {
            border-color: var(--c-primary-l);
        }

        /* Fix: testo pulsanti primari — bianco esplicito per non ereditare muted */
        .stFormSubmitButton button p,
        .stFormSubmitButton button *,
        .stButton > button[kind="primary"] p,
        .stButton > button[kind="primary"] *,
        .stDownloadButton > button[kind="primary"] p,
        .stDownloadButton > button[kind="primary"] *,
        button[data-testid="stBaseButton-primary"] p,
        button[data-testid="stBaseButton-primary"] *,
        button[data-testid="stBaseButton-primaryFormSubmit"] p,
        button[data-testid="stBaseButton-primaryFormSubmit"] * {
            color: #ffffff !important;
            font-size: inherit !important;
        }

        /* Fix: testo pulsanti secondari — usa colore ink standard */
        .stButton > button:not([kind="primary"]) p,
        .stButton > button:not([kind="primary"]) *,
        .stDownloadButton > button:not([kind="primary"]) p,
        .stDownloadButton > button:not([kind="primary"]) * {
            color: var(--c-ink) !important;
            font-size: inherit !important;
        }

        /* ─── Inputs ─────────────────────────────────────────── */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"],
        .stDateInput input,
        .stNumberInput input {
            background: var(--c-surface) !important;
            color: var(--c-ink) !important;
            border: 1px solid var(--c-border) !important;
            border-radius: var(--r-sm) !important;
            box-shadow: none !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus,
        .stNumberInput input:focus {
            border-color: var(--c-primary-l) !important;
            box-shadow: 0 0 0 3px rgba(40, 116, 166, 0.14) !important;
        }

        /* ─── Home nav cards ──────────────────────────────────── */
        div[data-testid="stPageLink"] a {
            background: var(--c-surface);
            border: 1px solid var(--c-border-l);
            border-radius: var(--r-lg);
            padding: 1.05rem 1.1rem;
            min-height: 4.2rem;
            box-shadow: var(--c-shadow);
            transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.12s ease;
        }

        div[data-testid="stPageLink"] a:hover {
            border-color: var(--c-primary-l);
            box-shadow: var(--c-shadow-md);
            transform: translateY(-2px);
        }

        div[data-testid="stPageLink"] a p {
            font-weight: 700 !important;
            color: var(--c-ink) !important;
            font-size: 0.97rem !important;
        }

        /* ─── Expanders ───────────────────────────────────────── */
        div[data-testid="stExpander"] {
            border: 1px solid var(--c-border-l);
            border-radius: var(--r);
            background: var(--c-surface);
            box-shadow: none;
            overflow: hidden;
        }

        /* ─── Bordered containers ─────────────────────────────── */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--c-border-l) !important;
            border-radius: var(--r) !important;
            background: var(--c-surface) !important;
            box-shadow: var(--c-shadow) !important;
        }

        /* ─── HR ──────────────────────────────────────────────── */
        hr { border-color: var(--c-border-l); }

        /* ─── Custom component classes ────────────────────────── */

        /* Home page card subtitle */
        .cpm-home-card-caption {
            color: var(--c-muted) !important;
            font-size: 0.875rem;
            line-height: 1.45;
            padding: 0.2rem 0.25rem 0.4rem 0.25rem;
        }

        /* Scoring page instruction banner */
        .cpm-response-help {
            background: var(--c-surface-alt);
            border: 1px solid var(--c-border-l);
            border-radius: var(--r);
            padding: 0.7rem 1rem;
            margin-bottom: 0.8rem;
            color: var(--c-muted);
        }

        /* Set column header */
        .cpm-set-title {
            background: transparent;
            border-bottom: 2px solid var(--c-border);
            padding: 0.5rem 0.65rem 0.45rem 0.65rem;
            font-weight: 800;
            font-size: 0.86rem;
            color: var(--c-primary) !important;
            text-transform: uppercase;
            letter-spacing: 0.065em;
            margin-bottom: 0.6rem;
        }

        /* Item code label above each input */
        .cpm-item-label {
            font-weight: 700;
            margin-bottom: 0.15rem;
            color: var(--c-ink);
            text-align: center;
            font-size: 0.875rem;
        }

        /* Response counter toolbar */
        .cpm-scoring-toolbar {
            background: var(--c-surface-alt);
            border: 1px solid var(--c-border-l);
            border-radius: var(--r);
            padding: 0.65rem 0.9rem;
            margin-bottom: 0.7rem;
            color: var(--c-muted);
        }

        /* Keyboard shortcut badge */
        .cpm-kbd {
            display: inline-block;
            min-width: 1.75rem;
            padding: 0.05rem 0.32rem;
            margin-inline: 0.1rem;
            border-radius: 6px;
            border: 1px solid var(--c-border);
            background: var(--c-surface);
            color: var(--c-ink);
            font-size: 0.83rem;
            font-weight: 700;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.07);
        }

        /* Centred large input for single-character responses */
        div[data-testid="stTextInput"] input[aria-label^="Risposta "] {
            text-align: center;
            font-size: 1.1rem;
            font-weight: 800;
            padding-top: 0.45rem !important;
            padding-bottom: 0.45rem !important;
        }

        /* Placeholder "1-6" non viene troncato nelle colonne strette */
        div[data-testid="stTextInput"] input[aria-label^="Risposta "]::placeholder {
            font-size: 0.72rem;
            font-weight: 400;
            letter-spacing: -0.01em;
            opacity: 0.7;
        }

        div[data-testid="stTextInput"] {
            margin-bottom: 0.3rem;
        }

        /* ─── Caption: contrasto migliorato ──────────────────── */
        /* (spostato in Typography — questa sezione reserved) */

        /* ─── Heading anchor: visibile solo su hover ─────────── */
        [data-testid="stHeaderActionElements"] {
            opacity: 0;
            transition: opacity 0.2s;
            display: inline-flex !important;
            vertical-align: middle;
        }

        .stHeading:hover [data-testid="stHeaderActionElements"] {
            opacity: 0.4;
        }

        /* ─── Nascondi nav auto Streamlit (rimpiazzata da page_link) ─ */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* ─── Localizzazione testo file uploader ─────────────── */
        /* Testo principale (drag & drop) */
        div[data-testid="stFileUploaderDropzoneInstructions"] div > span:first-child {
            font-size: 0 !important;
            line-height: 0;
            color: transparent !important;
        }
        div[data-testid="stFileUploaderDropzoneInstructions"] div > span:first-child::after {
            content: "Trascina il file qui oppure clicca";
            font-size: 0.875rem;
            line-height: 1.4;
            display: inline;
            color: var(--c-ink);
        }
        /* Testo limite dimensione */
        div[data-testid="stFileUploaderDropzoneInstructions"] div > span:last-child {
            font-size: 0 !important;
            line-height: 0;
            color: transparent !important;
        }
        div[data-testid="stFileUploaderDropzoneInstructions"] div > span:last-child::after {
            content: "Limite 200 MB per file \u2022 CSV, XLSX, XLS";
            font-size: 0.75rem;
            line-height: 1.4;
            display: inline;
            color: var(--c-muted);
        }
        /* Pulsante Browse files \2192 Sfoglia file */
        div[data-testid="stFileUploader"] button[data-testid="stBaseButton-secondary"],
        div[data-testid="stFileUploader"] button[data-testid="stBaseButton-secondary"] * {
            color: transparent !important;
            font-size: 0 !important;
        }
        div[data-testid="stFileUploader"] button[data-testid="stBaseButton-secondary"]::after {
            content: "Sfoglia file";
            color: var(--c-ink);
            font-size: 0.875rem;
            font-weight: 600;
            display: inline;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def _render_sidebar() -> None:
    using_placeholder = is_using_placeholder()

    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.5rem 0.2rem 1.2rem 0.2rem;">
                <div style="font-size: 2rem; line-height:1;">🧩</div>
                <div style="font-size: 1.1rem; font-weight: 800; margin-top: 0.4rem; color: #e2f0fc;">
                    CPM Scoring Tool
                </div>
                <div style="font-size: 0.82rem; color: #7aadcc; margin-top: 0.1rem; letter-spacing: 0.02em;">
                    Matrici Colorate di Raven
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.page_link("app.py", label="Home", icon="🏠")
        st.page_link("pages/1_📝_Scoring.py", label="Scoring Singolo", icon="📝")
        st.page_link("pages/2_📊_Batch.py", label="Batch Scoring", icon="📊")
        st.page_link("pages/3_🗄️_Database.py", label="Database", icon="🗄️")
        st.page_link("pages/4_📄_Report.py", label="Report PDF", icon="📄")
        st.page_link("pages/5_📏_Norme.py", label="Norme", icon="📏")
        st.divider()
        if using_placeholder:
            st.warning(
                "Norme di esempio attive.\nCarica un CSV dalla pagina **Norme** per percentili reali.",
                icon="⚠️",
            )
        else:
            st.success("Norme personalizzate attive.", icon="✅")
