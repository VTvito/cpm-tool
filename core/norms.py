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
from datetime import date
from pathlib import Path

# Percorso del file norme esterno
_NORMS_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "norms.csv"

# Fasce d'età supportate (semestri: anni;mesi)
AGE_BANDS: list[str] = [
    "3;0-3;6", "3;6-4;0",
    "4;0-4;6", "4;6-5;0",
    "5;0-5;6", "5;6-6;0",
    "6;0-6;6", "6;6-7;0",
    "7;0-7;6", "7;6-8;0",
    "8;0-8;6", "8;6-9;0",
    "9;0-9;6", "9;6-10;0",
    "10;0-10;6", "10;6-11;0",
    "11;0-11;6", "11;6-12;0",
    "Adulti", "Anziani",
]
_AGE_BAND_SET: set[str] = set(AGE_BANDS)

# Placeholder base per anno (9 colonne: età 3-11)
_BASE_PLACEHOLDER: list[tuple] = [
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

# Tabella normativa placeholder: ogni colonna anno → 2 colonne semestrali
_PLACEHOLDER_TABLE: list[tuple] = [
    tuple([row[0]] + [val for val in row[1:] for _ in range(2)])
    for row in _BASE_PLACEHOLDER
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
    except (ValueError, OSError):
        return None


def _normalize_age_band_label(label: str) -> str | None:
    """Converte un'intestazione CSV in una fascia d'età supportata.

    Accetta header come "3;0-3;6", "Età 3;0-3;6", "Adulti", "Età Adulti".
    """
    clean = label.strip()
    if not clean:
        return None

    lowered = clean.lower()
    lowered = lowered.replace("età", "").replace("eta", "").strip()

    if lowered == "adulti":
        return "Adulti"
    if lowered == "anziani":
        return "Anziani"

    # Cerca pattern fascia semestrale: N;M-N;M
    match = re.search(r"(\d+\s*;\s*\d+\s*-\s*\d+\s*;\s*\d+)", clean)
    if match:
        band = re.sub(r"\s", "", match.group(1))  # rimuove spazi interni
        return band if band in _AGE_BAND_SET else None

    return None


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
    except (ValueError, OSError):
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


def compute_age(birth_date: date, test_date: date) -> tuple[int, int]:
    """Calcola età in (anni, mesi) dalla data di nascita alla data di somministrazione."""
    years = test_date.year - birth_date.year
    months = test_date.month - birth_date.month
    if test_date.day < birth_date.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    return years, months


def age_to_band(age_years: int | None = None, age_months: int = 0) -> str:
    """Converte un'età (anni, mesi) nella fascia normativa semestrale.

    Formato fasce: "3;0-3;6" = da 3 anni 0 mesi a 3 anni 5 mesi.
    """
    if age_years is None:
        return ""
    age_years = int(age_years)
    if age_years < 3:
        return ""
    if 3 <= age_years <= 11:
        if age_months < 6:
            return f"{age_years};0-{age_years};6"
        else:
            return f"{age_years};6-{age_years + 1};0"
    if age_years >= 65:
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
