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
            --cpm-bg: #f5f1e8;
            --cpm-surface: #fffdf8;
            --cpm-surface-strong: #ffffff;
            --cpm-ink: #16202b;
            --cpm-muted: #536173;
            --cpm-border: #c9d2dd;
            --cpm-primary: #0f5c8a;
            --cpm-primary-strong: #0b466a;
            --cpm-accent: #c26d1a;
            --cpm-success: #1e6b42;
            --cpm-warning: #9c4b00;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(15, 92, 138, 0.08), transparent 24%),
                linear-gradient(180deg, #f8f5ef 0%, var(--cpm-bg) 100%);
            color: var(--cpm-ink);
            font-family: "Segoe UI", Aptos, "Trebuchet MS", sans-serif;
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3, h4, h5, h6,
        p, label, span, div {
            color: var(--cpm-ink);
        }

        p,
        div[data-testid="stCaptionContainer"] p,
        label[data-testid="stWidgetLabel"] {
            color: var(--cpm-muted) !important;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eef3f7 0%, #e7edf3 100%);
            border-right: 1px solid rgba(15, 92, 138, 0.18);
        }

        section[data-testid="stSidebar"] > div {
            min-width: 16rem;
            max-width: 16rem;
        }

        .stAlert {
            border-radius: 12px;
            border-width: 1px;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(22, 32, 43, 0.10);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            box-shadow: 0 6px 20px rgba(22, 32, 43, 0.04);
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
            border: 1px solid rgba(15, 92, 138, 0.28);
            box-shadow: none;
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
        }

        div[data-testid="stPageLink"] a {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(15, 92, 138, 0.16);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            min-height: 4rem;
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
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(15, 92, 138, 0.12);
            border-radius: 12px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.75rem;
            color: var(--cpm-muted);
        }

        .cpm-set-title {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 92, 138, 0.14);
            border-radius: 12px;
            padding: 0.55rem 0.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .cpm-item-label {
            font-weight: 700;
            padding-top: 0.45rem;
            color: var(--cpm-ink);
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