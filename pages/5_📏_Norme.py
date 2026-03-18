"""
Pagina 5 – Tabelle Normative

Modifica diretta della tabella norme nell'interfaccia (no CSV richiesto).
Il caricamento/esportazione CSV è disponibile come operazione secondaria.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from core.norms import (
    AGE_BANDS, get_norm_table_as_dicts,
    lookup_percentile, describe_percentile,
    is_using_placeholder, save_norms_csv, get_norms_csv_path,
)
from streamlit_ui import configure_page


configure_page("Norme CPM", "📏")

_PERC_OPTIONS = ["<5", "5", "10", "25", "50", "75", "90", "95", ">95"]


def _build_norm_df() -> pd.DataFrame:
    return pd.DataFrame(get_norm_table_as_dicts())


def _on_save_from_editor():
    """Serializza il DataFrame dell'editor e salva come CSV."""
    df = st.session_state.get("norm_edited_values")
    if df is None or df.empty:
        st.session_state["norm_upload_error"] = "Nessun dato da salvare."
        st.session_state.pop("norm_upload_ok", None)
        return
    age_cols = [c for c in df.columns if c != "Punteggio Grezzo"]
    if df[age_cols].isnull().any().any():
        st.session_state["norm_upload_error"] = (
            "Alcune celle sono ancora vuote. Seleziona un valore in ogni cella prima di salvare."
        )
        st.session_state.pop("norm_upload_ok", None)
        return
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    msg = save_norms_csv(csv_bytes)
    if msg.startswith("Errore"):
        st.session_state["norm_upload_error"] = msg
        st.session_state.pop("norm_upload_ok", None)
    else:
        st.session_state["norm_upload_ok"] = msg
        st.session_state.pop("norm_upload_error", None)


def _on_upload_norms():
    """Salva il CSV caricato dall'utente."""
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
    """Elimina il CSV personalizzato e torna ai placeholder."""
    csv_path = get_norms_csv_path()
    if csv_path.is_file():
        csv_path.unlink()
    st.session_state["norm_upload_ok"] = "Norme ripristinate ai valori di esempio."
    st.session_state.pop("norm_upload_error", None)


# ─────────────────────────────────────────
#  HEADER + STATUS
# ─────────────────────────────────────────
st.header("📏 Tabelle Normative CPM")

using_placeholder = is_using_placeholder()
if using_placeholder:
    st.warning(
        "**Norme di esempio attive** — i percentili mostrati sono valori fittizi. "
        "Modifica la tabella qui sotto e premi **Salva norme** per attivare i dati reali "
        "(Belacchi et al., 2008).",
        icon="⚠️",
    )
else:
    st.success(
        "**Norme personalizzate attive** — percentili calcolati dalla tabella salvata.",
        icon="✅",
    )

# ─────────────────────────────────────────
#  TABELLA NORME — EDITING DIRETTO
# ─────────────────────────────────────────
st.subheader("✏️ Tabella Norme")
st.caption(
    "Clicca su una cella per selezionare il percentile corrispondente. "
    "La colonna **P. Grezzo** non è modificabile. "
    "Premi **Salva norme** per rendere effettive le modifiche."
)

norm_df = _build_norm_df()
age_cols = [c for c in norm_df.columns if c != "Punteggio Grezzo"]

column_config: dict = {
    "Punteggio Grezzo": st.column_config.NumberColumn(
        "P. Grezzo",
        disabled=True,
        width="small",
        help="Punteggio totale CPM (0–36). Non modificabile.",
    ),
}
for col in age_cols:
    column_config[col] = st.column_config.SelectboxColumn(
        col,
        options=_PERC_OPTIONS,
        required=True,
        width="small",
    )

edited_df = st.data_editor(
    norm_df,
    column_config=column_config,
    num_rows="fixed",
    hide_index=True,
    key="norm_editor",
)
# Persisti il DataFrame modificato per la callback (pattern data_editor)
st.session_state["norm_edited_values"] = edited_df

# Messaggi di feedback
if st.session_state.get("norm_upload_error"):
    st.error(f"❌ {st.session_state['norm_upload_error']}")
if st.session_state.get("norm_upload_ok"):
    st.success(f"✅ {st.session_state['norm_upload_ok']}")

btn_c1, btn_c2, _ = st.columns([1, 2, 3])
with btn_c1:
    st.button(
        "💾 Salva norme",
        type="primary",
        on_click=_on_save_from_editor,
        width="stretch",
    )
with btn_c2:
    st.button(
        "🔄 Ripristina valori di esempio",
        on_click=_on_reset_norms,
        disabled=using_placeholder,
        help="Cancella le norme personalizzate e torna ai valori placeholder.",
    )

# ─────────────────────────────────────────
#  CSV: IMPORTA / ESPORTA (secondario)
# ─────────────────────────────────────────
with st.expander("🗂️ Importa / Esporta CSV", expanded=False):
    st.caption(
        "Usa questa sezione se preferisci compilare le norme in Excel e importarle, "
        "oppure per fare un backup/ripristino del file corrente."
    )

    dl_c1, dl_c2 = st.columns(2)

    # Template CSV (con BOM per apertura corretta in Excel)
    template_path = Path(__file__).resolve().parent.parent / "data" / "norms_template.csv"
    if template_path.is_file():
        raw_bytes = template_path.read_bytes()
        bom = b"\xef\xbb\xbf"
        template_bytes = raw_bytes if raw_bytes.startswith(bom) else bom + raw_bytes
        with dl_c1:
            st.download_button(
                "⬇️ Template CSV (vuoto)",
                data=template_bytes,
                file_name="CPM_Norme_Template.csv",
                mime="text/csv; charset=utf-8",
                help="Apri con Excel, compila i valori dal manuale, salva come CSV e ricarica qui sotto.",
            )

    # Norme attuali
    csv_path = get_norms_csv_path()
    if csv_path.is_file():
        raw_saved = csv_path.read_bytes()
        bom = b"\xef\xbb\xbf"
        saved_bytes = raw_saved if raw_saved.startswith(bom) else bom + raw_saved
        with dl_c2:
            st.download_button(
                "⬇️ Norme attuali (CSV)",
                data=saved_bytes,
                file_name="CPM_Norme_Attuali.csv",
                mime="text/csv; charset=utf-8",
            )

    st.divider()
    st.file_uploader(
        "Carica CSV con le norme",
        type=["csv"],
        help=(
            "Formato: prima colonna = Punteggio Grezzo (intero); "
            "colonne successive = percentile per fascia d'età (es. Età 7, Adulti, Anziani). "
            "Valori percentile accettati: <5 · 5 · 10 · 25 · 50 · 75 · 90 · 95 · >95."
        ),
        key="norm_csv_upload",
    )
    st.button(
        "📤 Applica CSV caricato",
        type="primary",
        on_click=_on_upload_norms,
        disabled=st.session_state.get("norm_csv_upload") is None,
    )

st.divider()

# ─────────────────────────────────────────
#  CALCOLATORE RAPIDO
# ─────────────────────────────────────────
st.subheader("🔢 Calcolatore Rapido")
st.caption("Inserisci punteggio grezzo e fascia d'età per ottenere subito il percentile.")

q1, q2 = st.columns(2)
with q1:
    raw = st.number_input(
        "Punteggio Grezzo",
        min_value=0, max_value=36, value=18, step=1,
        key="norm_raw",
    )
with q2:
    bands_calc = [col.replace("Età ", "") for col in age_cols] if age_cols else AGE_BANDS[:9]
    band = st.selectbox("Fascia d'Età", options=bands_calc, key="norm_band")

pct = lookup_percentile(raw, band)
desc = describe_percentile(pct)

c1, c2, c3 = st.columns(3)
c1.metric("Punteggio", f"{raw} / 36")
c2.metric("Percentile", pct)
c3.metric("Classificazione", desc)

st.divider()

# ─────────────────────────────────────────
#  LEGENDA
# ─────────────────────────────────────────
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
