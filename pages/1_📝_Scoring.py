"""
Pagina 1 – Scoring Singolo Soggetto

ARCHITETTURA: usiamo on_click callbacks per mutare session_state PRIMA
che la pagina si ri-esegua, garantendo che pulsanti come "Salva" vedano
lo stato aggiornato al momento del rendering.
"""

import streamlit as st
import pandas as pd
from datetime import date

from core.answer_key import SETS, ANSWER_KEY
from core.scoring import score_with_norms, ScoringResult
from core.norms import age_to_band, is_using_placeholder
from core.charts import bar_chart_sets, radar_chart, percentile_gauge, item_heatmap
from core.pdf_report import generate_pdf
from core.database import save_result


def _build_editor_dataframe(set_key: str) -> pd.DataFrame:
    return pd.DataFrame({
        "Item": SETS[set_key],
        "Risposta": [None] * len(SETS[set_key]),
    })


# ─────────────────────────────────────────
#  CALLBACKS (eseguiti PRIMA del rerun)
# ─────────────────────────────────────────

def _on_calcola():
    """Legge le risposte da session_state, calcola lo scoring."""
    dn = st.session_state.get("sc_dn")
    ds = st.session_state.get("sc_ds")
    if dn and ds and dn > ds:
        st.session_state["calc_error"] = "❌ Correggi le date prima di calcolare: la data di nascita non può essere successiva alla data di somministrazione."
        st.session_state.pop("last_result", None)
        st.session_state.pop("last_responses", None)
        return

    # Leggi risposte dalla tabella dati (st.data_editor)
    responses = {}
    for set_key in ["A", "Ab", "B"]:
        values_key = f"resp_values_{set_key}"
        df = st.session_state.get(values_key, _build_editor_dataframe(set_key))
        for _, row in df.iterrows():
            item = row["Item"]
            val = row["Risposta"]
            if pd.notna(val) and val != "" and str(val).strip() not in ("–", ""):
                try:
                    responses[item] = int(val)
                except (ValueError, TypeError):
                    responses[item] = None
            else:
                responses[item] = None

    if all(v is None for v in responses.values()):
        st.session_state["calc_error"] = "⚠️ Non è stata inserita nessuna risposta. Compila almeno un item."
        return

    st.session_state.pop("calc_error", None)

    # Calcola età
    eta, eta_band = None, ""
    if dn and ds:
        eta = ds.year - dn.year
        if (ds.month, ds.day) < (dn.month, dn.day):
            eta -= 1
        eta_band = age_to_band(eta)

    result = score_with_norms(responses, age=eta, age_band=eta_band)
    result.nome = st.session_state.get("sc_nome", "")
    result.cognome = st.session_state.get("sc_cognome", "")
    result.data_nascita = dn
    result.data_somministrazione = ds
    result.sesso = st.session_state.get("sc_sex", "")
    result.esaminatore = st.session_state.get("sc_exam", "")
    result.note = st.session_state.get("sc_note", "")

    st.session_state["last_result"] = result
    st.session_state["last_responses"] = dict(responses)
    st.session_state.pop("save_msg", None)


def _on_salva():
    """Salva il risultato corrente nel database."""
    if "last_result" not in st.session_state:
        return
    result: ScoringResult = st.session_state["last_result"]
    result.note = st.session_state.get("sc_note", "")
    resps = st.session_state.get("last_responses", {})
    rec_id = save_result(result, resps)
    st.session_state["save_msg"] = f"Salvato nel database (ID: {rec_id})"


def _on_reset():
    """Pulisce lo stato per un nuovo soggetto."""
    # Pulisci risultati e messaggi
    for key in ["last_result", "last_responses", "save_msg", "calc_error"]:
        st.session_state.pop(key, None)
    # Pulisci i dataframe del data_editor (forza ricreazione)
    for set_key in ["A", "Ab", "B"]:
        st.session_state.pop(f"resp_editor_{set_key}", None)
        st.session_state.pop(f"resp_values_{set_key}", None)
    # Pulisci anagrafica
    for key in ["sc_nome", "sc_cognome", "sc_dn", "sc_ds", "sc_sex", "sc_exam", "sc_note"]:
        st.session_state.pop(key, None)
    # Incrementa il reset counter per forzare la rigenerazione dei widget
    st.session_state["_reset_counter"] = st.session_state.get("_reset_counter", 0) + 1


# ─────────────────────────────────────────
#  PAGINA
# ─────────────────────────────────────────

st.header("📝 Scoring Singolo Soggetto")
st.caption("Inserisci i dati del soggetto e le risposte ai 36 item, poi premi **Calcola**.")

with st.expander("ℹ️ Come usare questa pagina", expanded=False):
    st.markdown(
        """
        1. Compila i dati del soggetto.
        2. Inserisci le risposte nelle tre griglie Set A, Ab e B.
        3. Premi **Calcola Score** per ottenere punteggi, percentile e grafici.
        4. Se il risultato va conservato, usa **Salva nel Database**.

        Nota: se mancano date valide, il percentile può non essere disponibile.
        """
    )

if is_using_placeholder():
    st.warning(
        "⚠️ Le norme in uso sono **placeholder di esempio**. "
        "Carica le norme reali dalla pagina **📏 Norme** prima dell'uso clinico.",
        icon="⚠️",
    )



# ─────────────────────────────────────────
#  ANAGRAFICA
# ─────────────────────────────────────────
with st.expander("👤 Dati del Soggetto", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nome", key="sc_nome")
        st.text_input("Cognome", key="sc_cognome")
    with c2:
        st.date_input(
            "Data di nascita",
            value=None,
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY",
            key="sc_dn",
        )
        st.date_input(
            "Data somministrazione",
            value=date.today(),
            format="DD/MM/YYYY",
            key="sc_ds",
        )
    with c3:
        st.selectbox("Sesso", ["", "M", "F", "Altro"], key="sc_sex")
        st.text_input("Esaminatore", key="sc_exam")

    data_nascita = st.session_state.get("sc_dn")
    data_somm = st.session_state.get("sc_ds")
    eta = None
    eta_band = ""
    if data_nascita and data_somm:
        delta = data_somm.year - data_nascita.year
        if (data_somm.month, data_somm.day) < (data_nascita.month, data_nascita.day):
            delta -= 1
        eta = delta
        eta_band = age_to_band(eta)

    # Validazione date
    if data_nascita and data_somm and data_nascita > data_somm:
        st.error("❌ La data di nascita non può essere successiva alla data di somministrazione.")
        eta = None
        eta_band = ""
    elif eta is not None and eta < 0:
        st.error("❌ L'età calcolata è negativa. Controllare le date inserite.")
        eta = None
        eta_band = ""

    if eta is not None:
        col_eta1, col_eta2, _ = st.columns([1, 1, 2])
        with col_eta1:
            st.metric("Età (anni)", eta)
        with col_eta2:
            st.metric("Fascia normativa", eta_band if eta_band else "Non disponibile")

# ─────────────────────────────────────────
#  GRIGLIA RISPOSTE (data_editor)
# ─────────────────────────────────────────
st.subheader("📋 Risposte ai 36 Item")
st.caption(
    "Per ogni item inserisci il numero della risposta scelta dal soggetto (1–6). "
    "Lascia vuoto se l'item non è stato risposto. "
    "Usa **Tab** per spostarti rapidamente tra le celle."
)

set_configs = [
    ("Set A", "A", "#D6EAF8"),
    ("Set Ab", "Ab", "#FAD7A0"),
    ("Set B", "B", "#D5F5E3"),
]

col_a, col_sep1, col_ab, col_sep2, col_b = st.columns([4, 0.3, 4, 0.3, 4])
columns_ui = [col_a, col_ab, col_b]

for col_ui, (set_label, set_key, color) in zip(columns_ui, set_configs):
    with col_ui:
        st.markdown(
            f'<div style="background:{color}; padding:0.5rem; border-radius:8px; '
            f'text-align:center; font-weight:bold; font-size:1.1rem; margin-bottom:0.5rem;">'
            f'{set_label}</div>',
            unsafe_allow_html=True,
        )
        # Costruisci il DataFrame per il data_editor
        df_data = st.session_state.get(f"resp_values_{set_key}", _build_editor_dataframe(set_key))
        edited_df = st.data_editor(
            df_data,
            key=f"resp_editor_{set_key}",
            column_config={
                "Item": st.column_config.TextColumn(
                    "Item", disabled=True, width="small",
                ),
                "Risposta": st.column_config.SelectboxColumn(
                    "Risposta (1–6)",
                    options=[1, 2, 3, 4, 5, 6],
                    width="small",
                ),
            },
            hide_index=True,
            width="stretch",
            num_rows="fixed",
        )
        st.session_state[f"resp_values_{set_key}"] = edited_df.copy()

# ─────────────────────────────────────────
#  BARRA AZIONI
# ─────────────────────────────────────────
st.divider()

# Contatore item compilati
answered = 0
for set_key in ["A", "Ab", "B"]:
    values_key = f"resp_values_{set_key}"
    if values_key in st.session_state:
        df_state = st.session_state[values_key]
        for _, row in df_state.iterrows():
            val = row.get("Risposta")
            if pd.notna(val) and str(val).strip() not in ("", "–"):
                answered += 1
st.caption(f"Item compilati: **{answered}** / 36")

st.text_area(
    "📝 Note / Osservazioni (opzionale)",
    key="sc_note",
    placeholder="Aggiungi eventuali note sul soggetto o la somministrazione...",
)

has_result = "last_result" in st.session_state
has_invalid_dates = bool(data_nascita and data_somm and data_nascita > data_somm)

btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
with btn_col1:
    st.button(
        "🧮 Calcola Score", type="primary", width="stretch",
        key="btn_calcola", on_click=_on_calcola, disabled=has_invalid_dates,
    )
with btn_col2:
    st.button(
        "💾 Salva nel Database", width="stretch",
        key="btn_salva", on_click=_on_salva, disabled=not has_result or has_invalid_dates,
    )
with btn_col3:
    st.button(
        "🔄 Nuovo Soggetto", width="stretch",
        key="btn_reset", on_click=_on_reset,
    )
with btn_col4:
    pdf_slot = st.empty()

# ─────────────────────────────────────────
#  MESSAGGI
# ─────────────────────────────────────────
if st.session_state.get("calc_error"):
    st.warning(st.session_state["calc_error"])

if "save_msg" in st.session_state:
    st.toast(st.session_state["save_msg"], icon="✅")
    st.success(f"✅ {st.session_state['save_msg']}")

# ─────────────────────────────────────────
#  RISULTATI
# ─────────────────────────────────────────
if "last_result" in st.session_state:
    result: ScoringResult = st.session_state["last_result"]

    st.divider()
    st.subheader("🎯 Risultati")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Set A", f"{result.set_a_score} / 12")
    r2.metric("Set Ab", f"{result.set_ab_score} / 12")
    r3.metric("Set B", f"{result.set_b_score} / 12")
    r4.metric("TOTALE", f"{result.total_raw} / 36")

    if result.age_band:
        p1, p2 = st.columns(2)
        with p1:
            st.metric("Percentile", result.percentile)
        with p2:
            st.metric("Descrizione", result.description)
    else:
        st.info(
            "ℹ️ Inserisci le date di nascita e somministrazione per ottenere "
            "il percentile e la classificazione qualitativa."
        )

    # Indice di discrepanza tra set
    if result.discrepancy_flag == "significativa":
        st.error(
            f"⚠️ **Discrepanza significativa tra i set** (Δ = {result.discrepancy}). "
            "Il profilo presenta una differenza marcata tra le prestazioni nei diversi set. "
            "Si consiglia un approfondimento clinico.",
            icon="🔴",
        )
    elif result.discrepancy_flag == "attenzione":
        st.warning(
            f"⚠️ **Discrepanza da monitorare** (Δ = {result.discrepancy}). "
            "La differenza tra i set è lievemente elevata.",
            icon="🟡",
        )

    # ── GRAFICI ─────────────────────────
    st.divider()
    st.subheader("📊 Grafici")

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(bar_chart_sets(result), width="stretch")
    with g2:
        st.plotly_chart(radar_chart(result), width="stretch")

    g3, g4 = st.columns(2)
    with g3:
        if result.age_band:
            st.plotly_chart(percentile_gauge(result.percentile),
                            width="stretch")
        else:
            st.caption("Gauge percentile non disponibile (manca la fascia d'età).")
    with g4:
        st.plotly_chart(item_heatmap(result), width="stretch")

    # ── PDF download ────────────────────
    try:
        chart_imgs = {}
        try:
            chart_imgs["bar_sets"] = bar_chart_sets(result).to_image(
                format="png", width=800, height=350, scale=2)
            chart_imgs["heatmap"] = item_heatmap(result).to_image(
                format="png", width=800, height=250, scale=2)
            if result.age_band:
                chart_imgs["gauge"] = percentile_gauge(result.percentile).to_image(
                    format="png", width=600, height=280, scale=2)
        except Exception:
            chart_imgs = None

        pdf_bytes = generate_pdf(result, chart_imgs)
        fn = f"CPM_Report_{result.cognome}_{result.nome}.pdf" if result.cognome else "CPM_Report.pdf"
        pdf_slot.download_button(
            "📄 Scarica PDF",
            data=pdf_bytes,
            file_name=fn,
            mime="application/pdf",
            width="stretch",
            key="btn_pdf",
        )
    except Exception as e:
        pdf_slot.caption(f"⚠️ PDF: {e}")
else:
    st.info("👆 Compila le risposte e premi **Calcola Score** per vedere i risultati.")
