# CPM Scoring Tool — Project Guidelines

## Overview

Streamlit web app for automatic scoring of **Raven's Coloured Progressive Matrices (CPM)**.
Target users: small psychology research teams (2–5 people), non-technical.
Language: Italian UI, Italian code comments, English code identifiers.

## Tech Stack

| Component | Technology | Version Notes |
|-----------|------------|---------------|
| Framework | Streamlit | ≥ 1.55, multi-page via `pages/` directory |
| Charts | Plotly | Interactive; kaleido for PNG export to PDF |
| PDF | fpdf2 | Helvetica only — **no Unicode** (use `_sanitize()`) |
| Database | SQLite | Single-file at `data/sessions.db` |
| Data | pandas | **Must be < 3.0** (Streamlit incompatibility) |
| Python | 3.13+ | Type hints use `X | Y` syntax (PEP 604) |

## Architecture

```
app.py                  # Entry point + home page (st.page_link navigation)
streamlit_ui/           # Shared UI layer — no core/ imports
  shell.py              #   configure_page(), CSS tokens, dark sidebar + nav links
core/                   # Pure logic — no Streamlit imports
  answer_key.py         # 36-item answer key (3 sets × 12)
  norms.py              # Normative tables — CSV loading + placeholder fallback
  scoring.py            # ScoringResult dataclass + scoring + discrepancy index
  charts.py             # Plotly chart builders
  pdf_report.py         # A4 PDF generation with fpdf2
  database.py           # SQLite CRUD
pages/                  # Streamlit pages (auto-discovered)
  1_📝_Scoring.py       # Single subject scoring (text input grid)
  2_📊_Batch.py         # CSV/Excel batch scoring
  3_🗄️_Database.py      # Database viewer/export/backup/restore
  4_📄_Report.py        # PDF report generator (single + batch ZIP)
  5_📏_Norme.py         # Normative tables viewer + Excel/CSV upload and management
data/                   # Runtime data (gitignored)
  norms_template.csv    # CSV template for norms input
tests/                  # Tests
  test_core.py          # pytest unit tests for core/ (49 tests)
  test_playwright.py    # Playwright E2E tests
```

**Separation rule**: `core/` modules must NEVER import `streamlit`. All Streamlit interactions stay in `pages/` and `app.py`.

## Critical Patterns

### Streamlit session_state & Buttons

Buttons that depend on other button results **must use `on_click` callbacks**, not inline `if st.button():` blocks. Callbacks execute BEFORE the page re-renders, so state is ready for the next render cycle.

**NEVER** put buttons inside conditional blocks (`if show_results:`) — Streamlit resets the entire session when the widget tree is inconsistent between runs.

Pattern:
```python
def _on_action():
    st.session_state["result"] = compute()

st.button("Go", on_click=_on_action)  # Always in widget tree

if "result" in st.session_state:       # Conditional DISPLAY only
    st.write(st.session_state["result"])
```

### UX Pattern: Lean UI

Keep pages clean and focused:
- **No per-page help expanders** — user guidance lives in `docs/GUIDA.md` and the Home expander only.
- **No "next step" info boxes** after actions (save, upload, generate) — trust the user to navigate.
- **Norms status** (placeholder / custom) is shown **once in the sidebar** (`streamlit_ui/shell.py → _render_sidebar()`), not repeated on individual pages.
- **Sidebar navigation** (`st.page_link` for all 5 pages + Home) lives in `_render_sidebar()` — do not duplicate nav in page bodies.
- Advanced operations and secondary charts go in expanders or lower sections.

### Shared UI Shell

`streamlit_ui/shell.py` is the single source of truth for page setup:
- `configure_page(title, icon)` calls `st.set_page_config(initial_sidebar_state="auto")` and sets page title as `"<title> · CPM"`.
- `_inject_styles()` contains all CSS; design tokens use the `--c-*` prefix (e.g. `--c-primary`, `--c-ink`, `--c-surface`).
- `_render_sidebar()` renders the dark navy sidebar with navigation links and norms status badge.
- Every page must call `configure_page()` as its first statement — before any other `st.*` call.

### Scoring Page data_editor

On current Streamlit versions, the raw widget state for `st.data_editor` may be a dict-like structure rather than the edited DataFrame itself.
For the Scoring page, persist the DataFrame returned by `st.data_editor(...)` in dedicated `resp_values_*` keys and read those keys inside callbacks and counters.

### PDF Generation

fpdf2 with Helvetica font cannot render Unicode. Always sanitize text through `core.pdf_report._sanitize()` before writing to PDF cells. `generate_pdf()` returns `bytes` (not `bytearray`).

### Normative Tables

Norms default to **PLACEHOLDER** values in `core/norms.py`. If a `data/norms.csv` file exists, norms are loaded from CSV instead. Users manage norms via the **📏 Norme** page (upload/download/reset). Key functions:
- `load_norm_table()` — returns current norms (CSV or placeholder)
- `save_norms_csv(bytes)` — validates and saves uploaded CSV
- `is_using_placeholder()` — True if CSV is absent/invalid
- `get_norms_csv_path()` — returns the Path to the CSV file

### Scoring & Discrepancy

`ScoringResult` includes `discrepancy` (float) and `discrepancy_flag` (str):
- `discrepancy` = max(set scores) – min(set scores)
- `discrepancy_flag`: `""` (ok), `"attenzione"` (Δ ≥ 4), `"significativa"` (Δ ≥ 6)

## Build & Run

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows
pip install -r requirements.txt
streamlit run app.py
```

> **Streamlit Cloud deploy**: `packages.txt` lists Linux apt packages required for kaleido
> (`libgbm1`, `libnss3`, `libatk-bridge2.0-0`). No comments allowed in `packages.txt`.

## Testing

Unit tests (no server needed):
```bash
python -m pytest tests/test_core.py -v
```

Full regression:
```bash
python -m pytest -q
```

E2E tests use Playwright (headless Chromium):
```bash
pip install playwright
playwright install chromium
python tests/test_playwright.py
```
The Streamlit server must be running on `localhost:8501` before running E2E tests.

Optional live smoke check:
```bash
python tests/smoke_test.py
```

## Conventions

- Color palette: Set A = `#2980B9` (blue), Set Ab = `#E67E22` (orange), Set B = `#27AE60` (green)
- Theme primary: `#0077B6` (configured in `.streamlit/config.toml`)
- All user-facing text in Italian
- `use_container_width=True` is deprecated in Streamlit ≥ 1.55 → migrate to `width='stretch'`
- Database auto-initializes on first access via `init_db()`
