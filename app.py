"""
CPM Scoring Tool – Matrici Colorate di Raven
Applicazione Streamlit per lo scoring automatico.

Avvia con:  streamlit run app.py
"""

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="CPM Scoring Tool",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar branding + stato norme ────────
from core.norms import is_using_placeholder

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <span style="font-size:2.5rem;">🧩</span>
            <h2 style="margin:0; color:#1B3A6B;">CPM Scoring Tool</h2>
            <p style="color:#666; font-size:0.85rem; margin-top:0.2rem;">
                Matrici Colorate di Raven
            </p>
        </div>
        <hr style="margin: 0 0 1rem 0;">
        """,
        unsafe_allow_html=True,
    )
    if is_using_placeholder():
        st.warning("Norme: valori di esempio. Carica le norme reali in **📏 Norme**.", icon="⚠️")
    else:
        st.success("Norme personalizzate attive.", icon="✅")

# ── Home page ─────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding: 2rem 0;">
        <span style="font-size:4rem;">🧩</span>
        <h1 style="color:#1B3A6B; margin-bottom:0;">CPM Scoring Tool</h1>
        <p style="color:#555; font-size:1.15rem; max-width:600px; margin:0.5rem auto;">
            Strumento per lo scoring automatico delle
            <b>Matrici Progressive Colorate di Raven (CPM)</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Norme → Scoring o Batch → Database → Report")

st.divider()

# ── Navigation ────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/1_📝_Scoring.py", label="📝  Scoring Singolo", icon="📝")
    st.caption("Risposte di un soggetto, punteggio e grafici.")

with col2:
    st.page_link("pages/2_📊_Batch.py", label="📊  Batch Scoring", icon="📊")
    st.caption("Carica un file CSV/Excel con più soggetti.")

with col3:
    st.page_link("pages/3_🗄️_Database.py", label="🗄️  Database", icon="🗄️")
    st.caption("Consulta, filtra ed esporta i risultati salvati.")

col4, col5, col6 = st.columns(3)

with col4:
    st.page_link("pages/4_📄_Report.py", label="📄  Report PDF", icon="📄")
    st.caption("Genera report stampabili singoli o in blocco.")

with col5:
    st.page_link("pages/5_📏_Norme.py", label="📏  Norme", icon="📏")
    st.caption("Gestisci tabelle normative e calcolatore rapido.")

with col6:
    pass  # spazio vuoto per bilanciare la griglia

# ── In-app guide ─────────────────────────
guide_path = Path(__file__).resolve().parent / "docs" / "GUIDA.md"
with st.expander("📘 Guida rapida all'uso", expanded=False):
    if guide_path.is_file():
        st.markdown(guide_path.read_text(encoding="utf-8"))
    else:
        st.markdown(
            "**Workflow**: Norme → Scoring o Batch → Database → Report"
        )

st.caption(
    "Tool per uso accademico e di ricerca. "
    "Il test CPM è di proprietà di Pearson/OS Firenze — utilizzare solo con licenza valida."
)
