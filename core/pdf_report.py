"""
CPM – Generazione report PDF.

Genera un report A4 con anagrafica, tabella risposte, risultati e grafici.
Usa fpdf2 (pure Python, zero dipendenze di sistema).
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from fpdf import FPDF

from core.answer_key import SETS, ANSWER_KEY
from core.norms import is_using_placeholder
from core.scoring import ScoringResult


def _sanitize(text: str) -> str:
    """Replace problematic Unicode characters with ASCII equivalents."""
    replacements = {
        "\u2013": "-",  # en-dash
        "\u2014": "-",  # em-dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2026": "...",  # ellipsis
        "\u2022": "-",  # bullet
        "\u2192": "->",  # right arrow
        "\u2717": "X",  # ballot X
        "\u2713": "V",  # check mark
        "\u2715": "X",  # multiplication X
        "\u2260": "!=",  # not equal
        "\u2264": "<=",  # less or equal
        "\u2265": ">=",  # greater or equal
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text


class CPMReport(FPDF):
    """Report PDF custom per un singolo soggetto CPM."""

    # Colori (R, G, B)
    _DARK_BLUE = (27, 58, 107)
    _TEAL = (0, 119, 182)
    _GREEN = (39, 174, 96)
    _ORANGE = (230, 126, 34)
    _BLUE = (41, 128, 185)
    _RED = (231, 76, 60)
    _LIGHT_GRAY = (242, 243, 244)
    _WHITE = (255, 255, 255)

    @staticmethod
    def _norms_status_text() -> str:
        if is_using_placeholder():
            return "Norme: PLACEHOLDER (verificare con manuale)"
        return "Norme: CSV personalizzate caricate"

    def header(self):
        self.set_fill_color(*self._DARK_BLUE)
        self.rect(0, 0, 210, 22, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self._WHITE)
        self.set_y(4)
        self.cell(0, 14, _sanitize("CPM - Matrici Colorate di Raven  |  Report Scoring"), align="C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10,
                  _sanitize(
                      "Report generato automaticamente  |  "
                      f"{self._norms_status_text()}  |  "
                      f"Pag. {self.page_no()}/{{nb}}"
                  ),
                  align="C")


def _safe(val) -> str:
    if val is None:
        return "-"
    return _sanitize(str(val))


def generate_pdf(
    result: ScoringResult,
    chart_images: dict[str, bytes] | None = None,
) -> bytes:
    """Genera il PDF e restituisce i bytes.

    Args:
        result: ScoringResult con tutti i dati.
        chart_images: dict opzionale {"bar": png_bytes, "radar": png_bytes, …}.
    """
    using_placeholder = is_using_placeholder()
    pdf = CPMReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── ANAGRAFICA ──────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(*CPMReport._TEAL)
    pdf.set_text_color(*CPMReport._WHITE)
    pdf.cell(0, 9, _sanitize("  Dati del Soggetto"), fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    data_rows = [
        ("Nome", _safe(result.nome)),
        ("Cognome", _safe(result.cognome)),
        ("Data di nascita", _safe(result.data_nascita)),
        ("Data somministrazione", _safe(result.data_somministrazione)),
        ("Sesso", _safe(result.sesso)),
        ("Esaminatore", _safe(result.esaminatore)),
        ("Fascia d'età", _safe(result.age_band)),
    ]
    for label, val in data_rows:
        pdf.set_fill_color(*CPMReport._LIGHT_GRAY)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(55, 7, f"  {_sanitize(label)}", fill=True, border=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(*CPMReport._WHITE)
        pdf.cell(0, 7, f"  {_sanitize(val)}", fill=True, border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # ── RISULTATI ───────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(*CPMReport._DARK_BLUE)
    pdf.set_text_color(*CPMReport._WHITE)
    pdf.cell(0, 9, _sanitize("  Risultati"), fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(0, 0, 0)
    results_rows = [
        ("Totale Set A", f"{result.set_a_score} / 12", CPMReport._BLUE),
        ("Totale Set Ab", f"{result.set_ab_score} / 12", CPMReport._ORANGE),
        ("Totale Set B", f"{result.set_b_score} / 12", CPMReport._GREEN),
        ("TOTALE GREZZO", f"{result.total_raw} / 36", CPMReport._DARK_BLUE),
        ("Percentile", result.percentile, CPMReport._TEAL),
        ("Descrizione", result.description, CPMReport._TEAL),
    ]
    for label, val, color in results_rows:
        pdf.set_fill_color(*CPMReport._LIGHT_GRAY)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(55, 8, f"  {_sanitize(label)}", fill=True, border=1)
        pdf.set_fill_color(*CPMReport._WHITE)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*color)
        pdf.cell(0, 8, f"  {_sanitize(val)}", fill=True, border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # Discrepanza tra set
    if result.discrepancy > 0:
        disc_val = f"Delta = {result.discrepancy}"
        if result.discrepancy_flag == "significativa":
            disc_label = "DISCREPANZA SIGNIFICATIVA"
            disc_color = CPMReport._RED
        elif result.discrepancy_flag == "attenzione":
            disc_label = "Discrepanza da monitorare"
            disc_color = CPMReport._ORANGE
        else:
            disc_label = "Discrepanza tra set"
            disc_color = CPMReport._TEAL
        pdf.set_fill_color(*CPMReport._LIGHT_GRAY)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(55, 8, f"  {_sanitize(disc_label)}", fill=True, border=1)
        pdf.set_fill_color(*CPMReport._WHITE)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*disc_color)
        pdf.cell(0, 8, f"  {_sanitize(disc_val)}", fill=True, border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(5)

    # ── DETTAGLIO RISPOSTE ──────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(*CPMReport._TEAL)
    pdf.set_text_color(*CPMReport._WHITE)
    pdf.cell(0, 9, _sanitize("  Dettaglio Risposte per Item"), fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # Intestazione colonne (3 set: Item | Risp | Esito)
    col_w = 20
    set_configs = [
        ("Set A", CPMReport._BLUE),
        ("Set Ab", CPMReport._ORANGE),
        ("Set B", CPMReport._GREEN),
    ]
    pdf.set_font("Helvetica", "B", 9)
    for set_label, color in set_configs:
        pdf.set_fill_color(*color)
        pdf.set_text_color(*CPMReport._WHITE)
        pdf.cell(col_w, 6, "Item", border=1, fill=True, align="C")
        pdf.cell(col_w, 6, "Risp.", border=1, fill=True, align="C")
        pdf.cell(col_w, 6, "Esito", border=1, fill=True, align="C")
    pdf.ln()

    # Righe
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    for i in range(12):
        for set_name in ["A", "Ab", "B"]:
            item = SETS[set_name][i]
            r = result.item_results.get(item)
            raw_response = result.responses.get(item)

            pdf.set_fill_color(*CPMReport._LIGHT_GRAY if i % 2 == 0 else CPMReport._WHITE)
            pdf.cell(col_w, 6, item, border=1, fill=True, align="C")

            # Risposta data
            if raw_response is None:
                resp_text = "-"
            else:
                resp_text = str(raw_response)
            pdf.cell(col_w, 6, resp_text, border=1, fill=True, align="C")

            # Esito con colore
            if r is None:
                pdf.set_fill_color(189, 195, 199)
                esito = "-"
            elif r:
                pdf.set_fill_color(169, 223, 191)
                esito = "OK"
            else:
                pdf.set_fill_color(245, 203, 167)
                esito = "X"
            pdf.cell(col_w, 6, esito, border=1, fill=True, align="C")
        pdf.ln()

    pdf.ln(3)

    # ── GRAFICI (se forniti) ────────────────
    if chart_images:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(*CPMReport._TEAL)
        pdf.set_text_color(*CPMReport._WHITE)
        pdf.cell(0, 9, _sanitize("  Grafici"), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        for name, img_bytes in chart_images.items():
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            try:
                pdf.image(tmp_path, w=170)
                pdf.ln(5)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    # ── NOTE ────────────────────────────────
    if result.note:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, "Note:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _sanitize(result.note))

    # ── DISCLAIMER ──────────────────────────
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(0, 4,
        _sanitize(
            (
                "Le norme applicate sono PLACEHOLDER di esempio. "
                "Verificare sempre con il manuale dell'edizione in uso "
                "(Belacchi et al., 2008 - OS Firenze). "
                if using_placeholder else
                "Il percentile e' stato calcolato usando il file norme CSV attualmente caricato. "
                "Verificare che il file corrisponda all'edizione del manuale in uso. "
            ) +
            "Questo report e' uno strumento di supporto e non sostituisce "
            "la valutazione clinica dell'esaminatore."
        ))

    return bytes(pdf.output())
