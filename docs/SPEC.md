# CPM Scoring Tool — Specifica Corrente

Versione documento: 2026-03-18
Stato: allineato al codice attuale

## Obiettivo

Applicazione Streamlit locale per automatizzare il flusso CPM:

inserimento risposte -> scoring -> percentile -> grafici -> salvataggio -> PDF

Target principale:
- dottorandi
- docenti e ricercatori di psicologia
- piccoli team accademici con bassa competenza tecnica

## Scope implementato

### 1. Scoring singolo
- anagrafica essenziale
- inserimento risposte tramite 3 `st.data_editor`
- punteggi per set A, Ab, B
- totale grezzo
- percentile e descrizione qualitativa quando la fascia età è disponibile
- indice di discrepanza tra set
- grafici interattivi
- salvataggio DB e PDF

### 2. Batch scoring
- input CSV o Excel
- template CSV scaricabile
- validazione colonne item
- normalizzazione risposte e date
- risultati tabellari con export CSV/Excel
- salvataggio massivo nel DB

### 3. Database locale
- storage SQLite in `data/sessions.db`
- ricerca e filtri
- export completo e anonimizzato
- cancellazione record
- backup e restore con validazione schema

### 4. Report PDF
- generazione singola da record DB
- ZIP batch per tutti i soggetti
- grafici inclusi se `kaleido` è disponibile
- testo sanitizzato ASCII per compatibilità `fpdf2` + Helvetica

### 5. Norme
- fallback con valori di esempio integrato
- caricamento CSV da pagina Norme
- mapping delle colonne età guidato dagli header CSV
- download norme attuali e reset ai valori di esempio

### 6. Guida utente
- guida rapida disponibile nel file `docs/GUIDA.md`
- stessa guida consultabile nella home dell'app (expander)
- home con navigazione compatta a link diretti verso le 5 pagine
- stato norme (placeholder/personalizzate) nella sidebar globale

## Vincoli operativi

- `core/` non importa mai `streamlit`
- uso locale/offline o su rete fidata
- nessuna autenticazione o gestione multi-utente
- `pandas < 3.0`
- PDF solo con caratteri ASCII sanitizzati
- valori normativi reali non inclusi nel repository

## Architettura minima

```text
app.py + pages/      UI Streamlit
core/                logica pura di scoring, norme, PDF, DB
data/                SQLite locale + eventuale norms.csv
tests/               pytest + Playwright
```

## Pattern applicativi da preservare

- pulsanti Streamlit sempre nel widget tree, con `on_click` e `disabled`
- nella pagina Scoring il valore utile del `st.data_editor` è il DataFrame restituito dal widget; non usare direttamente lo stato raw del widget come se fosse sempre un DataFrame
- le norme CSV si validano prima del salvataggio e si mappano per header, non per posizione
- UI leggera: niente expander "come usare questa pagina" — le istruzioni sono nella Guida; niente info box "prossimo passo" dopo ogni azione
- stato norme (placeholder / personalizzate) visibile nella sidebar, non ripetuto in ogni pagina
- home con navigazione compatta (page_link + caption), guida completa accessibile via expander

## Qualità attuale verificata

- unit test `pytest`: 47 passati
- E2E Playwright: passati sui flussi Home, Scoring, Batch, Database, Report, Norme
- startup Streamlit verificato

## Fuori scope attuale

- autenticazione
- deployment server multi-utente
- confronto longitudinale tra soggetti
- supporto SPM/APM

Per la lista completa delle evoluzioni pianificate, vedere `docs/ROADMAP.md`.

## Riferimenti

- Belacchi C., Scalisi T.G., Cannoni E., Cornoldi C. (2008). CPM – Coloured Progressive Matrices. OS Firenze.
- Streamlit
- Plotly
- fpdf2
