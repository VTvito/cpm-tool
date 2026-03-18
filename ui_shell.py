from __future__ import annotations

import streamlit as st

from core.norms import is_using_placeholder


def configure_page(page_title: str, page_icon: str = "🧩") -> None:
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_styles()
    _render_sidebar()


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --cpm-bg: #f2eee6;
            --cpm-surface: #faf7f1;
            --cpm-surface-strong: #ffffff;
            --cpm-ink: #13202d;
            --cpm-muted: #4c5b6d;
            --cpm-border: #bcc8d4;
            --cpm-primary: #0e5a86;
            --cpm-primary-strong: #0a3f61;
            --cpm-accent: #a95f18;
            --cpm-success: #1e6b42;
            --cpm-warning: #9c4b00;
            --cpm-shadow: 0 10px 32px rgba(19, 32, 45, 0.06);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(14, 90, 134, 0.10), transparent 22%),
                radial-gradient(circle at top left, rgba(169, 95, 24, 0.08), transparent 18%),
                linear-gradient(180deg, #f7f3ec 0%, var(--cpm-bg) 100%);
            color: var(--cpm-ink);
            font-family: Aptos, "Segoe UI", "Trebuchet MS", sans-serif;
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1rem;
            padding-bottom: 2.2rem;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--cpm-ink);
            font-family: Georgia, "Times New Roman", serif;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem;
        }

        h2 {
            font-size: 1.7rem;
        }

        p, label, span, div {
            color: var(--cpm-ink);
        }

        p,
        div[data-testid="stCaptionContainer"] p,
        label[data-testid="stWidgetLabel"] {
            color: var(--cpm-muted) !important;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ebf1f6 0%, #e0e8ef 100%);
            border-right: 1px solid rgba(14, 90, 134, 0.16);
        }

        section[data-testid="stSidebar"] > div {
            min-width: 16rem;
            max-width: 16rem;
        }

        .stAlert {
            border-radius: 14px;
            border-width: 1px;
            box-shadow: var(--cpm-shadow);
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(19, 32, 45, 0.08);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            box-shadow: var(--cpm-shadow);
        }

        div[data-testid="stMetricLabel"] * {
            color: var(--cpm-muted) !important;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] * {
            color: var(--cpm-ink) !important;
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stBaseButton-secondary"] > button,
        div[data-testid="stBaseButton-primary"] > button {
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid rgba(14, 90, 134, 0.24);
            box-shadow: none;
            min-height: 2.9rem;
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background: linear-gradient(180deg, var(--cpm-primary) 0%, var(--cpm-primary-strong) 100%);
            color: #ffffff;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"],
        .stDateInput input,
        .stNumberInput input {
            background: var(--cpm-surface-strong) !important;
            color: var(--cpm-ink) !important;
            border: 1px solid var(--cpm-border) !important;
            border-radius: 10px !important;
            box-shadow: none !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus,
        .stNumberInput input:focus {
            border-color: var(--cpm-primary) !important;
            box-shadow: 0 0 0 3px rgba(14, 90, 134, 0.16) !important;
            transform: translateY(-1px);
        }

        div[data-testid="stPageLink"] a {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(14, 90, 134, 0.12);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            min-height: 4rem;
            box-shadow: var(--cpm-shadow);
        }

        div[data-testid="stPageLink"] a:hover {
            border-color: rgba(15, 92, 138, 0.32);
            background: #ffffff;
        }

        .cpm-home-card-caption {
            min-height: 2.7rem;
            padding-inline: 0.2rem;
        }

        .cpm-response-help {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 251, 253, 0.88) 100%);
            border: 1px solid rgba(14, 90, 134, 0.12);
            border-radius: 14px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.85rem;
            color: var(--cpm-muted);
            box-shadow: var(--cpm-shadow);
        }

        .cpm-set-title {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(245, 249, 252, 0.92) 100%);
            border: 1px solid rgba(14, 90, 134, 0.14);
            border-radius: 14px;
            padding: 0.65rem 0.8rem;
            font-weight: 700;
            margin-bottom: 0.65rem;
            box-shadow: var(--cpm-shadow);
        }

        .cpm-set-card {
            background: rgba(255, 255, 255, 0.64);
            border: 1px solid rgba(14, 90, 134, 0.10);
            border-radius: 16px;
            padding: 0.8rem 0.8rem 0.5rem 0.8rem;
            box-shadow: var(--cpm-shadow);
        }

        .cpm-item-label {
            font-weight: 700;
            padding-top: 0.1rem;
            margin-bottom: 0.2rem;
            color: var(--cpm-ink);
            text-align: center;
            font-size: 0.9rem;
        }

        .cpm-scoring-toolbar {
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(14, 90, 134, 0.10);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.8rem;
            box-shadow: var(--cpm-shadow);
        }

        .cpm-kbd {
            display: inline-block;
            min-width: 1.9rem;
            padding: 0.08rem 0.4rem;
            margin-inline: 0.12rem;
            border-radius: 8px;
            border: 1px solid rgba(19, 32, 45, 0.12);
            background: rgba(255, 255, 255, 0.9);
            color: var(--cpm-ink);
            font-size: 0.86rem;
            font-weight: 700;
            text-align: center;
        }

        div[data-testid="stTextInput"] input[aria-label^="Risposta "] {
            text-align: center;
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }

        div[data-testid="stTextInput"] {
            margin-bottom: 0.35rem;
        }

        div[data-testid="stExpander"] {
            border: 1px solid rgba(14, 90, 134, 0.10);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.76);
            box-shadow: var(--cpm-shadow);
            overflow: hidden;
        }

        hr {
            border-color: rgba(22, 32, 43, 0.10);
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
            <div style="padding: 0.2rem 0 1rem 0;">
                <div style="font-size: 2rem; line-height: 1;">🧩</div>
                <div style="font-size: 1.2rem; font-weight: 800; margin-top: 0.35rem; color: #132238;">
                    CPM Scoring Tool
                </div>
                <div style="font-size: 0.92rem; color: #536173; margin-top: 0.15rem;">
                    Matrici Colorate di Raven
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if using_placeholder:
            st.warning(
                "Norme di esempio attive. Per percentili reali, carica un CSV dalla pagina Norme.",
                icon="⚠️",
            )
        else:
            st.success("Norme personalizzate attive.", icon="✅")