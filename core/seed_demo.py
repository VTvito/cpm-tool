"""
CPM – Seed dati demo.

Popola il database con soggetti realistici se è vuoto.
Usato per la demo pubblica: ogni cold start su Streamlit Cloud
ricrea i dati di esempio automaticamente.
"""

from __future__ import annotations

from datetime import date

from core.answer_key import ANSWER_KEY, SETS
from core.database import is_db_empty, save_result
from core.norms import compute_age
from core.scoring import score_with_norms

# ── Item labels per set ──────────────────────────────────────────────────────
_A  = SETS["A"]    # A1-A12
_AB = SETS["Ab"]   # Ab1-Ab12
_B  = SETS["B"]    # B1-B12


def _wrong(item: str) -> int:
    """Risposta sbagliata garantita per l'item (diversa dalla corretta)."""
    return (ANSWER_KEY[item] % 6) + 1


def _build(wrong_items: set[str]) -> dict[str, int]:
    return {
        item: (_wrong(item) if item in wrong_items else ANSWER_KEY[item])
        for item in ANSWER_KEY
    }


# ── Pattern di punteggio ─────────────────────────────────────────────────────

def _all_correct() -> dict[str, int]:             # 36/36
    return _build(set())

def _very_good() -> dict[str, int]:               # 33/36  A=11 Ab=11 B=11
    return _build({"A12", "Ab12", "B12"})

def _above_avg() -> dict[str, int]:               # 27/36  A=9  Ab=9  B=9
    return _build(set(_A[9:]) | set(_AB[9:]) | set(_B[9:]))

def _average() -> dict[str, int]:                 # 21/36  A=7  Ab=7  B=7
    return _build(set(_A[7:]) | set(_AB[7:]) | set(_B[7:]))

def _below_avg() -> dict[str, int]:               # 12/36  A=4  Ab=4  B=4
    return _build(set(_A[4:]) | set(_AB[4:]) | set(_B[4:]))

def _poor() -> dict[str, int]:                    # 6/36   A=2  Ab=2  B=2
    return _build(set(_A[2:]) | set(_AB[2:]) | set(_B[2:]))

def _disc_significativa() -> dict[str, int]:      # A=12  Ab=4  B=11  Δ=8
    return _build(set(_AB[4:]) | {"B12"})

def _disc_attenzione() -> dict[str, int]:         # A=10  Ab=6  B=10  Δ=4
    return _build(set(_A[10:]) | set(_AB[6:]) | set(_B[10:]))


# ── Soggetti demo ────────────────────────────────────────────────────────────
# (nome, cognome, data_nascita, data_somm, sesso, esaminatore, pattern_fn, note)
_DEMO_SUBJECTS: list[tuple] = [
    # fascia 5
    ("Sofia",      "Russo",    date(2020, 4, 12), date(2026, 1, 15), "F",
     "Dott.ssa M. Verdi",    _all_correct,         ""),
    # fascia 6
    ("Marco",      "Bianchi",  date(2019, 9,  3), date(2026, 1, 20), "M",
     "Dott. R. Ferretti",    _very_good,           ""),
    ("Serena",     "Lombardi", date(2019,11, 14), date(2026, 1, 28), "F",
     "Dott.ssa M. Verdi",    _below_avg,           ""),
    # fascia 7
    ("Giulia",     "Romano",   date(2018, 2, 27), date(2026, 2,  4), "F",
     "Dott.ssa M. Verdi",    _above_avg,           ""),
    ("Luca",       "Esposito", date(2018, 7, 14), date(2026, 2,  4), "M",
     "Dott. R. Ferretti",    _average,
     "Lieve difficolta di concentrazione in fase iniziale"),
    # fascia 8
    ("Anna",       "Ferrari",  date(2017,11, 20), date(2026, 2, 18), "F",
     "Dott.ssa M. Verdi",    _above_avg,           ""),
    ("Matteo",     "Ricci",    date(2017, 5,  8), date(2026, 2, 18), "M",
     "Dott. R. Ferretti",    _below_avg,           ""),
    ("Valentina",  "Serra",    date(2017, 8, 25), date(2026, 2, 25), "F",
     "Dott.ssa L. Conti",    _disc_significativa,
     "Discrepanza Set A / Set Ab da approfondire clinicamente"),
    # fascia 9
    ("Chiara",     "Marino",   date(2016, 8,  1), date(2026, 3,  3), "F",
     "Dott.ssa L. Conti",    _very_good,           ""),
    ("Alessandro", "Greco",    date(2016, 3, 22), date(2026, 3,  3), "M",
     "Dott.ssa L. Conti",    _average,             ""),
    # fascia 10
    ("Francesca",  "Bruno",    date(2015, 6,  5), date(2026, 3, 10), "F",
     "Dott.ssa L. Conti",    _above_avg,           ""),
    ("Davide",     "Conti",    date(2015, 1, 30), date(2026, 3, 10), "M",
     "Dott. R. Ferretti",    _poor,
     "Richiesta rivalutazione con approfondimento neuropsicologico"),
    ("Riccardo",   "Mancini",  date(2015,12,  7), date(2026, 3,  5), "M",
     "Dott. R. Ferretti",    _disc_attenzione,     ""),
    # fascia 11
    ("Elena",      "Gallo",    date(2014,10, 11), date(2026, 3, 17), "F",
     "Dott.ssa M. Verdi",    _very_good,           ""),
    ("Lorenzo",    "Colombo",  date(2014, 4, 19), date(2026, 3, 17), "M",
     "Dott.ssa M. Verdi",    _average,             ""),
]


def seed_if_empty() -> int:
    """Inserisce i soggetti demo se il database è vuoto.

    Ritorna il numero di record inseriti (0 se il DB non era vuoto).
    """
    if not is_db_empty():
        return 0

    count = 0
    for nome, cognome, dn, ds, sesso, esaminatore, pattern_fn, note in _DEMO_SUBJECTS:
        eta_anni, eta_mesi = compute_age(dn, ds)

        responses = pattern_fn()
        result = score_with_norms(responses, age_years=eta_anni, age_months=eta_mesi)
        result.nome = nome
        result.cognome = cognome
        result.data_nascita = dn
        result.data_somministrazione = ds
        result.sesso = sesso
        result.esaminatore = esaminatore
        result.note = note
        save_result(result, responses)
        count += 1

    return count
