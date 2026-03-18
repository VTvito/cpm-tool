"""
Pagina 2 – Batch Scoring

Carica un file CSV o Excel con le risposte di più soggetti
e ottieni lo scoring automatico in blocco.
"""

import io
import streamlit as st
import pandas as pd

from core.answer_key import SETS, ANSWER_KEY
from core.scoring import score_with_norms, normalize_response
from core.database import save_result
from ui_shell import configure_page


configure_page("Batch Scoring", "📊")


MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


def _parse_batch_date(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day") and not isinstance(value, str):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if pd.notna(parsed):
            return parsed.date()

    parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _load_uploaded_dataframe(uploaded_file) -> pd.DataFrame:
    file_bytes = uploaded_file.getvalue()
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("File troppo grande. Limite massimo: 5 MB.")
    buffer = io.BytesIO(file_bytes)
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(buffer)
    else:
        df = pd.read_excel(buffer)

    df.columns = [str(col).strip() for col in df.columns]
    if df.empty:
        raise ValueError("Il file caricato non contiene righe dati.")
    return df


def _build_batch_results(df: pd.DataFrame, all_items: list[str]) -> tuple[list[tuple], pd.DataFrame]:
    results = []

    for _, row in df.iterrows():
        responses = {}
        for item in all_items:
            responses[item] = normalize_response(row.get(item))

        eta = None
        dn = _parse_batch_date(row.get("DataNascita"))
        ds = _parse_batch_date(row.get("DataSomministrazione"))
        if dn and ds:
            eta = ds.year - dn.year
            if (ds.month, ds.day) < (dn.month, dn.day):
                eta -= 1

        result = score_with_norms(responses, age=eta)
        result.nome = str(row.get("Nome", ""))
        result.cognome = str(row.get("Cognome", ""))
        result.sesso = str(row.get("Sesso", ""))
        result.esaminatore = str(row.get("Esaminatore", ""))

        result.data_nascita = dn
        result.data_somministrazione = ds

        results.append((result, responses))

    rows_out = []
    for result, _ in results:
        rows_out.append({
            "Nome": result.nome,
            "Cognome": result.cognome,
            "Fascia Età": result.age_band,
            "Set A": result.set_a_score,
            "Set Ab": result.set_ab_score,
            "Set B": result.set_b_score,
            "Totale": result.total_raw,
            "Percentile": result.percentile,
            "Descrizione": result.description,
        })

    return results, pd.DataFrame(rows_out)


def _on_batch_upload_change():
    for key in ["batch_results", "batch_results_df", "batch_error", "batch_save_msg"]:
        st.session_state.pop(key, None)


def _on_batch_calcola():
    uploaded_file = st.session_state.get("batch_uploaded")
    if uploaded_file is None:
        st.session_state["batch_error"] = "Carica prima un file CSV o Excel valido."
        return

    try:
        df = _load_uploaded_dataframe(uploaded_file)
    except Exception as exc:
        st.session_state["batch_error"] = f"Errore nella lettura del file: {exc}"
        st.session_state.pop("batch_results", None)
        st.session_state.pop("batch_results_df", None)
        return

    missing_items = [item for item in ALL_ITEMS if item not in df.columns]
    if missing_items:
        missing_text = ", ".join(missing_items[:10])
        suffix = " …" if len(missing_items) > 10 else ""
        st.session_state["batch_error"] = (
            f"Colonne mancanti nel file: {missing_text}{suffix}. Usa il template fornito."
        )
        st.session_state.pop("batch_results", None)
        st.session_state.pop("batch_results_df", None)
        return

    results, results_df = _build_batch_results(df, ALL_ITEMS)
    st.session_state["batch_results"] = results
    st.session_state["batch_results_df"] = results_df
    st.session_state.pop("batch_error", None)
    st.session_state.pop("batch_save_msg", None)


def _on_batch_save():
    results = st.session_state.get("batch_results", [])
    if not results:
        return

    count = 0
    for result, responses in results:
        save_result(result, responses)
        count += 1

    st.session_state["batch_save_msg"] = f"{count} soggetti salvati nel database!"

st.header("📊 Batch Scoring – Più Soggetti")
st.caption("Carica un file CSV o Excel con le risposte di più soggetti.")

# ─────────────────────────────────────────
#  TEMPLATE SCARICABILE
# ─────────────────────────────────────────
st.subheader("1️⃣  Scarica il Template")
st.caption("Ogni riga è un soggetto, ogni colonna un item (A1–B12). Non rinominare le colonne.")

all_items = []
for set_name in ["A", "Ab", "B"]:
    all_items.extend(SETS[set_name])
ALL_ITEMS = all_items

template_cols = ["Nome", "Cognome", "DataNascita", "DataSomministrazione",
                 "Sesso", "Esaminatore"] + all_items
template_df = pd.DataFrame(columns=template_cols)
# Aggiungi una riga di esempio
example_row = {
    "Nome": "Mario", "Cognome": "Rossi",
    "DataNascita": "15/05/2018", "DataSomministrazione": "18/03/2026",
    "Sesso": "M", "Esaminatore": "Dott.ssa Bianchi",
}
for item in all_items:
    example_row[item] = ANSWER_KEY[item]  # risposte tutte corrette come esempio
template_df = pd.concat([template_df, pd.DataFrame([example_row])], ignore_index=True)

csv_template = template_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Scarica Template CSV",
    data=csv_template,
    file_name="CPM_BatchTemplate.csv",
    mime="text/csv",
)

st.divider()

# ─────────────────────────────────────────
#  UPLOAD FILE
# ─────────────────────────────────────────
st.subheader("2️⃣  Carica il File Compilato")

uploaded = st.file_uploader(
    "Scegli un file CSV o Excel",
    type=["csv", "xlsx", "xls"],
    help="Il file deve avere le stesse colonne del template scaricato.",
    key="batch_uploaded",
    on_change=_on_batch_upload_change,
)

preview_df = None
upload_error = ""
missing_items = []

if uploaded is not None:
    try:
        preview_df = _load_uploaded_dataframe(uploaded)
    except Exception as e:
        upload_error = f"Errore nella lettura del file: {e}"

if upload_error:
    st.error(f"❌ {upload_error}")
elif preview_df is not None:
    st.success(f"✅ File caricato: **{len(preview_df)}** soggetti trovati.")
    checklist_col1, checklist_col2, checklist_col3 = st.columns(3)
    checklist_col1.success("File letto")
    checklist_col2.success(f"{len(preview_df)} righe trovate")

    # Anteprima
    with st.expander("👀 Anteprima dati caricati", expanded=False):
        st.dataframe(preview_df, width="stretch", height=300)

    # Verifica colonne item
    missing_items = [item for item in ALL_ITEMS if item not in preview_df.columns]
    if missing_items:
        checklist_col3.error("Colonne item mancanti")
        st.error(
            f"❌ Colonne mancanti nel file: **{', '.join(missing_items[:10])}**"
            + (" …" if len(missing_items) > 10 else "")
            + "\n\nAssicurati di usare il template fornito."
        )
    else:
        checklist_col3.success("Struttura file valida")

st.divider()

# ─────────────────────────────────────
#  SCORING
# ─────────────────────────────────────
st.subheader("3️⃣  Calcola Punteggi")

actions_col1, actions_col2 = st.columns(2)
with actions_col1:
    st.button(
        "🧮  Calcola Score per Tutti",
        type="primary",
        key="batch_btn_calcola",
        on_click=_on_batch_calcola,
        disabled=uploaded is None or bool(upload_error) or bool(missing_items),
        width="stretch",
    )
with actions_col2:
    st.button(
        "💾 Salva Tutti nel Database",
        key="batch_btn_salva",
        on_click=_on_batch_save,
        disabled=not st.session_state.get("batch_results"),
        width="stretch",
    )

if st.session_state.get("batch_error"):
    st.error(f"❌ {st.session_state['batch_error']}")

if st.session_state.get("batch_save_msg"):
    st.success(f"✅ {st.session_state['batch_save_msg']}")

results_df = st.session_state.get("batch_results_df")
if results_df is not None:
    # ── TABELLA RISULTATI ───────────
    st.subheader("📋 Risultati")

    st.dataframe(
        results_df,
        width="stretch",
        height=min(400, 50 + 35 * len(results_df)),
        column_config={
            "Set A": st.column_config.ProgressColumn(
                "Set A", min_value=0, max_value=12, format="%d/12"),
            "Set Ab": st.column_config.ProgressColumn(
                "Set Ab", min_value=0, max_value=12, format="%d/12"),
            "Set B": st.column_config.ProgressColumn(
                "Set B", min_value=0, max_value=12, format="%d/12"),
            "Totale": st.column_config.ProgressColumn(
                "Totale", min_value=0, max_value=36, format="%d/36"),
        },
    )

    # Statistiche
    with st.expander("📈 Statistiche Descrittive", expanded=False):
        st.dataframe(
            results_df[["Set A", "Set Ab", "Set B", "Totale"]].describe().round(2),
            width="stretch",
        )

    st.divider()

    # ── EXPORT ──────────────────────
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        csv_out = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Scarica Risultati (CSV)",
            data=csv_out,
            file_name="CPM_Risultati_Batch.csv",
            mime="text/csv",
            width="stretch",
        )

    with col_exp2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            results_df.to_excel(writer, index=False, sheet_name="Risultati")
        st.download_button(
            "⬇️ Scarica Risultati (Excel)",
            data=buf.getvalue(),
            file_name="CPM_Risultati_Batch.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
