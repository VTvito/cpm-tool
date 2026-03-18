---
description: "Use when writing or modifying tests — unit tests (pytest) or E2E tests (Playwright). Covers Streamlit's DOM structure, selector patterns, and unit test conventions."
applyTo: "tests/**/*.py"
---
# Testing Guidelines

## Unit Tests (pytest)

File: `tests/test_core.py` — 49 tests covering all `core/` modules.

### Running
```bash
python -m pytest tests/test_core.py -v
```

### Conventions
- Tests use `monkeypatch` to redirect `DB_PATH` and `_NORMS_CSV_PATH` to temp directories.
- Each test class covers one module: `TestAnswerKey`, `TestScoring`, `TestNorms`, `TestPDF`, `TestDatabase`, `TestCharts`.
- Database tests use `autouse` fixture to create a fresh temp DB per test.

### Adding Tests
- For scoring edge cases, use `score_responses()` (pure) or `score_with_norms()` (with percentile).
- Prefer exercising `normalize_response()` behavior through `score_responses()` inputs rather than testing UI-only logic.
- For PDF tests, assert `isinstance(result, bytes)` and check PDF header `b"%PDF-"`.
- For norms CSV tests, use `monkeypatch.setattr("core.norms._NORMS_CSV_PATH", tmp_path / "norms.csv")`.

## Playwright E2E Tests

File: `tests/test_playwright.py` — tests run against a live Streamlit server at `http://localhost:8501`.

Smoke file: `tests/smoke_test.py` — lightweight live page-load check. Intended to be run directly when a local server is already active.

### Setup
```bash
pip install playwright
playwright install chromium
streamlit run app.py            # Run in a separate terminal; server must already be up
python tests/test_playwright.py
```

Optional smoke run:
```bash
python tests/smoke_test.py
```

### Streamlit DOM Selectors

Streamlit renders custom components — standard HTML selectors won't work:

| Widget | Selector |
|--------|----------|
| Selectbox | `div[data-testid="stSelectbox"]` with inner `p:text-is("Label")` |
| Button | `button:has-text("Button Text")` |
| Download button | `[data-testid="stDownloadButton"]` (it's a `<div>`, not `<button>`) |
| File uploader | `[data-testid="stFileUploader"]` |
| DataFrame / data_editor | `div[data-testid="stDataFrame"]` |
| Plotly chart | `div.js-plotly-plot` |
| Expander | `[data-testid="stExpander"]` |

### Data Editor Note

The Scoring page uses `st.data_editor` instead of individual selectboxes. The data_editor renders as `stDataFrame` elements in the DOM. Programmatic cell editing requires complex DOM interactions (click cell → type value → press Enter). The E2E tests verify data_editor presence but do not fill individual cells.

### Timing
- Use `page.wait_for_timeout(ms)` after navigation and widget interactions.
- Initial page load: 4000ms. After button click: 3000–5000ms. After smaller interactions: 200–500ms.
- For PDF/report generation, prefer polling for success/download state over a single fixed wait.

### Screenshots
Test screenshots are saved to `tests/screenshots/` (gitignored).

### Smoke Behavior
- `tests/smoke_test.py` assumes Streamlit is already running on `localhost:8501`.
- When collected under `pytest` without a running server, it may skip at module level.
- Prefer running it directly as a manual smoke check rather than treating it as the main regression suite.
