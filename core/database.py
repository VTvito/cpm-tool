"""
CPM – Database SQLite per la persistenza dei soggetti.

Fornisce funzioni CRUD per salvare, recuperare, filtrare ed esportare
i risultati di scoring dei soggetti.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from core.scoring import ScoringResult

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sessions.db"


@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Crea la tabella se non esiste."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT,
                cognome       TEXT,
                data_nascita  TEXT,
                data_somm     TEXT,
                sesso         TEXT,
                esaminatore   TEXT,
                eta_band      TEXT,
                risposte      TEXT,
                score_a       INTEGER,
                score_ab      INTEGER,
                score_b       INTEGER,
                total_raw     INTEGER,
                percentile    TEXT,
                descrizione   TEXT,
                note          TEXT DEFAULT '',
                created_at    TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def save_result(result: ScoringResult, responses: Mapping[str, int | None]) -> int:
    """Salva un risultato nel database. Restituisce l'id del record."""
    init_db()
    with _connect() as conn:
        cur = conn.execute("""
            INSERT INTO subjects
                (nome, cognome, data_nascita, data_somm, sesso, esaminatore,
                 eta_band, risposte, score_a, score_ab, score_b, total_raw,
                 percentile, descrizione, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.nome,
            result.cognome,
            str(result.data_nascita) if result.data_nascita else "",
            str(result.data_somministrazione) if result.data_somministrazione else "",
            result.sesso,
            result.esaminatore,
            result.age_band,
            json.dumps(responses, ensure_ascii=False),
            result.set_a_score,
            result.set_ab_score,
            result.set_b_score,
            result.total_raw,
            result.percentile,
            result.description,
            result.note,
        ))
        return cur.lastrowid


def get_all_subjects() -> list[dict]:
    """Restituisce tutti i soggetti come lista di dizionari."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM subjects ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def is_db_empty() -> bool:
    """Restituisce True se non ci sono soggetti nel database."""
    init_db()
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        return count == 0


def get_subject(subject_id: int) -> dict | None:
    """Restituisce un singolo soggetto per id."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM subjects WHERE id = ?", (subject_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_subject(subject_id: int):
    """Elimina un soggetto dal database."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))


def subject_to_result(row: dict) -> ScoringResult:
    """Ricostruisce un ScoringResult da un record del database."""
    from core.scoring import score_responses
    try:
        responses = json.loads(row["risposte"]) if row["risposte"] else {}
    except (json.JSONDecodeError, TypeError):
        responses = {}
    result = score_responses(responses)
    result.nome = row.get("nome", "")
    result.cognome = row.get("cognome", "")
    dn = row.get("data_nascita", "")
    if dn:
        try:
            result.data_nascita = date.fromisoformat(dn)
        except ValueError:
            pass
    ds = row.get("data_somm", "")
    if ds:
        try:
            result.data_somministrazione = date.fromisoformat(ds)
        except ValueError:
            pass
    result.sesso = row.get("sesso", "")
    result.esaminatore = row.get("esaminatore", "")
    result.age_band = row.get("eta_band", "")
    result.percentile = row.get("percentile", "–")
    result.description = row.get("descrizione", "")
    result.note = row.get("note", "")
    return result
