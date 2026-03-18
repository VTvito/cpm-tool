"""
CPM Scoring Tool – Matrici Colorate di Raven
Applicazione Streamlit per lo scoring automatico.

Avvia con:  streamlit run app.py
"""

from pathlib import Path

import streamlit as st
from streamlit_ui import configure_page

configure_page("CPM Scoring Tool", "🧩")

# ── Hero ──────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding: 2.5rem 0 1.8rem 0;">
        <div style="font-size:3.5rem; line-height:1; margin-bottom:0.5rem;">🧩</div>
        <h1 style="font-size:2.6rem; margin:0 0 0.5rem 0;
                   font-family:Georgia,serif; letter-spacing:-0.03em;
                   color:#0e1d2a;">
            CPM Scoring Tool
        </h1>
        <p style="color:#4c6475; font-size:1.05rem;
                  max-width:540px; margin:0 auto 1.2rem; line-height:1.6;">
            Scoring automatico delle
            <strong>Matrici Progressive Colorate di Raven</strong>.<br>
            Norme Belacchi <em>et al.</em> (2008), fascia di età 3–11 anni.
        </p>
        <div style="display:inline-flex; align-items:center; gap:0.6rem;
                    background:#eaeff5; border-radius:24px;
                    padding:0.3rem 1rem; font-size:0.85rem; color:#4c6475;">
            <span>📚 Uso accademico e di ricerca</span>
            <span style="opacity:0.35;">·</span>
            <span>🔒 Dati locali — nessun invio esterno</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Navigation cards ──────────────────────
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

with col1:
    st.page_link("pages/1_📝_Scoring.py", label="Scoring Singolo", icon="📝")
    st.markdown(
        '<div class="cpm-home-card-caption">Inserisci le risposte di un soggetto, '
        "calcola punteggio e percentile.</div>",
        unsafe_allow_html=True,
    )

with col2:
    st.page_link("pages/2_📊_Batch.py", label="Batch Scoring", icon="📊")
    st.markdown(
        '<div class="cpm-home-card-caption">Carica un file CSV o Excel '
        "con più soggetti in una sola operazione.</div>",
        unsafe_allow_html=True,
    )

with col3:
    st.page_link("pages/3_🗄️_Database.py", label="Database", icon="🗄️")
    st.markdown(
        '<div class="cpm-home-card-caption">Consulta, filtra ed esporta '
        "i risultati salvati dalle sessioni precedenti.</div>",
        unsafe_allow_html=True,
    )

with col4:
    st.page_link("pages/4_📄_Report.py", label="Report PDF", icon="📄")
    st.markdown(
        '<div class="cpm-home-card-caption">Genera report stampabili '
        "per singolo soggetto o in batch come file ZIP.</div>",
        unsafe_allow_html=True,
    )

with col5:
    st.page_link("pages/5_📏_Norme.py", label="Norme", icon="📏")
    st.markdown(
        '<div class="cpm-home-card-caption">Gestisci le tabelle normative '
        "e verifica un percentile con il calcolatore rapido.</div>",
        unsafe_allow_html=True,
    )

# col6 vuoto — griglia 3+2

# ── Workflow ──────────────────────────────
st.markdown(
    """
    <div style="background:#ffffff; border:1px solid #dce6ee; border-radius:14px;
                padding:1.1rem 1.5rem; margin:1.5rem 0 0 0;
                box-shadow:0 2px 8px rgba(14,29,42,0.06);">
        <div style="font-weight:700; color:#0e1d2a; margin-bottom:0.75rem;
                    font-size:0.82rem; text-transform:uppercase; letter-spacing:0.06em;">
            Workflow consigliato
        </div>
        <div style="display:flex; align-items:center; gap:0.45rem; flex-wrap:wrap;">
            <span style="background:#eaeff5; border-radius:8px;
                         padding:0.22rem 0.7rem; font-size:0.88rem;
                         color:#1a4f72; font-weight:700;">1 · Norme</span>
            <span style="color:#b0bec8; font-size:0.8rem;">▶</span>
            <span style="background:#eaeff5; border-radius:8px;
                         padding:0.22rem 0.7rem; font-size:0.88rem;
                         color:#1a4f72; font-weight:700;">2 · Scoring o Batch</span>
            <span style="color:#b0bec8; font-size:0.8rem;">▶</span>
            <span style="background:#eaeff5; border-radius:8px;
                         padding:0.22rem 0.7rem; font-size:0.88rem;
                         color:#1a4f72; font-weight:700;">3 · Database</span>
            <span style="color:#b0bec8; font-size:0.8rem;">▶</span>
            <span style="background:#eaeff5; border-radius:8px;
                         padding:0.22rem 0.7rem; font-size:0.88rem;
                         color:#1a4f72; font-weight:700;">4 · Report PDF</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── In-app guide ─────────────────────────
guide_path = Path(__file__).resolve().parent / "docs" / "GUIDA.md"
with st.expander("📘 Guida rapida all'uso", expanded=False):
    if guide_path.is_file():
        st.markdown(guide_path.read_text(encoding="utf-8"))
    else:
        st.markdown("**Workflow**: Norme → Scoring o Batch → Database → Report")

st.caption(
    "Tool per uso accademico e di ricerca. "
    "Il test CPM è di proprietà di Pearson/OS Firenze — utilizzare solo con licenza valida."
)
