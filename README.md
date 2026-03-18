# CPM Scoring Tool

Tool Streamlit per lo scoring automatico delle Matrici Progressive Colorate di Raven (CPM), pensato per uso accademico locale da parte di ricercatori, dottorandi e docenti di psicologia.

## Avvio rapido

Prerequisiti:
- Python 3.13+

Installazione:

```bash
pip install -r requirements.txt
```

Avvio:

```bash
streamlit run app.py
```

App disponibile su http://localhost:8501

## Cosa include

- Scoring singolo con griglia risposte, grafici, discrepanza tra set e PDF
- Batch scoring da CSV/Excel con export risultati
- Database SQLite locale con filtri, export anonimizzato, backup e restore
- Report PDF singolo e ZIP batch
- Gestione norme da CSV con fallback a valori di esempio
- Guida rapida consultabile direttamente nella home dell'app

## Norme

Il progetto usa valori di esempio finché non viene caricato un file `data/norms.csv` dalla pagina Norme.

Prima di uso clinico o di ricerca, caricare le norme ufficiali dal manuale di riferimento:

> Belacchi C., Scalisi T.G., Cannoni E., Cornoldi C. (2008).
> CPM – Coloured Progressive Matrices. Organizzazioni Speciali, Firenze.

## Documenti essenziali

- `docs/SPEC.md`: specifica corrente, ridotta e allineata al codice
- `docs/GUIDA.md`: guida utente in linguaggio semplice
- `docs/ROADMAP.md`: roadmap evolutiva con cicli di miglioramento pianificati
- `.github/copilot-instructions.md`: regole di sviluppo condivise

## Test

Unit test:

```bash
python -m pytest tests/test_core.py -v
```

Suite completa:

```bash
python -m pytest -q
```

Nota: la suite `pytest` raccoglie anche smoke test ed E2E browser. Se Streamlit non è attivo su `localhost:8501`, questi test vengono saltati automaticamente.

E2E:

```bash
playwright install chromium
streamlit run app.py
python tests/test_playwright.py
```

Smoke test rapido con server attivo:

```bash
python tests/smoke_test.py
```

## Note operative

- Uso previsto: locale/offline o su rete fidata
- Nessuna autenticazione o multi-utente
- Dati salvati in `data/sessions.db`
- PDF con font Helvetica: testo sanitizzato ASCII
- Stato norme mostrato in sidebar; la pagina Norme serve per gestione CSV e consultazione
- `tests/smoke_test.py` è pensato come controllo live rapido con server attivo su `localhost:8501`
