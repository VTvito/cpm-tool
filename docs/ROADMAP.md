# CPM Scoring Tool — Roadmap Evolutiva

Versione documento: 2026-03-18

## Stato attuale

Il tool copre il workflow CPM completo: inserimento risposte, scoring singolo e batch,
percentili con norme CSV, grafici interattivi, database SQLite locale, report PDF.

UI refactored (2026-03-18): design system accademico pulito, sidebar navy con navigazione
completa, token CSS `--c-*`, home page con hero + banner workflow.

Deploy su Streamlit Cloud attivo (2026-03-18): auto-seed 15 soggetti demo al cold start
(DB vuoto), fix `sys.path` per compatibilità cloud, CSV export con BOM per Excel,
template batch in formato Excel.

Qualità verificata con 49 test standard + smoke/E2E browser separati sui flussi principali di tutte le pagine.

File di test inclusi in `samples/`: `batch_test.csv` (6 soggetti, inclusa discrepanza) e `norms_test.csv` (8 fasce Età 5-11 + Adulti).

`packages.txt` aggiornato con tutti i pacchetti apt richiesti da kaleido 1.x su Streamlit Cloud.

Valutazione complessiva: **9 / 10**

---

## Ciclo 1 — Priorità alta

Interventi consigliati per il prossimo stream di sviluppo.

### 1.1 Autenticazione leggera

- **Cosa**: login con utente/password per proteggere l'accesso quando l'app è online.
- **Perché**: i dati dei soggetti sono dati sensibili. Senza autenticazione, chiunque
  abbia l'URL può accedere al database.
- **Come**: valutare `streamlit-authenticator` o l'API nativa `st.experimental_user`.
- **Effort**: basso-medio.

### 1.2 Confronto longitudinale

- **Cosa**: poter confrontare lo scoring dello stesso soggetto in date diverse (pre/post trattamento).
- **Perché**: è una delle richieste più frequenti in contesti di ricerca e intervento.
- **Come**: aggiungere un selettore multi-record per soggetto nel Database o in una nuova
  pagina dedicata, con grafico temporale e delta automatico.
- **Effort**: medio.

### 1.3 Modifica record salvati

- **Cosa**: permettere l'editing in-place di un record già nel database.
- **Perché**: attualmente l'unica opzione è cancellare e reinserire.
- **Come**: aggiungere una modale o expander con form pre-compilato nella pagina Database.
- **Effort**: basso.

### 1.4 Grafici nel Batch

- **Cosa**: aggiungere grafici di distribuzione nella pagina Batch
  (istogramma punteggi totali, boxplot per set, distribuzione percentili).
- **Perché**: chi fa batch scoring su un campione vuole subito una visione d'insieme.
- **Come**: nuova sezione con `st.expander` nella pagina Batch, usando le funzioni
  Plotly già presenti in `core/charts.py` (o nuove dedicate).
- **Effort**: basso.

---

## Ciclo 2 — Priorità media

Interventi per consolidare e ampliare il valore del tool.

### 2.1 Confronto tra gruppi

- **Cosa**: confronto statistico tra due sottogruppi (es. M/F, classi, fasce d'età).
- **Perché**: utile per tesi di laurea, paper e report di ricerca.
- **Come**: nuova pagina o sezione in Batch con test t / Mann-Whitney e grafici
  comparativi. Usare `scipy.stats` (nuova dipendenza).
- **Effort**: medio.

### 2.2 Supporto SPM / APM

- **Cosa**: estendere il tool alle Standard e Advanced Progressive Matrices.
- **Perché**: amplierebbe il target oltre i 3-11 anni / screening di base.
- **Come**: la struttura `core/` lo facilita: servono nuovi `answer_key`, nuove
  tabelle normative e adattamento delle pagine UI.
- **Effort**: medio-alto.

### 2.3 Backup automatico del database

- **Cosa**: copia automatica del DB prima di ogni sessione o a intervalli regolari.
- **Perché**: il backup manuale è disponibile ma facilmente dimenticato.
- **Come**: copia timestampata del file `.db` su `data/backups/` con rotazione
  (es. ultimi 5 backup).
- **Effort**: basso.

### 2.4 Accessibilità (a11y)

- **Cosa**: verifica contrasti WCAG AA, test screen reader, etichette `aria-label`.
- **Perché**: Streamlit ha limitazioni ma i margini di miglioramento ci sono.
- **Come**: audit con Lighthouse/axe, fix puntuali su colori e heading.
- **Effort**: basso-medio.

### 2.5 Tastiera avanzata nello Scoring

- **Cosa**: focus chain ancora più efficiente per inserimento rapido item-per-item.
- **Perché**: lo Scoring è già ottimizzato con campi rapidi e form submit, ma un flusso quasi da data-entry ridurrebbe ancora il tempo operativo.
- **Come**: valutare componenti/custom JS molto mirati solo se Streamlit base non basta, senza compromettere stabilità e deploy.
- **Effort**: medio.

---

## Ciclo 3 — Nice-to-have

### 3.1 Dark mode

- Aggiornare `.streamlit/config.toml` con tema scuro opzionale.

### 3.2 Multilingua (i18n)

- Introdurre un layer di traduzione per supportare almeno italiano + inglese.
- Non urgente finché il target è accademico italiano.

### 3.3 Persistenza cloud per deploy online

- Migrare da SQLite locale a un DB esterno (es. Supabase, Turso, PostgreSQL)
  per uso su Streamlit Community Cloud dove il filesystem è effimero.

### 3.4 Export in formati accademici

- Export tabelle risultati in formato LaTeX o APA-style per inserimento diretto
  in tesi e paper.

---

## Note sul deploy

Se il progetto viene pubblicato su **Streamlit Community Cloud** o ambienti equivalenti,
il database SQLite locale resta effimero: i dati si perdono quando l'app va in sleep
o viene riavviata.
Per persistenza dati in produzione, valutare la migrazione a DB esterno (vedi 3.3).

I dati inseriti tramite i test E2E (Playwright) restano locali alla macchina di sviluppo
e non si propagano automaticamente a eventuali istanze deployate.
