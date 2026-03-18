"""
Pagina 5 – Tabelle Normative

Consultazione interattiva delle norme CPM per fascia d'età.
Include caricamento norme da file CSV per utenti non tecnici.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from core.norms import (
    AGE_BANDS, get_norm_table_as_dicts,
    lookup_percentile, describe_percentile,
    is_using_placeholder, save_norms_csv, get_norms_csv_path,
)


def _on_upload_norms():
    """Callback: salva il CSV norme caricato dall'utente."""
    uploaded = st.session_state.get("norm_csv_upload")
    if uploaded is None:
        return
    csv_bytes = uploaded.getvalue()
    msg = save_norms_csv(csv_bytes)
    if msg.startswith("Errore"):
        st.session_state["norm_upload_error"] = msg
        st.session_state.pop("norm_upload_ok", None)
    else:
        st.session_state["norm_upload_ok"] = msg
        st.session_state.pop("norm_upload_error", None)


def _on_reset_norms():
    """Callback: elimina il CSV norme personalizzato, torna ai placeholder."""
    csv_path = get_norms_csv_path()
    if csv_path.is_file():
        csv_path.unlink()
    st.session_state["norm_upload_ok"] = "Norme ripristinate ai valori placeholder di esempio."
    st.session_state.pop("norm_upload_error", None)


st.header("📏 Tabelle Normative CPM")
st.caption("Lo stato corrente delle norme è mostrato nella sidebar. Qui puoi caricare, scaricare o ripristinare il CSV usato dal tool.")

# ── STATO NORME ───────────────────────────
using_placeholder = is_using_placeholder()
norms_panel_open = (
    using_placeholder
    or st.session_state.get("norm_csv_upload") is not None
    or bool(st.session_state.get("norm_upload_error"))
    or bool(st.session_state.get("norm_upload_ok"))
)

# ─────────────────────────────────────────
#  CARICAMENTO NORME DA CSV
# ─────────────────────────────────────────
with st.expander("📂 Carica / Gestisci Norme dal Manuale", expanded=norms_panel_open):
    st.markdown(
        "Per caricare le norme dal manuale Belacchi et al. (2008):\n\n"
        "1. **Scarica il template CSV** qui sotto\n"
        "2. **Aprilo con Excel** (o LibreOffice Calc)\n"
        "3. **Sostituisci i valori** con quelli del manuale, mantenendo il formato\n"
        "4. **Salva come CSV** e caricalo qui\n\n"
        "Il formato è: prima colonna = Punteggio Grezzo, "
        "colonne successive = percentile per ogni fascia d'età. "
        "Sono supportate le colonne Età 3–11 e, se presenti, Adulti e Anziani."
    )

    # Download template
    template_path = Path(__file__).resolve().parent.parent / "data" / "norms_template.csv"
    if template_path.is_file():
        st.download_button(
            "⬇️ Scarica Template CSV",
            data=template_path.read_bytes(),
            file_name="CPM_Norme_Template.csv",
            mime="text/csv",
        )

    # Download norme attuali (se personalizzate)
    csv_path = get_norms_csv_path()
    if csv_path.is_file():
        st.download_button(
            "⬇️ Scarica Norme Attuali (CSV)",
            data=csv_path.read_bytes(),
            file_name="CPM_Norme_Attuali.csv",
            mime="text/csv",
        )

    st.divider()

    # Upload
    st.file_uploader(
        "Carica file CSV con le norme",
        type=["csv"],
           help="Il file deve avere la colonna Punteggio Grezzo e una o più colonne età riconoscibili "
               "dal nome header, ad esempio Età 7, Adulti, Anziani.",
        key="norm_csv_upload",
    )
    st.button(
        "📤 Carica e Applica Norme",
        type="primary",
        on_click=_on_upload_norms,
        disabled=st.session_state.get("norm_csv_upload") is None,
    )

    st.divider()
    st.button(
        "🔄 Ripristina Norme Placeholder",
        on_click=_on_reset_norms,
        help="Rimuove il file norme personalizzato e torna ai valori di esempio.",
        disabled=using_placeholder,
    )

    if st.session_state.get("norm_upload_error"):
        st.error(f"❌ {st.session_state['norm_upload_error']}")

    if st.session_state.get("norm_upload_ok"):
        st.success(f"✅ {st.session_state['norm_upload_ok']}")

st.divider()

norm_data = get_norm_table_as_dicts()
df = pd.DataFrame(norm_data)
age_cols_available = [c for c in df.columns if c.startswith("Età ")]
bands_calc = [col.replace("Età ", "") for col in age_cols_available]

# ─────────────────────────────────────────
#  CALCOLATORE RAPIDO
# ─────────────────────────────────────────
st.subheader("🔢 Calcolatore Rapido")
st.caption(
    "Inserisci un punteggio grezzo e una fascia d'età per ottenere subito il percentile."
)

q1, q2 = st.columns(2)
with q1:
    raw = st.number_input(
        "Punteggio Grezzo",
        min_value=0, max_value=36, value=18, step=1,
        key="norm_raw",
    )
with q2:
    band = st.selectbox(
        "Fascia d'Età",
        options=bands_calc if bands_calc else AGE_BANDS[:9],
        key="norm_band",
    )

pct = lookup_percentile(raw, band)
desc = describe_percentile(pct)

c1, c2, c3 = st.columns(3)
c1.metric("Punteggio", f"{raw} / 36")
c2.metric("Percentile", pct)
c3.metric("Classificazione", desc)

st.divider()

# ─────────────────────────────────────────
#  TABELLA NORMATIVA
# ─────────────────────────────────────────
st.subheader("📊 Tabella Punteggio Grezzo → Percentile")

# Colori per i percentili
def color_percentile(val):
    if val in ("<5", "5"):
        return "background-color: #FADBD8"
    elif val in ("10", "25"):
        return "background-color: #FDEBD0"
    elif val == "50":
        return "background-color: #D5F5E3"
    elif val in ("75", "90"):
        return "background-color: #D6EAF8"
    elif val in ("95", ">95"):
        return "background-color: #D2B4DE"
    return ""

with st.expander("📄 Consulta la tabella completa", expanded=False):
    st.caption("Puoi filtrare per fascia d'età per una lettura più pulita:")
    selected_bands = st.multiselect(
        "Mostra fasce d'età",
        options=age_cols_available,
        default=age_cols_available,
        key="norm_filter",
    )

    cols_to_show = ["Punteggio Grezzo"] + selected_bands
    available_cols = [c for c in cols_to_show if c in df.columns]
    df_filtered = df[available_cols]

    styled = df_filtered.style.map(
        color_percentile,
        subset=[c for c in available_cols if c != "Punteggio Grezzo"],
    )

    st.dataframe(
        styled,
        width="stretch",
        height=min(600, 50 + 35 * len(df_filtered)),
    )

# ─────────────────────────────────────────
#  LEGENDA
# ─────────────────────────────────────────
st.divider()
st.subheader("📋 Legenda Bande di Prestazione")

legend = [
    ("< 5° percentile",     "#FADBD8", "Molto inferiore alla media"),
    ("5° percentile",        "#FADBD8", "Nettamente inferiore alla media"),
    ("10°–25° percentile",   "#FDEBD0", "Inferiore alla media"),
    ("50° percentile",       "#D5F5E3", "Nella media"),
    ("75°–90° percentile",   "#D6EAF8", "Superiore alla media"),
    ("≥ 95° percentile",     "#D2B4DE", "Nettamente superiore alla media"),
]

for pct_label, color, description in legend:
    st.markdown(
        f'<div style="display:flex; align-items:center; margin-bottom:0.3rem;">'
        f'<div style="width:20px; height:20px; background:{color}; '
        f'border-radius:4px; margin-right:0.7rem; border:1px solid #ccc;"></div>'
        f'<b>{pct_label}</b>&nbsp;&nbsp;→&nbsp;&nbsp;{description}'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "📖 Per le norme ufficiali consultare: "
    "Belacchi C., Scalisi T.G., Cannoni E., Cornoldi C. (2008). "
    "*CPM – Coloured Progressive Matrices*. Organizzazioni Speciali, Firenze."
)
