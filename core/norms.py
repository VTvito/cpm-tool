"""
CPM – Tabelle normative italiane.

Le norme vengono caricate dal file data/norms.csv se presente,
altrimenti si usano i valori placeholder di esempio.
Per caricare le norme reali: usare la pagina "Norme" dell'app
oppure posizionare un file CSV nella cartella data/.

Riferimento: Belacchi C., Scalisi T.G., Cannoni E., Cornoldi C. (2008).
CPM – Coloured Progressive Matrices. OS Firenze.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

# Percorso del file norme esterno
_NORMS_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "norms.csv"

# Fasce d'età supportate (anni compiuti)
AGE_BANDS: list[str] = [
    "3", "4", "5", "6", "7", "8", "9", "10", "11",
    "Adulti", "Anziani",
]

# Tabella normativa placeholder (usata se il CSV non esiste)
_PLACEHOLDER_TABLE: list[tuple] = [
    (0,  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5"),
    (5,  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5"),
    (10, "5",   "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5"),
    (12, "10",  "5",   "<5",  "<5",  "<5",  "<5",  "<5",  "<5",  "<5"),
    (14, "25",  "10",  "5",   "<5",  "<5",  "<5",  "<5",  "<5",  "<5"),
    (16, "50",  "25",  "10",  "5",   "<5",  "<5",  "<5",  "<5",  "<5"),
    (18, "75",  "50",  "25",  "10",  "5",   "<5",  "<5",  "<5",  "<5"),
    (20, "90",  "75",  "50",  "25",  "10",  "5",   "<5",  "<5",  "<5"),
    (22, "95",  "90",  "75",  "50",  "25",  "10",  "5",   "<5",  "<5"),
    (24, ">95", "95",  "90",  "75",  "50",  "25",  "10",  "5",   "<5"),
    (26, ">95", ">95", "95",  "90",  "75",  "50",  "25",  "10",  "5"),
    (28, ">95", ">95", ">95", "95",  "90",  "75",  "50",  "25",  "10"),
    (30, ">95", ">95", ">95", ">95", "95",  "90",  "75",  "50",  "25"),
    (32, ">95", ">95", ">95", ">95", ">95", "95",  "90",  "75",  "50"),
    (34, ">95", ">95", ">95", ">95", ">95", ">95", "95",  "90",  "75"),
    (36, ">95", ">95", ">95", ">95", ">95", ">95", ">95", "95",  "90"),
]


def _load_norm_table_from_csv(path: Path) -> list[tuple] | None:
    """Carica la tabella norme da un file CSV.

    Formato atteso: prima colonna = Punteggio Grezzo (int),
    colonne successive = percentili per Età 3, 4, …, 11 (stringhe).
    """
    if not path.is_file():
        return None
    try:
        _, rows = _parse_norm_csv_text(path.read_text(encoding="utf-8-sig"))
        return rows
    except Exception:
        pass
    return None


def _normalize_age_band_label(label: str) -> str | None:
    """Converte un'intestazione CSV in una fascia d'età supportata."""
    clean = label.strip()
    if not clean:
        return None

    lowered = clean.lower()
    lowered = lowered.replace("età", "eta")
    lowered = lowered.replace("anni", "")
    lowered = lowered.replace("anno", "")
    lowered = lowered.strip()

    if lowered == "adulti":
        return "Adulti"
    if lowered == "anziani":
        return "Anziani"

    match = re.search(r"(\d+)", lowered)
    if not match:
        return None

    age = match.group(1)
    return age if age in AGE_BANDS else None


def _parse_norm_csv_text(csv_text: str) -> tuple[list[str], list[tuple]]:
    """Valida e converte il CSV norme in bande + righe dati."""
    reader = csv.reader(io.StringIO(csv_text))
    rows_in = [row for row in reader if any(cell.strip() for cell in row)]
    if len(rows_in) < 2:
        raise ValueError("il file deve avere almeno un'intestazione e una riga dati.")

    header = rows_in[0]
    if len(header) < 2:
        raise ValueError("servono almeno 2 colonne (Punteggio Grezzo + almeno una fascia d'età).")

    bands: list[str] = []
    for cell in header[1:]:
        band = _normalize_age_band_label(cell)
        if band is None:
            raise ValueError(f"colonna età non riconosciuta: {cell!r}.")
        if band in bands:
            raise ValueError(f"fascia d'età duplicata nel CSV: {band}.")
        bands.append(band)

    expected_width = len(header)
    parsed_rows: list[tuple] = []
    previous_raw: int | None = None
    for row in rows_in[1:]:
        if len(row) != expected_width:
            raise ValueError("tutte le righe devono avere lo stesso numero di colonne dell'intestazione.")

        raw_text = row[0].strip()
        if not raw_text:
            continue

        try:
            raw_score = int(raw_text)
        except ValueError:
            raise ValueError(f"il punteggio grezzo '{raw_text}' non è un numero intero valido.")
        if previous_raw is not None and raw_score <= previous_raw:
            raise ValueError("i punteggi grezzi devono essere ordinati in modo strettamente crescente.")

        parsed_rows.append((raw_score, *(cell.strip() for cell in row[1:])))
        previous_raw = raw_score

    if not parsed_rows:
        raise ValueError("nessuna riga dati valida trovata nel file.")

    return bands, parsed_rows


def _load_norm_table_with_bands() -> tuple[list[str], list[tuple]] | None:
    """Carica dal CSV le bande disponibili e la tabella corrispondente."""
    if not _NORMS_CSV_PATH.is_file():
        return None
    try:
        return _parse_norm_csv_text(_NORMS_CSV_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def load_norm_table() -> list[tuple]:
    """Restituisce la tabella norme, cercando prima il CSV esterno."""
    loaded = _load_norm_table_with_bands()
    if loaded is not None:
        _, rows = loaded
        return rows
    return list(_PLACEHOLDER_TABLE)


def is_using_placeholder() -> bool:
    """True se si stanno usando le norme placeholder (CSV assente o invalido)."""
    return _load_norm_table_with_bands() is None


def save_norms_csv(csv_bytes: bytes) -> str:
    """Salva un file CSV norme nella cartella data/.

    Restituisce un messaggio di conferma o errore.
    Fa una validazione base del formato prima di salvare.
    """
    _NORMS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Validazione: prova a parsare prima di salvare
    try:
        text = csv_bytes.decode("utf-8-sig")
        _, rows = _parse_norm_csv_text(text)
        count = len(rows)
    except ValueError as exc:
        return f"Errore: {exc}"
    except Exception as exc:
        return f"Errore nella lettura del file: {exc}"

    _NORMS_CSV_PATH.write_bytes(csv_bytes)
    # Invalida la cache interna reimportando
    return f"Norme salvate con successo! ({count} righe caricate)"


def get_norms_csv_path() -> Path:
    """Restituisce il percorso del file CSV norme."""
    return _NORMS_CSV_PATH


# ── API pubblica (compatibile con il resto del codice) ──

def _get_age_col() -> dict[str, int]:
    """Mappa fascia_età → indice colonna nella tabella norme."""
    loaded = _load_norm_table_with_bands()
    if loaded is not None:
        bands, _ = loaded
        return {band: idx for idx, band in enumerate(bands)}

    n_cols = len(_PLACEHOLDER_TABLE[0]) - 1 if _PLACEHOLDER_TABLE else 0
    return {band: idx for idx, band in enumerate(AGE_BANDS[:n_cols])}


# Tabella norme dinamica: usare sempre load_norm_table() per ottenere
# i dati aggiornati. NORM_TABLE è mantenuto solo per import legacy.
NORM_TABLE = _PLACEHOLDER_TABLE


def age_to_band(age: int | float | None) -> str:
    """Converte un'età in anni nella fascia normativa appropriata."""
    if age is None:
        return ""
    age = int(age)
    if age < 3:
        return ""
    if 3 <= age <= 11:
        return str(age)
    if age >= 65:
        return "Anziani"
    return "Adulti"


def lookup_percentile(raw_score: int, age_band: str) -> str:
    """Restituisce il percentile per un punteggio grezzo e una fascia d'età.

    Ritorna "–" se la fascia non è presente nella tabella.
    """
    age_col = _get_age_col()
    if age_band not in age_col:
        return "–"
    col = age_col[age_band]

    table = load_norm_table()
    result = "<5"
    for row in table:
        if raw_score >= row[0]:
            result = row[col + 1]  # +1 perché indice 0 è il punteggio
        else:
            break
    return result


def describe_percentile(pct: str) -> str:
    """Mappa un percentile a una descrizione qualitativa italiana."""
    mapping = {
        "<5":  "Molto inferiore alla media",
        "5":   "Nettamente inferiore alla media",
        "10":  "Inferiore alla media",
        "25":  "Inferiore alla media",
        "50":  "Nella media",
        "75":  "Superiore alla media",
        "90":  "Superiore alla media",
        "95":  "Nettamente superiore alla media",
        ">95": "Nettamente superiore alla media",
    }
    return mapping.get(pct, "Dati non disponibili")


def get_norm_table_as_dicts() -> list[dict]:
    """Restituisce la tabella norme come lista di dizionari per visualizzazione."""
    loaded = _load_norm_table_with_bands()
    if loaded is not None:
        bands_available, table = loaded
    else:
        table = list(_PLACEHOLDER_TABLE)
        n_cols = len(table[0]) - 1 if table else 0
        bands_available = AGE_BANDS[:n_cols]

    rows = []
    for row in table:
        d = {"Punteggio Grezzo": row[0]}
        for i, band in enumerate(bands_available):
            d[f"Età {band}"] = row[i + 1]
        rows.append(d)
    return rows
