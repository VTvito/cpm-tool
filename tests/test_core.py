"""
Unit test per i moduli core/ — scoring, norms, pdf_report, database, charts.

Esegui con:  python -m pytest tests/test_core.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Assicura che il progetto sia nel path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.answer_key import ANSWER_KEY, SETS, TOTAL_ITEMS, MAX_PER_SET
from core.scoring import score_responses, score_with_norms, ScoringResult
from core.norms import (
    AGE_BANDS, lookup_percentile, describe_percentile,
    age_to_band, load_norm_table, save_norms_csv,
    is_using_placeholder, get_norms_csv_path, get_norm_table_as_dicts,
    _PLACEHOLDER_TABLE,
)
from core.pdf_report import generate_pdf, _sanitize
from core.charts import bar_chart_sets, radar_chart, percentile_gauge, item_heatmap, total_bar


# ═══════════════════════════════════════════
#  answer_key.py
# ═══════════════════════════════════════════

class TestAnswerKey:
    def test_total_items(self):
        assert len(ANSWER_KEY) == TOTAL_ITEMS == 36

    def test_sets_structure(self):
        assert set(SETS.keys()) == {"A", "Ab", "B"}
        for items in SETS.values():
            assert len(items) == MAX_PER_SET == 12

    def test_all_items_in_answer_key(self):
        for items in SETS.values():
            for item in items:
                assert item in ANSWER_KEY

    def test_answer_range(self):
        for item, val in ANSWER_KEY.items():
            assert 1 <= val <= 6, f"{item} ha risposta {val} fuori range 1-6"


# ═══════════════════════════════════════════
#  scoring.py
# ═══════════════════════════════════════════

class TestScoring:
    def test_all_correct(self):
        """Tutte le risposte corrette => 36/36, set 12/12."""
        resp = dict(ANSWER_KEY)
        result = score_responses(resp)
        assert result.set_a_score == 12
        assert result.set_ab_score == 12
        assert result.set_b_score == 12
        assert result.total_raw == 36

    def test_all_wrong(self):
        """Tutte le risposte sbagliate => 0/36."""
        resp = {}
        for item, correct in ANSWER_KEY.items():
            wrong = (correct % 6) + 1  # valore diverso dal corretto
            resp[item] = wrong
        result = score_responses(resp)
        assert result.total_raw == 0
        assert result.set_a_score == 0

    def test_no_responses(self):
        """Nessuna risposta => 0/36, tutti None."""
        result = score_responses({})
        assert result.total_raw == 0
        for item_result in result.item_results.values():
            assert item_result is None

    def test_partial_responses(self):
        """Solo Set A corretto, rest vuoto."""
        resp = {}
        for item in SETS["A"]:
            resp[item] = ANSWER_KEY[item]
        result = score_responses(resp)
        assert result.set_a_score == 12
        assert result.set_ab_score == 0
        assert result.set_b_score == 0
        assert result.total_raw == 12

    def test_item_results_detail(self):
        """Verifica dettaglio item: corretto, errato, None."""
        resp = {"A1": ANSWER_KEY["A1"], "A2": (ANSWER_KEY["A2"] % 6) + 1}
        result = score_responses(resp)
        assert result.item_results["A1"] is True
        assert result.item_results["A2"] is False
        assert result.item_results["A3"] is None

    def test_discrepancy_zero(self):
        """Set bilanciati => discrepancy = 0."""
        result = score_responses(dict(ANSWER_KEY))
        assert result.discrepancy == 0
        assert result.discrepancy_flag == ""

    def test_discrepancy_flag_attenzione(self):
        """Delta >= 4 => flag 'attenzione'."""
        # A tutto corretto (12), Ab tutto errato con 8 corretti, B tutto corretto (12)
        resp = {}
        for item in SETS["A"]:
            resp[item] = ANSWER_KEY[item]
        for i, item in enumerate(SETS["Ab"]):
            resp[item] = ANSWER_KEY[item] if i < 8 else (ANSWER_KEY[item] % 6) + 1
        for item in SETS["B"]:
            resp[item] = ANSWER_KEY[item]
        result = score_responses(resp)
        # A=12, Ab=8, B=12 => delta = 12-8 = 4
        assert result.discrepancy == 4
        assert result.discrepancy_flag == "attenzione"

    def test_discrepancy_flag_significativa(self):
        """Delta >= 6 => flag 'significativa'."""
        resp = {}
        for item in SETS["A"]:
            resp[item] = ANSWER_KEY[item]
        for i, item in enumerate(SETS["Ab"]):
            resp[item] = ANSWER_KEY[item] if i < 6 else (ANSWER_KEY[item] % 6) + 1
        for item in SETS["B"]:
            resp[item] = ANSWER_KEY[item]
        result = score_responses(resp)
        # A=12, Ab=6, B=12 => delta = 12-6 = 6
        assert result.discrepancy == 6
        assert result.discrepancy_flag == "significativa"

    def test_score_with_norms_child(self):
        """Scoring con norme per bambino di 5 anni."""
        resp = dict(ANSWER_KEY)
        result = score_with_norms(resp, age=5)
        assert result.age_band == "5"
        assert result.percentile != "–"
        assert result.description != ""

    def test_score_with_norms_no_age(self):
        """Scoring senza età => nessun percentile."""
        resp = dict(ANSWER_KEY)
        result = score_with_norms(resp)
        assert result.age_band == ""
        assert result.percentile == "–"

    def test_score_with_norms_direct_band(self):
        """Scoring con age_band diretto."""
        resp = dict(ANSWER_KEY)
        result = score_with_norms(resp, age_band="7")
        assert result.age_band == "7"
        assert result.percentile != "–"

    def test_invalid_responses_are_treated_as_missing(self):
        """Input non interi o fuori range non devono rompere lo scoring."""
        resp = {
            "A1": str(ANSWER_KEY["A1"]),
            "A2": float(ANSWER_KEY["A2"]),
            "A3": 7,
            "A4": "abc",
            "A5": 2.5,
            "A6": True,
        }
        result = score_responses(resp)
        assert result.set_a_score == 2
        assert result.item_results["A1"] is True
        assert result.item_results["A2"] is True
        assert result.item_results["A3"] is None
        assert result.item_results["A4"] is None
        assert result.item_results["A5"] is None
        assert result.item_results["A6"] is None


# ═══════════════════════════════════════════
#  norms.py
# ═══════════════════════════════════════════

class TestNorms:
    def test_age_bands_defined(self):
        assert len(AGE_BANDS) == 11  # 3-11 + Adulti + Anziani

    def test_age_to_band(self):
        assert age_to_band(3) == "3"
        assert age_to_band(11) == "11"
        assert age_to_band(30) == "Adulti"
        assert age_to_band(70) == "Anziani"
        assert age_to_band(2) == ""
        assert age_to_band(None) == ""

    def test_lookup_percentile_valid(self):
        pct = lookup_percentile(20, "3")
        assert pct != "–"

    def test_lookup_percentile_invalid_band(self):
        pct = lookup_percentile(20, "NonEsiste")
        assert pct == "–"

    def test_lookup_percentile_zero(self):
        pct = lookup_percentile(0, "3")
        assert pct == "<5"

    def test_lookup_percentile_max(self):
        pct = lookup_percentile(36, "3")
        assert pct == ">95"

    def test_describe_percentile(self):
        assert describe_percentile("50") == "Nella media"
        assert describe_percentile("<5") == "Molto inferiore alla media"
        assert describe_percentile(">95") == "Nettamente superiore alla media"
        assert describe_percentile("unknown") == "Dati non disponibili"

    def test_placeholder_table_format(self):
        """La tabella placeholder ha il formato atteso."""
        assert len(_PLACEHOLDER_TABLE) > 0
        for row in _PLACEHOLDER_TABLE:
            assert isinstance(row[0], int)
            assert 0 <= row[0] <= 36

    def test_load_norm_table(self):
        """load_norm_table restituisce una lista di tuple non vuota."""
        table = load_norm_table()
        assert len(table) > 0
        assert isinstance(table[0], tuple)

    def test_get_norm_table_as_dicts(self):
        """Verifica formato dizionario per la visualizzazione."""
        dicts = get_norm_table_as_dicts()
        assert len(dicts) > 0
        assert "Punteggio Grezzo" in dicts[0]

    def test_save_norms_csv_validation(self):
        """CSV malformato viene respinto."""
        bad_csv = b"solo una colonna\n"
        msg = save_norms_csv(bad_csv)
        assert msg.startswith("Errore")

    def test_save_and_load_norms_csv(self, tmp_path, monkeypatch):
        """Ciclo completo salva/carica CSV norme in directory temporanea."""
        # Redirect il percorso CSV a una directory temporanea
        csv_path = tmp_path / "norms.csv"
        monkeypatch.setattr("core.norms._NORMS_CSV_PATH", csv_path)

        # Crea un CSV valido di test
        lines = ["Punteggio Grezzo,Età 3,Età 4,Età 5"]
        for score in range(0, 37, 2):
            lines.append(f"{score},<5,10,25")
        csv_bytes = "\n".join(lines).encode("utf-8")

        msg = save_norms_csv(csv_bytes)
        assert not msg.startswith("Errore"), msg
        assert csv_path.is_file()

        # Verifica che viene caricato
        from core.norms import _load_norm_table_from_csv
        table = _load_norm_table_from_csv(csv_path)
        assert table is not None
        assert len(table) > 0

    def test_lookup_percentile_uses_csv_headers(self, tmp_path, monkeypatch):
        """Le colonne età del CSV devono essere mappate dal nome header, non per posizione."""
        csv_path = tmp_path / "norms.csv"
        monkeypatch.setattr("core.norms._NORMS_CSV_PATH", csv_path)

        csv_bytes = (
            "Punteggio Grezzo,Età 7,Adulti,Anziani\n"
            "0,<5,10,25\n"
            "20,50,75,90\n"
        ).encode("utf-8")

        msg = save_norms_csv(csv_bytes)
        assert not msg.startswith("Errore"), msg
        assert lookup_percentile(20, "7") == "50"
        assert lookup_percentile(20, "Adulti") == "75"
        assert lookup_percentile(20, "Anziani") == "90"
        assert lookup_percentile(20, "3") == "–"

        dicts = get_norm_table_as_dicts()
        assert "Età 7" in dicts[0]
        assert "Età Adulti" in dicts[0]
        assert "Età Anziani" in dicts[0]

    def test_save_norms_csv_rejects_ragged_rows(self, tmp_path, monkeypatch):
        """CSV con colonne incoerenti deve essere respinto."""
        csv_path = tmp_path / "norms.csv"
        monkeypatch.setattr("core.norms._NORMS_CSV_PATH", csv_path)

        bad_csv = (
            "Punteggio Grezzo,Età 3,Età 4\n"
            "0,<5,10\n"
            "10,25\n"
        ).encode("utf-8")

        msg = save_norms_csv(bad_csv)
        assert msg.startswith("Errore")
        assert not csv_path.exists()


# ═══════════════════════════════════════════
#  pdf_report.py
# ═══════════════════════════════════════════

class TestPDF:
    def test_sanitize_unicode(self):
        assert _sanitize("test\u2013dash") == "test-dash"
        assert _sanitize("quote\u201csmart\u201d") == 'quote"smart"'
        assert _sanitize("normal text") == "normal text"

    def test_generate_pdf_basic(self):
        """Genera PDF con risultato base, verifica che restituisce bytes."""
        result = score_responses(dict(ANSWER_KEY))
        result.nome = "Test"
        result.cognome = "User"
        pdf_bytes = generate_pdf(result)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_pdf_with_norms(self):
        """PDF con percentile compilato."""
        result = score_with_norms(dict(ANSWER_KEY), age=7)
        result.nome = "Marco"
        result.cognome = "Rossi"
        pdf_bytes = generate_pdf(result)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_generate_pdf_with_discrepancy(self):
        """PDF con discrepanza significativa."""
        resp = {}
        for item in SETS["A"]:
            resp[item] = ANSWER_KEY[item]
        for i, item in enumerate(SETS["Ab"]):
            resp[item] = ANSWER_KEY[item] if i < 5 else (ANSWER_KEY[item] % 6) + 1
        for item in SETS["B"]:
            resp[item] = ANSWER_KEY[item]
        result = score_with_norms(resp, age=8)
        result.nome = "Discrepanza"
        result.cognome = "Test"
        pdf_bytes = generate_pdf(result)
        assert isinstance(pdf_bytes, bytes)
        assert result.discrepancy_flag == "significativa"

    def test_generate_pdf_with_notes(self):
        """PDF con note contenenti caratteri speciali."""
        result = score_responses(dict(ANSWER_KEY))
        result.nome = "Note"
        result.cognome = "Test"
        result.note = "Soggetto collaborativo. Punteggio \u2013 nella norma."
        pdf_bytes = generate_pdf(result)
        assert isinstance(pdf_bytes, bytes)

    def test_generate_pdf_empty_responses(self):
        """PDF con risposte vuote."""
        result = score_responses({})
        pdf_bytes = generate_pdf(result)
        assert isinstance(pdf_bytes, bytes)


# ═══════════════════════════════════════════
#  database.py
# ═══════════════════════════════════════════

class TestDatabase:
    @pytest.fixture(autouse=True)
    def use_temp_db(self, tmp_path, monkeypatch):
        """Usa un database temporaneo per ogni test."""
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("core.database.DB_PATH", db_path)
        from core.database import init_db
        init_db()

    def test_save_and_retrieve(self):
        from core.database import save_result, get_all_subjects, get_subject
        result = score_with_norms(dict(ANSWER_KEY), age=6)
        result.nome = "Mario"
        result.cognome = "Rossi"
        rec_id = save_result(result, dict(ANSWER_KEY))
        assert rec_id is not None

        subjects = get_all_subjects()
        assert len(subjects) == 1
        assert subjects[0]["nome"] == "Mario"

        subj = get_subject(rec_id)
        assert subj is not None
        assert subj["total_raw"] == 36

    def test_delete_subject(self):
        from core.database import save_result, get_all_subjects, delete_subject
        result = score_responses(dict(ANSWER_KEY))
        result.nome = "ToDelete"
        rec_id = save_result(result, dict(ANSWER_KEY))
        assert len(get_all_subjects()) == 1

        delete_subject(rec_id)
        assert len(get_all_subjects()) == 0

    def test_subject_to_result(self):
        from core.database import save_result, get_subject, subject_to_result
        result = score_with_norms(dict(ANSWER_KEY), age=8)
        result.nome = "Rebuild"
        result.cognome = "Test"
        rec_id = save_result(result, dict(ANSWER_KEY))

        subj = get_subject(rec_id)
        assert subj is not None
        rebuilt = subject_to_result(subj)
        assert rebuilt.nome == "Rebuild"
        assert rebuilt.total_raw == 36
        assert rebuilt.set_a_score == 12

    def test_multiple_subjects(self):
        from core.database import save_result, get_all_subjects
        for i in range(5):
            result = score_responses(dict(ANSWER_KEY))
            result.nome = f"Subj{i}"
            save_result(result, dict(ANSWER_KEY))
        assert len(get_all_subjects()) == 5

    def test_json_responses_stored(self):
        from core.database import save_result, get_subject
        resp = dict(ANSWER_KEY)
        result = score_responses(resp)
        rec_id = save_result(result, resp)

        subj = get_subject(rec_id)
        assert subj is not None
        stored = json.loads(subj["risposte"])
        assert stored["A1"] == ANSWER_KEY["A1"]


# ═══════════════════════════════════════════
#  charts.py
# ═══════════════════════════════════════════

class TestCharts:
    @pytest.fixture
    def sample_result(self):
        return score_with_norms(dict(ANSWER_KEY), age=7)

    def test_bar_chart(self, sample_result):
        fig = bar_chart_sets(sample_result)
        assert fig is not None
        assert len(fig.data) > 0

    def test_radar_chart(self, sample_result):
        fig = radar_chart(sample_result)
        assert fig is not None

    def test_percentile_gauge(self, sample_result):
        fig = percentile_gauge(sample_result.percentile)
        assert fig is not None

    def test_item_heatmap(self, sample_result):
        fig = item_heatmap(sample_result)
        assert fig is not None

    def test_total_bar(self, sample_result):
        fig = total_bar(sample_result)
        assert fig is not None
        assert len(fig.data) == 2  # ottenuto + massimo

    def test_percentile_gauge_edge(self):
        """Gauge con percentile sconosciuto."""
        fig = percentile_gauge("–")
        assert fig is not None
