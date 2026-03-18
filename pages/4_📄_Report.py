"""
Pagina 4 – Report PDF

Seleziona un soggetto dal database e genera un report PDF stampabile.
Supporto per generazione batch (ZIP con report multipli).
"""

import io
import re
import zipfile

import streamlit as st

from core.database import get_all_subjects, subject_to_result, init_db
from core.charts import bar_chart_sets, item_heatmap, percentile_gauge
from core.pdf_report import generate_pdf

init_db()


def _safe_report_filename(nome: str, cognome: str) -> str:
    raw_name = f"CPM_Report_{cognome}_{nome}".strip("_")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_name).strip("._")
    return f"{safe_name or 'CPM_Report'}.pdf"


def _display_value(value) -> str:
    return str(value) if value not in (None, "") else "–"


def _clear_report_pdf_state():
    for key in ["rpt_pdf_bytes", "rpt_pdf_name", "rpt_pdf_warning", "rpt_pdf_success"]:
        st.session_state.pop(key, None)


def _on_generate_report_pdf():
    selected_subject = st.session_state.get("rpt_selected_subject")
    if not selected_subject:
        return

    result = subject_to_result(selected_subject)
    result.note = st.session_state.get("rpt_note", "")

    chart_imgs = {}
    warning_message = ""
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
        warning_message = (
            "I grafici non sono stati inclusi nel PDF. "
            "Per includerli, installa il pacchetto `kaleido`: `pip install kaleido`"
        )

    pdf_bytes = generate_pdf(result, chart_imgs)
    filename = _safe_report_filename(result.nome, result.cognome)

    st.session_state["rpt_pdf_bytes"] = pdf_bytes
    st.session_state["rpt_pdf_name"] = filename
    st.session_state["rpt_pdf_warning"] = warning_message
    st.session_state["rpt_pdf_success"] = "Report generato con successo!"

st.header("📄 Genera Report PDF")
st.caption("Seleziona un soggetto dal database per generare un report PDF stampabile.")

with st.expander("ℹ️ Come usare questa pagina", expanded=False):
    st.markdown(
        """
        1. Seleziona un soggetto già salvato nel database.
        2. Controlla l'anteprima dei dati e dei risultati.
        3. Aggiungi eventuali note al report.
        4. Genera il PDF singolo oppure uno ZIP con tutti i report.

        Nota: se i grafici non entrano nel PDF, verifica che `kaleido` sia installato.
        """
    )

# ─────────────────────────────────────────
#  SELEZIONE SOGGETTO
# ─────────────────────────────────────────
subjects = get_all_subjects()

if not subjects:
    st.info(
        "📭 Nessun soggetto nel database. "
        "Salva dei risultati dalla pagina **Scoring** o **Batch** per generare i report."
    )
    st.stop()

# Crea lista leggibile
options = {}
for s in subjects:
    label = f"ID {s['id']} — {s.get('cognome', '')} {s.get('nome', '')} (Totale: {s.get('total_raw', '?')})"
    options[label] = s

selected_label = st.selectbox(
    "Seleziona soggetto",
    list(options.keys()),
    key="rpt_selected_label",
    on_change=_clear_report_pdf_state,
)
st.caption("Se il database cresce, usa cognome, nome e ID mostrati nell'elenco per individuare rapidamente il soggetto corretto.")
selected = options[selected_label]
st.session_state["rpt_selected_subject"] = selected
result = subject_to_result(selected)

# ─────────────────────────────────────────
#  ANTEPRIMA
# ─────────────────────────────────────────
st.divider()
st.subheader("👁️ Anteprima Report")

c1, c2 = st.columns(2)

with c1:
    st.markdown("##### 👤 Anagrafica")
    st.table([
        {"Campo": "Nome", "Valore": _display_value(result.nome)},
        {"Campo": "Cognome", "Valore": _display_value(result.cognome)},
        {"Campo": "Data nascita", "Valore": _display_value(result.data_nascita)},
        {"Campo": "Data somministrazione", "Valore": _display_value(result.data_somministrazione)},
        {"Campo": "Sesso", "Valore": _display_value(result.sesso)},
        {"Campo": "Esaminatore", "Valore": _display_value(result.esaminatore)},
        {"Campo": "Fascia età", "Valore": _display_value(result.age_band)},
    ])

with c2:
    st.markdown("##### 🎯 Risultati")
    r1, r2 = st.columns(2)
    r1.metric("Set A", f"{result.set_a_score}/12")
    r2.metric("Set Ab", f"{result.set_ab_score}/12")
    r3, r4 = st.columns(2)
    r3.metric("Set B", f"{result.set_b_score}/12")
    r4.metric("TOTALE", f"{result.total_raw}/36")
    st.metric("Percentile", f"{result.percentile} — {result.description}")

# Grafici anteprima
g1, g2 = st.columns(2)
with g1:
    st.plotly_chart(bar_chart_sets(result), width="stretch")
with g2:
    st.plotly_chart(item_heatmap(result), width="stretch")

# ─────────────────────────────────────────
#  GENERAZIONE PDF
# ─────────────────────────────────────────
st.divider()

note_extra = st.text_area(
    "📝 Note aggiuntive per il report",
    value=result.note,
    placeholder="Aggiungi eventuali note per il report PDF…",
    key="rpt_note",
    on_change=_clear_report_pdf_state,
)
st.caption("Queste note vengono aggiunte solo al PDF generato, non modificano automaticamente il record originale nel database.")
result.note = note_extra

st.markdown("")

st.button(
    "📄  Genera e Scarica PDF",
    type="primary",
    key="rpt_btn_generate",
    on_click=_on_generate_report_pdf,
    width="stretch",
)

if st.session_state.get("rpt_pdf_warning"):
    st.warning(f"⚠️ {st.session_state['rpt_pdf_warning']}")

if st.session_state.get("rpt_pdf_bytes"):
    st.download_button(
        "⬇️ Scarica il Report PDF",
        data=st.session_state["rpt_pdf_bytes"],
        file_name=st.session_state["rpt_pdf_name"],
        mime="application/pdf",
        width="stretch",
    )
    st.info("Prossimo passo: se devi archiviare o condividere più report, usa la sezione batch qui sotto.", icon="➡️")

if st.session_state.get("rpt_pdf_success"):
    st.success(f"✅ {st.session_state['rpt_pdf_success']}")

# ─────────────────────────────────────────
#  GENERAZIONE BATCH (ZIP multi-PDF)
# ─────────────────────────────────────────
st.divider()
with st.expander("📦 Operazioni batch", expanded=False):
    st.subheader("Genera Report per Tutti i Soggetti")
    st.caption(
        "Genera un file ZIP contenente un report PDF per ogni soggetto nel database. "
        "Utile per archiviazione o stampa in blocco."
    )


def _on_generate_batch_zip():
    """Callback: genera ZIP con N report PDF."""
    all_subjects = get_all_subjects()
    if not all_subjects:
        return

    zip_buffer = io.BytesIO()
    count = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for subj in all_subjects:
            result = subject_to_result(subj)
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
            filename = _safe_report_filename(result.nome, result.cognome)
            # Evita nomi duplicati nel ZIP
            base = filename.rsplit(".", 1)[0]
            filename = f"{base}_ID{subj['id']}.pdf"
            zf.writestr(filename, pdf_bytes)
            count += 1

    st.session_state["rpt_batch_zip"] = zip_buffer.getvalue()
    st.session_state["rpt_batch_count"] = count


    st.button(
        "📦 Genera ZIP con Tutti i Report",
        type="secondary",
        key="rpt_btn_batch",
        on_click=_on_generate_batch_zip,
        disabled=not subjects,
        width="stretch",
    )

    if st.session_state.get("rpt_batch_zip"):
        count = st.session_state.get("rpt_batch_count", 0)
        st.success(f"✅ {count} report generati!")
        st.download_button(
            f"⬇️ Scarica ZIP ({count} report)",
            data=st.session_state["rpt_batch_zip"],
            file_name="CPM_Report_Tutti.zip",
            mime="application/zip",
            width="stretch",
        )
        st.caption("Usa il file ZIP per archiviazione, revisione con il team o stampa in blocco.")
