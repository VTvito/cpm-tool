---
description: "Use when modifying core/ modules: scoring logic, answer key, normative tables, charts, PDF reports, or database. Covers the separation rule, PDF Unicode safety, and PLACEHOLDER norms."
applyTo: "core/**/*.py"
---
# Core Module Guidelines

## Separation Rule

`core/` modules must **never** import `streamlit`. They are pure Python logic reusable outside the web app (CLI, batch scripts, tests).

## Key Modules

### answer_key.py
- `ANSWER_KEY`: dict mapping 36 item labels → correct answer (1–6)
- `SETS`: dict grouping items by set name ("A", "Ab", "B")
- Changes here affect all scoring — verify with unit tests after editing.

### norms.py
- **Default values are PLACEHOLDER** — replaced when user uploads a `data/norms.csv` via the Norme page.
- `load_norm_table()`: returns norms from CSV if present, otherwise placeholder table.
- `save_norms_csv(bytes)`: validates and saves uploaded CSV to `data/norms.csv`.
- `is_using_placeholder()`: True if CSV is absent or invalid.
- `get_norms_csv_path()`: returns the Path to the CSV file.
- `_get_age_col()`: dynamically builds age-band → column-index mapping from loaded table.
- `AGE_BANDS`: 20 supported bands — 18 six-month intervals (`"3;0-3;6"` … `"11;6-12;0"`) + `"Adulti"` + `"Anziani"`. Only bands present in the CSV get mapped.
- `compute_age(birth_date, test_date)`: returns `(years, months)` with day-level precision.
- `age_to_band(age_years, age_months)`: maps age to the correct 6-month band.
- CSV headers use the `"N;M-N;M"` notation (optionally prefixed with `"Età "`). Mapped by header label, not by column position.
- `NORM_TABLE`: static fallback pointing to `_PLACEHOLDER_TABLE` — always prefer `load_norm_table()`.

### scoring.py
- `ScoringResult`: dataclass holding scores, demographics, norms, and discrepancy index.
- `ScoringResult.responses`: original subject responses preserved for PDF fidelity and persistence.
- `normalize_response()`: central input normalization for item values; valid domain is integer 1–6, otherwise `None`.
- `ScoringResult.discrepancy`: float = max(set scores) – min(set scores).
- `ScoringResult.discrepancy_flag`: `""` (ok), `"attenzione"` (Δ ≥ 4), `"significativa"` (Δ ≥ 6).
- `score_responses()`: pure scoring without norms.
- `score_with_norms()`: scoring + percentile lookup. Accepts `age_years` + `age_months` (or direct `age_band`).

### charts.py
- Color palette: A = `#2980B9`, Ab = `#E67E22`, B = `#27AE60`
- All functions return `go.Figure` — the page layer calls `st.plotly_chart()`.
- `total_bar()` exists but is not currently used in any page.

### pdf_report.py
- fpdf2 uses Helvetica (built-in) — **no Unicode support**.
- Always pass text through `_sanitize()` before writing to PDF.
- `generate_pdf()` returns `bytes` (wrapped with `bytes(pdf.output())`).
- Charts are displayed interactively via Plotly in the Streamlit UI; they are **not** embedded in the PDF.
- Discrepancy section is included when `result.discrepancy > 0`.
- Footer/disclaimer must stay aligned with whether norms are placeholder or loaded from CSV.

### database.py
- SQLite at `data/sessions.db`, auto-created by `init_db()`.
- `save_result()` serializes responses as JSON in the `risposte` column.
- `subject_to_result()` reconstructs `ScoringResult` from a DB row.
- `DB_PATH` is exported for use by the Database page (backup/restore).
