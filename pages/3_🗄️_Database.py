"""
Pagina 3 – Database Soggetti

Visualizza, filtra, esporta e gestisci i risultati salvati.
"""

import io
from pathlib import Path
import streamlit as st
import pandas as pd

from core.database import get_all_subjects, delete_subject, subject_to_result, init_db, DB_PATH
from streamlit_ui import configure_page


configure_page("Database Soggetti", "🗄️")

init_db()


def _on_delete_subject():
    del_id = st.session_state.get("db_del_id")
    if not del_id:
        return

    delete_subject(int(del_id))
    st.session_state["db_delete_msg"] = f"Record ID {del_id} eliminato."
    st.session_state["db_del_id"] = ""


def _on_restore_upload_change():
    for key in ["db_restore_msg", "db_restore_error"]:
        st.session_state.pop(key, None)


def _validate_restore_bytes(restore_bytes: bytes) -> str | None:
    import sqlite3 as _sqlite3
    import tempfile as _tempfile

    tmp_path = None
    try:
        with _tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp.write(restore_bytes)
            tmp_path = tmp.name
        conn = _sqlite3.connect(tmp_path)
        try:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
        finally:
            conn.close()
        if "subjects" not in tables:
            return "❌ Il file caricato non contiene la tabella 'subjects'. Non è un backup valido."
        return None
    except Exception:
        return "❌ Il file caricato non è un database SQLite valido."
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def _on_restore_database():
    restore_file = st.session_state.get("db_restore_upload")
    if restore_file is None:
        return

    restore_bytes = restore_file.getvalue()
    error_message = _validate_restore_bytes(restore_bytes)
    if error_message:
        st.session_state["db_restore_error"] = error_message
        st.session_state.pop("db_restore_msg", None)
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_bytes(restore_bytes)
    st.session_state["db_restore_msg"] = "✅ Database ripristinato dal backup! Ricarica la pagina per vedere i dati aggiornati."
    st.session_state.pop("db_restore_error", None)

st.header("🗄️ Database Soggetti")
st.caption("Risultati salvati dalle sessioni di scoring.")

# ─────────────────────────────────────────
#  CARICAMENTO DATI
# ─────────────────────────────────────────
subjects = get_all_subjects()

if "db_delete_msg" in st.session_state:
    st.toast(st.session_state["db_delete_msg"], icon="🗑️")
    st.success(f"✅ {st.session_state['db_delete_msg']}")
    st.session_state.pop("db_delete_msg", None)

if not subjects:
    st.info(
        "📭 Il database è vuoto. "
        "Salva dei risultati dalla pagina **Scoring** o **Batch** per vederli qui."
    )
    st.stop()

df = pd.DataFrame(subjects)

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Record salvati", len(df))
metric_col2.metric("Media totale", round(df["total_raw"].mean(), 1) if not df.empty else 0)
metric_col3.metric("Ultimo inserimento", df.iloc[0]["created_at"][:10] if not df.empty and df.iloc[0]["created_at"] else "-")

# Rinomina colonne per leggibilità
col_rename = {
    "id": "ID",
    "nome": "Nome",
    "cognome": "Cognome",
    "data_nascita": "Data Nascita",
    "data_somm": "Data Somm.",
    "sesso": "Sesso",
    "esaminatore": "Esaminatore",
    "eta_band": "Fascia Età",
    "score_a": "Set A",
    "score_ab": "Set Ab",
    "score_b": "Set B",
    "total_raw": "Totale",
    "percentile": "Percentile",
    "descrizione": "Descrizione",
    "note": "Note",
    "created_at": "Data Inserimento",
}
df_display = df.rename(columns=col_rename)
# Rimuovi colonna risposte JSON dalla vista
if "risposte" in df_display.columns:
    df_display = df_display.drop(columns=["risposte"])

# ─────────────────────────────────────────
#  RICERCA E FILTRI
# ─────────────────────────────────────────
# Ricerca per nome/cognome
search_text = st.text_input(
    "🔍 Cerca per nome o cognome",
    key="db_search",
    placeholder="Es: Rossi, Marco, ...",
)
if search_text:
    search_lower = search_text.lower()
    df_display = df_display[
        df_display["Nome"].astype(str).str.lower().str.contains(search_lower, na=False, regex=False) |
        df_display["Cognome"].astype(str).str.lower().str.contains(search_lower, na=False, regex=False)
    ]

with st.expander("🔍 Filtri avanzati", expanded=False):
    f1, f2, f3 = st.columns(3)

    with f1:
        filter_exam = st.multiselect(
            "Esaminatore",
            options=sorted(df_display["Esaminatore"].dropna().unique()),
            key="db_filt_exam",
        )
    with f2:
        filter_band = st.multiselect(
            "Fascia Età",
            options=sorted(df_display["Fascia Età"].dropna().unique()),
            key="db_filt_band",
        )
    with f3:
        filter_total = st.slider(
            "Range Punteggio Totale",
            min_value=0, max_value=36,
            value=(0, 36),
            key="db_filt_total",
        )

    if filter_exam:
        df_display = df_display[df_display["Esaminatore"].isin(filter_exam)]
    if filter_band:
        df_display = df_display[df_display["Fascia Età"].isin(filter_band)]
    df_display = df_display[
        (df_display["Totale"] >= filter_total[0]) &
        (df_display["Totale"] <= filter_total[1])
    ]

st.markdown(f"**{len(df_display)}** soggetti trovati")

# ─────────────────────────────────────────
#  TABELLA
# ─────────────────────────────────────────
display_cols = ["ID", "Cognome", "Nome", "Fascia Età", "Totale",
                "Percentile", "Descrizione", "Data Inserimento"]
available = [c for c in display_cols if c in df_display.columns]

st.dataframe(
    df_display[available],
    width="stretch",
    height=min(500, 50 + 35 * len(df_display)),
    column_config={
        "Totale": st.column_config.ProgressColumn(
            "Totale", min_value=0, max_value=36, format="%d/36"),
        "Descrizione": st.column_config.TextColumn("Descrizione", width="large"),
        "Data Inserimento": st.column_config.TextColumn("Data Inserimento", width="medium"),
    },
)

with st.expander("📄 Mostra colonne aggiuntive", expanded=False):
    extra_cols = [
        c for c in ["Data Nascita", "Data Somm.", "Sesso", "Esaminatore",
                    "Set A", "Set Ab", "Set B", "Note"]
        if c in df_display.columns
    ]
    if extra_cols:
        st.dataframe(
            df_display[["ID", "Cognome", "Nome", *extra_cols]],
            width="stretch",
            height=min(400, 50 + 35 * len(df_display)),
            column_config={
                "Set A": st.column_config.ProgressColumn(
                    "Set A", min_value=0, max_value=12, format="%d/12"),
                "Set Ab": st.column_config.ProgressColumn(
                    "Set Ab", min_value=0, max_value=12, format="%d/12"),
                "Set B": st.column_config.ProgressColumn(
                    "Set B", min_value=0, max_value=12, format="%d/12"),
                "Esaminatore": st.column_config.TextColumn("Esaminatore", width="medium"),
                "Note": st.column_config.TextColumn("Note", width="large"),
            },
        )

# ─────────────────────────────────────────
#  STATISTICHE
# ─────────────────────────────────────────
with st.expander("📈 Statistiche Descrittive", expanded=False):
    numeric_cols = ["Set A", "Set Ab", "Set B", "Totale"]
    avail_num = [c for c in numeric_cols if c in df_display.columns]
    if avail_num:
        st.dataframe(
            df_display[avail_num].describe().round(2),
            width="stretch",
        )

st.divider()

# ─────────────────────────────────────────
#  EXPORT
# ─────────────────────────────────────────
st.subheader("📥 Esporta Dati")

# Helper: costruisce il DataFrame anonimizzato (riusato per CSV ed Excel)
def _anon_df(src: pd.DataFrame) -> pd.DataFrame:
    df_a = src.copy()
    if "Nome" in df_a.columns:
        df_a["Nome"] = [f"S{i+1:03d}" for i in range(len(df_a))]
    if "Cognome" in df_a.columns:
        df_a["Cognome"] = ""
    if "Esaminatore" in df_a.columns:
        df_a["Esaminatore"] = "–"
    if "Note" in df_a.columns:
        df_a["Note"] = ""
    return df_a

_anon_help = (
    "Esporta i dati con codici soggetto (S001, S002, ...) al posto dei nomi. "
    "Utile per condivisione dati nel rispetto della privacy."
)

# ── Riga 1: export completo ──────────────
row1_c1, row1_c2 = st.columns(2)

with row1_c1:
    csv_data = df_display[available].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Scarica CSV",
        data=csv_data,
        file_name="CPM_Database.csv",
        mime="text/csv",
        width="stretch",
    )

with row1_c2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_display[available].to_excel(writer, index=False, sheet_name="Database CPM")
    st.download_button(
        "⬇️ Scarica Excel",
        data=buf.getvalue(),
        file_name="CPM_Database.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

# ── Riga 2: export anonimizzato ──────────
row2_c1, row2_c2 = st.columns(2)

with row2_c1:
    csv_anon = _anon_df(df_display[available]).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "🔒 Anonimizzato (CSV)",
        data=csv_anon,
        file_name="CPM_Database_Anonimo.csv",
        mime="text/csv",
        width="stretch",
        help=_anon_help,
    )

with row2_c2:
    buf_anon = io.BytesIO()
    with pd.ExcelWriter(buf_anon, engine="openpyxl") as writer:
        _anon_df(df_display[available]).to_excel(writer, index=False, sheet_name="Database CPM Anonimo")
    st.download_button(
        "🔒 Anonimizzato (Excel)",
        data=buf_anon.getvalue(),
        file_name="CPM_Database_Anonimo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        help=_anon_help,
    )

# ─────────────────────────────────────────
#  ELIMINAZIONE
# ─────────────────────────────────────────
st.divider()
with st.expander("🛠️ Operazioni avanzate", expanded=False):
    st.markdown("Le azioni seguenti sono utili per manutenzione o correzioni puntuali del database.")

    st.markdown("#### 🗑️ Elimina un Record")
    st.warning("⚠️ L'eliminazione è permanente e non può essere annullata.")
    ids_available = df_display["ID"].tolist() if "ID" in df_display.columns else []
    del_id = st.selectbox(
        "Seleziona ID da eliminare",
        options=[""] + [str(i) for i in ids_available],
        key="db_del_id",
    )
    st.button(
        "🗑️ Conferma Eliminazione",
        type="secondary",
        key="db_btn_delete",
        on_click=_on_delete_subject,
        disabled=not del_id,
        width="stretch",
    )

    st.divider()
    st.markdown("#### 💾 Backup e Ripristino Database")

    bk_col1, bk_col2 = st.columns(2)
    with bk_col1:
        st.markdown("**Scarica una copia di backup** del database per sicurezza.")
        if DB_PATH.is_file():
            st.download_button(
                "⬇️ Scarica Backup Database",
                data=DB_PATH.read_bytes(),
                file_name="CPM_Database_Backup.db",
                mime="application/octet-stream",
                width="stretch",
            )

    with bk_col2:
        st.markdown("**Ripristina** un backup precedente (sovrascrive i dati attuali).")
        restore_file = st.file_uploader(
            "Carica file .db di backup",
            type=["db"],
            key="db_restore_upload",
            on_change=_on_restore_upload_change,
        )
        st.button(
            "⚠️ Ripristina Database da Backup",
            type="secondary",
            key="db_btn_restore",
            width="stretch",
            on_click=_on_restore_database,
            disabled=restore_file is None,
        )
        if st.session_state.get("db_restore_error"):
            st.error(st.session_state["db_restore_error"])
        if st.session_state.get("db_restore_msg"):
            st.success(st.session_state["db_restore_msg"])
