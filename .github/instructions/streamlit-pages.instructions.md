---
description: "Use when modifying Streamlit pages, adding widgets, handling session_state, or creating new pages. Covers the critical callback pattern, widget-tree stability, and data_editor usage."
applyTo: "pages/**/*.py"
---
# Streamlit Pages Guidelines

## Session State — The Callback Pattern

Streamlit re-executes the entire page script on every interaction. This means:

1. **Buttons that mutate state** must use `on_click=callback` — the callback runs BEFORE the page re-render, so subsequent widgets see updated state.
2. **Never put buttons inside conditional blocks** (`if "result" in st.session_state:`) — if the condition flips between runs, Streamlit can't reconcile the widget tree and resets the entire session.
3. **Display can be conditional**, buttons cannot.

```python
# CORRECT
def _on_calc():
    st.session_state["result"] = compute()

st.button("Calcola", on_click=_on_calc)           # Always rendered
st.button("Salva", disabled=not has_result, on_click=_on_save)  # Always rendered, disabled when no result

if "result" in st.session_state:
    st.write(st.session_state["result"])            # Conditional display only

# WRONG — will cause session reset
if "result" in st.session_state:
    st.button("Salva", on_click=_on_save)           # Button appears/disappears → crash
```

## Widget Keys

- Every widget that stores user input uses a `key=` parameter stored in `session_state`.
- Naming convention: `sc_` prefix for Scoring page, `batch_` for Batch, `db_` for Database, `rpt_` for Report, `norm_` for Norme.

## Data Editor Pattern (Scoring Page)

The Scoring page uses `st.data_editor` (3 grids: Set A, Ab, B) instead of 36 individual selectboxes.
- Widget keys: `resp_editor_A`, `resp_editor_Ab`, `resp_editor_B`
- Persist the DataFrame returned by `st.data_editor(...)` in dedicated keys such as `resp_values_A`, `resp_values_Ab`, `resp_values_B`.
- In callbacks and counters, read the persisted `resp_values_*` DataFrames rather than assuming `st.session_state[editor_key]` is itself a DataFrame.
- The `_on_reset` callback should clear both widget keys and persisted DataFrame keys.

## Imports

Pages import from `core/` only. Never import `streamlit` inside `core/` modules.

## UX Pattern — Lean UI

- Keep the primary task and primary CTA visible without requiring expanders.
- Move advanced operations, maintenance actions, or secondary charts into expanders or lower sections.
- Do NOT add per-page "ℹ️ Come usare questa pagina" expanders — guidance lives in `docs/GUIDA.md` and the Home page expander.
- Do NOT add "Prossimo passo" / next-step info boxes after actions — keep the UI quiet after saves and uploads.
- Norms status (placeholder / custom) is shown once in the sidebar (`streamlit_ui/shell.py`), not on individual pages.

## Shared UI Shell — `configure_page()`

All pages must call `configure_page(title, icon)` as their **first** statement (before any widget).
This function is in `streamlit_ui/shell.py` and:
- Calls `st.set_page_config(layout="wide", initial_sidebar_state="auto")`.
- Formats the browser tab title as `"<title> · CPM"`.
- Injects all CSS (design tokens use `--c-*` prefix: `--c-primary`, `--c-ink`, `--c-surface`, etc.).
- Renders the dark navy sidebar with `st.page_link` navigation for all 5 pages + Home and the norms status badge.

**Do not** call `st.set_page_config()` directly in pages.

## Deprecation: use_container_width

In Streamlit ≥ 1.55, use `width='stretch'` instead of `use_container_width=True` and `width='content'` instead of `use_container_width=False`.

## Page-Specific Features

### Database (Page 3)
- Search by name/surname, advanced filters, anonymized export (S001…), backup/restore with SQLite schema validation.

### Report (Page 4)
- Single PDF generation + batch ZIP generation for all subjects.

### Norme (Page 5)
- CSV norms upload/download/reset. Uses `on_click` callbacks for upload and reset actions.
- Keep reset controls always rendered and disable them when not applicable.
