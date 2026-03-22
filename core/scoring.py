"""
CPM – Logica di scoring.

Calcola punteggi per set, totale grezzo, percentile e descrizione qualitativa.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

from core.answer_key import ANSWER_KEY, SETS
from core.norms import lookup_percentile, describe_percentile, age_to_band


@dataclass
class ScoringResult:
    """Risultato dello scoring di un singolo soggetto."""

    # Punteggi per set (0–12 ciascuno)
    set_a_score: int = 0
    set_ab_score: int = 0
    set_b_score: int = 0

    # Totale grezzo (0–36)
    total_raw: int = 0

    # Dettaglio per item: True = corretto, False = errato, None = non risposto
    item_results: dict[str, bool | None] = field(default_factory=dict)
    responses: dict[str, int | None] = field(default_factory=dict)

    # Norme (compilate solo se è fornita la fascia d'età)
    age_band: str = ""
    percentile: str = "–"
    description: str = ""

    # Indice di discrepanza tra set (Raven, 1956)
    discrepancy: float = 0.0
    discrepancy_flag: str = ""  # "", "attenzione", "significativa"

    # Anagrafica (opzionale, per report/database)
    nome: str = ""
    cognome: str = ""
    data_nascita: date | None = None
    data_somministrazione: date | None = None
    sesso: str = ""
    esaminatore: str = ""
    note: str = ""


def normalize_response(value: object) -> int | None:
    """Normalizza una risposta item in un intero valido 1-6 oppure None."""
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if not numeric.is_integer():
        return None

    normalized = int(numeric)
    if 1 <= normalized <= 6:
        return normalized
    return None


def score_responses(responses: Mapping[str, int | None]) -> ScoringResult:
    """Calcola il punteggio CPM a partire dalle risposte.

    Args:
        responses: dizionario {item_label: risposta} (es. {"A1": 4, "A2": 5, …}).
                   Il valore può essere None o assente per item non risposti.

    Returns:
        ScoringResult con punteggi e dettaglio item.
    """
    result = ScoringResult()

    for set_name, items in SETS.items():
        set_score = 0
        for item in items:
            resp = normalize_response(responses.get(item))
            result.responses[item] = resp
            if resp is None:
                result.item_results[item] = None
            else:
                correct = resp == ANSWER_KEY[item]
                result.item_results[item] = correct
                if correct:
                    set_score += 1

        if set_name == "A":
            result.set_a_score = set_score
        elif set_name == "Ab":
            result.set_ab_score = set_score
        else:
            result.set_b_score = set_score

    result.total_raw = result.set_a_score + result.set_ab_score + result.set_b_score

    # Calcola indice di discrepanza (max delta tra i set)
    scores = [result.set_a_score, result.set_ab_score, result.set_b_score]
    result.discrepancy = max(scores) - min(scores)
    if result.discrepancy >= 6:
        result.discrepancy_flag = "significativa"
    elif result.discrepancy >= 4:
        result.discrepancy_flag = "attenzione"
    else:
        result.discrepancy_flag = ""

    return result


def score_with_norms(
    responses: Mapping[str, int | None],
    age_years: int | None = None,
    age_months: int = 0,
    age_band: str | None = None,
) -> ScoringResult:
    """Calcola lo scoring e aggiunge percentile + descrizione qualitativa.

    Se viene fornito `age_band` direttamente viene usato quello.
    Altrimenti viene calcolato da `age_years` e `age_months`.
    """
    result = score_responses(responses)

    band = age_band if age_band else age_to_band(age_years, age_months)
    result.age_band = band

    if band:
        result.percentile = lookup_percentile(result.total_raw, band)
        result.description = describe_percentile(result.percentile)

    return result
