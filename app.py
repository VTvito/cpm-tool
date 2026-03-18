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

# ── Sidebar branding ──────────────────────
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

st.divider()

# ── In-app guide ─────────────────────────
guide_path = Path(__file__).resolve().parent / "docs" / "GUIDA.md"
with st.expander("📘 Guida rapida all'uso", expanded=False):
    if guide_path.is_file():
        st.markdown(guide_path.read_text(encoding="utf-8"))
    else:
        st.markdown(
            """
            **Workflow consigliato**

            1. Vai su **📏 Norme** e carica il CSV con le norme ufficiali.
            2. Usa **📝 Scoring** per un singolo soggetto oppure **📊 Batch** per più soggetti.
            3. Salva i risultati nel database.
            4. Genera i report da **📄 Report**.
            """
        )

st.markdown("### Percorsi rapidi")
guide_col1, guide_col2, guide_col3 = st.columns(3)
with guide_col1:
    st.info("**Devo iniziare**\n\nCarica le norme ufficiali in **📏 Norme** se non vuoi usare valori di esempio.")
with guide_col2:
    st.info("**Devo fare scoring**\n\nUsa **📝 Scoring** per un soggetto o **📊 Batch** per un file con più soggetti.")
with guide_col3:
    st.info("**Devo esportare**\n\nI risultati si ritrovano in **🗄️ Database** e i PDF si generano in **📄 Report**.")

st.divider()

# ── Quick navigation ─────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        ### 📝 Scoring Singolo
        Inserisci le risposte di un soggetto e ottieni
        il punteggio, il percentile e i grafici in tempo reale.
        """
    )
    st.page_link("pages/1_📝_Scoring.py", label="Vai allo Scoring →", icon="📝")

with col2:
    st.markdown(
        """
        ### 📊 Batch & Database
        Carica un file con più soggetti per lo scoring di gruppo,
        oppure consulta il database dei risultati salvati.
        """
    )
    bc1, bc2 = st.columns(2)
    with bc1:
        st.page_link("pages/2_📊_Batch.py", label="Batch →", icon="📊")
    with bc2:
        st.page_link("pages/3_🗄️_Database.py", label="Database →", icon="🗄️")

with col3:
    st.markdown(
        """
        ### 📄 Report & Norme
        Genera un report PDF stampabile per ogni soggetto
        e consulta le tabelle normative con la legenda.
        """
    )
    rc1, rc2 = st.columns(2)
    with rc1:
        st.page_link("pages/4_📄_Report.py", label="Report →", icon="📄")
    with rc2:
        st.page_link("pages/5_📏_Norme.py", label="Norme →", icon="📏")

st.divider()

st.caption("Se non sai da dove partire: **Norme -> Scoring o Batch -> Database -> Report**")

# ── Info box ──────────────────────────────
from core.norms import is_using_placeholder
if is_using_placeholder():
    st.warning(
        "⚠️ **Nota importante**: le norme attualmente in uso sono **valori di esempio** (placeholder). "
        "Prima dell'uso clinico o di ricerca, caricare i valori dal manuale ufficiale "
        "dalla pagina **📏 Norme**.",
        icon="📋",
    )
else:
    st.success(
        "✅ Norme personalizzate caricate. Il tool è pronto per l'uso.",
        icon="✅",
    )

st.caption(
    "Tool per uso accademico e di ricerca. "
    "Il test CPM è di proprietà di Pearson/OS Firenze — utilizzare solo con licenza valida."
)
