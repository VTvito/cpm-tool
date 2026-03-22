"""
Pagina 1 – Scoring Singolo Soggetto

ARCHITETTURA: usiamo on_click callbacks per mutare session_state PRIMA
che la pagina si ri-esegua, garantendo che pulsanti come "Salva" vedano
lo stato aggiornato al momento del rendering.
"""

import io
import streamlit as st
import pandas as pd
from datetime import date

from core.answer_key import SETS
from core.scoring import score_with_norms, ScoringResult, normalize_response
from core.norms import age_to_band, compute_age
from core.charts import bar_chart_sets, radar_chart, percentile_gauge, item_heatmap
from core.pdf_report import generate_pdf
from core.database import save_result
from streamlit_ui import configure_page

configure_page("Scoring Singolo", "📝")

RESPONSE_ITEMS = [*SETS["A"], *SETS["Ab"], *SETS["B"]]


def _response_key(item: str) -> str:
    return f"sc_resp_{item}"


def _collect_responses() -> dict[str, int | None]:
    return {
        item: normalize_response(st.session_state.get(_response_key(item)))
        for item in RESPONSE_ITEMS
    }


def _filled_response_count() -> int:
    return sum(
        normalize_response(st.session_state.get(_response_key(item))) is not None
        for item in RESPONSE_ITEMS
    )


def _render_set_inputs(set_label: str, set_key: str):
    with st.container(border=True):
        st.markdown(f'<div class="cpm-set-title">{set_label}</div>', unsafe_allow_html=True)
        items = SETS[set_key]
        for row_start in range(0, len(items), 4):
            row_items = items[row_start:row_start + 4]
            row_cols = st.columns(4, gap="small")
            for col_ui, item in zip(row_cols, row_items):
                with col_ui:
                    st.markdown(f'<div class="cpm-item-label">{item}</div>', unsafe_allow_html=True)
                    st.text_input(
                        f"Risposta {item}",
                        key=_response_key(item),
                        max_chars=1,
                        placeholder="1-6",
                        label_visibility="collapsed",
                    )


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

    responses = _collect_responses()

    if all(v is None for v in responses.values()):
        st.session_state["calc_error"] = "⚠️ Non è stata inserita nessuna risposta. Compila almeno un item."
        return

    # Controlla valori fuori range 1–6 — solo avviso, la logica di scoring non cambia
    out_of_range = [
        f"{item}='{st.session_state.get(_response_key(item), '').strip()}'"
        for item in RESPONSE_ITEMS
        if str(st.session_state.get(_response_key(item), "")).strip().isdigit()
        and int(st.session_state.get(_response_key(item), "0").strip()) > 6
    ]
    if out_of_range:
        st.session_state["resp_range_warning"] = (
            f"⚠️ Valori fuori range ignorati (attesi 1–6): {', '.join(out_of_range)}. "
            "Le risposte non valide sono trattate come mancanti."
        )
    else:
        st.session_state.pop("resp_range_warning", None)

    st.session_state.pop("calc_error", None)

    # Calcola età
    eta_anni, eta_mesi, eta_band = None, 0, ""
    if dn and ds:
        eta_anni, eta_mesi = compute_age(dn, ds)
        eta_band = age_to_band(eta_anni, eta_mesi)

    result = score_with_norms(responses, age_years=eta_anni, age_months=eta_mesi, age_band=eta_band)
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
    for key in ["last_result", "last_responses", "save_msg", "calc_error", "resp_range_warning"]:
        st.session_state.pop(key, None)
    for item in RESPONSE_ITEMS:
        st.session_state.pop(_response_key(item), None)
    # Pulisci anagrafica
    for key in ["sc_nome", "sc_cognome", "sc_dn", "sc_ds", "sc_sex", "sc_exam", "sc_note"]:
        st.session_state.pop(key, None)
    # Incrementa il reset counter per forzare la rigenerazione dei widget
    st.session_state["_reset_counter"] = st.session_state.get("_reset_counter", 0) + 1


# ─────────────────────────────────────────
#  PAGINA
# ─────────────────────────────────────────

st.header("📝 Scoring Singolo Soggetto")
st.caption("Compila anagrafica e risposte, poi premi **Calcola Score**.")



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
        st.caption("Serve per calcolare età e percentile nella fascia corretta.")
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
    eta_anni = None
    eta_mesi = 0
    eta_band = ""
    if data_nascita and data_somm:
        eta_anni, eta_mesi = compute_age(data_nascita, data_somm)
        eta_band = age_to_band(eta_anni, eta_mesi)

    # Validazione date
    if data_nascita and data_somm and data_nascita > data_somm:
        st.error("❌ La data di nascita non può essere successiva alla data di somministrazione.")
        eta_anni = None
        eta_band = ""
    elif eta_anni is not None and eta_anni < 0:
        st.error("❌ L'età calcolata è negativa. Controllare le date inserite.")
        eta_anni = None
        eta_band = ""

    if eta_anni is not None:
        col_eta1, col_eta2, _ = st.columns([1, 1, 2])
        with col_eta1:
            st.metric("Età (anni;mesi)", f"{eta_anni};{eta_mesi}")
        with col_eta2:
            st.metric("Fascia normativa", eta_band if eta_band else "Non disponibile")

# ─────────────────────────────────────────
#  GRIGLIA RISPOSTE
# ─────────────────────────────────────────
st.subheader("📋 Risposte ai 36 Item")
st.markdown(
    '<div class="cpm-response-help">'
    'Digita un valore da 1 a 6. Usa <span class="cpm-kbd">Tab</span> per avanzare e '
    '<span class="cpm-kbd">Shift</span> + <span class="cpm-kbd">Tab</span> per tornare indietro. '
    'Il calcolo parte solo quando premi Calcola Score, cosi la compilazione resta fluida.'
    '</div>',
    unsafe_allow_html=True,
)

set_configs = [("Set A", "A"), ("Set Ab", "Ab"), ("Set B", "B")]

has_invalid_dates = bool(data_nascita and data_somm and data_nascita > data_somm)

with st.form("scoring_response_form", clear_on_submit=False):
    col_a, col_ab, col_b = st.columns(3)
    for col_ui, (set_label, set_key) in zip([col_a, col_ab, col_b], set_configs):
        with col_ui:
            _render_set_inputs(set_label, set_key)

    st.form_submit_button(
        "🧮 Calcola Score",
        type="primary",
        on_click=_on_calcola,
        disabled=has_invalid_dates,
        width="stretch",
    )

# ─────────────────────────────────────────
#  BARRA AZIONI
# ─────────────────────────────────────────
st.divider()

st.markdown(
    f'<div class="cpm-scoring-toolbar">Item compilati: <strong>{_filled_response_count()}</strong> / 36</div>',
    unsafe_allow_html=True,
)

with st.expander("📝 Note / Osservazioni opzionali", expanded=False):
    st.text_area(
        "Note cliniche o di somministrazione",
        key="sc_note",
        placeholder="Aggiungi eventuali note sul soggetto o la somministrazione...",
    )

has_result = "last_result" in st.session_state

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    st.button(
        "💾 Salva nel Database", width="stretch",
        key="btn_salva", on_click=_on_salva, disabled=not has_result or has_invalid_dates,
    )
with btn_col2:
    st.button(
        "🔄 Nuovo Soggetto", width="stretch",
        key="btn_reset", on_click=_on_reset,
    )

# ─────────────────────────────────────────
#  MESSAGGI
# ─────────────────────────────────────────
if st.session_state.get("calc_error"):
    st.warning(st.session_state["calc_error"])

if st.session_state.get("resp_range_warning"):
    st.warning(st.session_state["resp_range_warning"])

if "save_msg" in st.session_state:
    st.toast(st.session_state["save_msg"], icon="✅")
    st.caption(st.session_state["save_msg"])

# ─────────────────────────────────────────
#  RISULTATI
# ─────────────────────────────────────────
if "last_result" in st.session_state:
    result: ScoringResult = st.session_state["last_result"]

    st.divider()
    st.subheader("🎯 Risultati")

    summary_bits = [f"Totale {result.total_raw}/36"]
    if result.age_band:
        summary_bits.append(f"fascia {result.age_band}")
        summary_bits.append(f"percentile {result.percentile}")
    if result.discrepancy_flag:
        summary_bits.append(f"discrepanza {result.discrepancy_flag}")
    else:
        summary_bits.append("discrepanza assente o nei limiti")
    st.info("Risultato principale: " + " • ".join(summary_bits))

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
        st.caption("Inserisci le date di nascita e somministrazione per il percentile.")

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
    # ── GRAFICI PRINCIPALI ──────────────
    st.divider()

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(bar_chart_sets(result), width="stretch")
    with g2:
        st.plotly_chart(item_heatmap(result), width="stretch")

    with st.expander("📈 Approfondimento grafico", expanded=False):
        g3, g4 = st.columns(2)
        with g3:
            st.plotly_chart(radar_chart(result), width="stretch")
        with g4:
            if result.age_band:
                st.plotly_chart(percentile_gauge(result.percentile), width="stretch")
            else:
                st.caption("Gauge percentile non disponibile (manca la fascia d'età).")

    # ── PDF download ────────────────────
    try:
        pdf_bytes = generate_pdf(result)
        fn = f"CPM_Report_{result.cognome}_{result.nome}.pdf" if result.cognome else "CPM_Report.pdf"
        st.download_button(
            "📄 Scarica PDF",
            data=pdf_bytes,
            file_name=fn,
            mime="application/pdf",
            width="stretch",
            key="btn_pdf",
        )
    except Exception as e:
        st.warning(f"PDF non disponibile: {e}")

    # ── Export dati (CSV / Excel / anonimizzato) ─────
    st.divider()
    st.subheader("📥 Esporta Risultato")

    row_data = {
        "Nome": result.nome,
        "Cognome": result.cognome,
        "Fascia Età": result.age_band,
        "Set A": result.set_a_score,
        "Set Ab": result.set_ab_score,
        "Set B": result.set_b_score,
        "Totale": result.total_raw,
        "Percentile": result.percentile,
        "Descrizione": result.description,
        "Discrepanza": result.discrepancy,
        "Flag": result.discrepancy_flag,
    }
    export_df = pd.DataFrame([row_data])
    anon_df = export_df.copy()
    anon_df["Nome"] = "S001"
    anon_df["Cognome"] = ""

    exp_c1, exp_c2 = st.columns(2)
    with exp_c1:
        csv_out = export_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Scarica CSV",
            data=csv_out,
            file_name="CPM_Risultato_Singolo.csv",
            mime="text/csv",
            width="stretch",
            key="btn_exp_csv",
        )
    with exp_c2:
        buf_xl = io.BytesIO()
        with pd.ExcelWriter(buf_xl, engine="openpyxl") as w:
            export_df.to_excel(w, index=False, sheet_name="Risultato")
        st.download_button(
            "⬇️ Scarica Excel",
            data=buf_xl.getvalue(),
            file_name="CPM_Risultato_Singolo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            key="btn_exp_xlsx",
        )

    anon_c1, anon_c2 = st.columns(2)
    with anon_c1:
        csv_anon = anon_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "🔒 Anonimizzato (CSV)",
            data=csv_anon,
            file_name="CPM_Risultato_Anonimo.csv",
            mime="text/csv",
            width="stretch",
            key="btn_anon_csv",
            help="Nome sostituito da codice S001.",
        )
    with anon_c2:
        buf_anon = io.BytesIO()
        with pd.ExcelWriter(buf_anon, engine="openpyxl") as w:
            anon_df.to_excel(w, index=False, sheet_name="Risultato Anonimo")
        st.download_button(
            "🔒 Anonimizzato (Excel)",
            data=buf_anon.getvalue(),
            file_name="CPM_Risultato_Anonimo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            key="btn_anon_xlsx",
            help="Nome sostituito da codice S001.",
        )
