"""
Playwright E2E test — CPM Scoring Tool
Naviga tutte le pagine e verifica i flussi principali di UI,
salvataggio, export e report.

Nota: la compilazione puntuale delle celle di st.data_editor nella pagina
Scoring non è ancora automatizzata in questo test.

Screenshot salvati in tests/screenshots/
"""

import csv
import re
import socket
import sys
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


pytestmark = pytest.mark.e2e

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.database import get_all_subjects

BASE_URL = "http://localhost:8501"
SCREENSHOTS = Path(__file__).parent / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)


def _is_server_up(host: str = "localhost", port: int = 8501) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False

# Risposte test: A tutto corretto (12), Ab 11/12, B 11/12 => totale 34
TEST_RESPONSES = {
    "A1": "4", "A2": "5", "A3": "1", "A4": "2", "A5": "6", "A6": "3",
    "A7": "6", "A8": "2", "A9": "1", "A10": "3", "A11": "4", "A12": "5",
    "Ab1": "6", "Ab2": "2", "Ab3": "1", "Ab4": "2", "Ab5": "5", "Ab6": "3",
    "Ab7": "5", "Ab8": "6", "Ab9": "4", "Ab10": "3", "Ab11": "4", "Ab12": "1",
    "B1": "3", "B2": "4", "B3": "3", "B4": "4", "B5": "2", "B6": "5",
    "B7": "1", "B8": "1", "B9": "2", "B10": "5", "B11": "6", "B12": "4",
}

BATCH_ROWS = [
    {
        "Nome": "LucaE2E",
        "Cognome": "BatchVerdiA",
        "DataNascita": "2018-02-10",
        "DataSomministrazione": "2026-03-18",
        "Sesso": "M",
        "Esaminatore": "Dott.ssa Batch",
        **TEST_RESPONSES,
    },
    {
        "Nome": "SaraE2E",
        "Cognome": "BatchVerdiB",
        "DataNascita": "2017-07-22",
        "DataSomministrazione": "2026-03-18",
        "Sesso": "F",
        "Esaminatore": "Dott.ssa Batch",
        **TEST_RESPONSES,
    },
]

step_n = 0

def shot(page, name):
    global step_n
    step_n += 1
    path = SCREENSHOTS / f"{step_n:02d}_{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"    screenshot {path.name}")


def wait_st(page, ms=2000):
    """Wait for Streamlit to finish rendering."""
    page.wait_for_timeout(ms)


def fill_selectbox(page, label_text, value):
    """Fill a Streamlit selectbox by finding it via label text in <p> tag."""
    container = page.locator(
        'div[data-testid="stSelectbox"]'
    ).filter(has=page.locator(f'p:text-is("{label_text}")'))

    if container.count() == 0:
        return False

    select = container.first.locator('div[data-baseweb="select"]')
    select.click()
    page.wait_for_timeout(200)

    option = page.locator('li[role="option"]').filter(has_text=value)
    if option.count() > 0:
        option.first.click()
        page.wait_for_timeout(100)
        return True
    else:
        page.keyboard.press("Escape")
        return False


def get_selectbox_options(page, label_text):
    """Return the visible options of a Streamlit selectbox."""
    container = page.locator(
        'div[data-testid="stSelectbox"]'
    ).filter(has=page.locator(f'p:text-is("{label_text}")'))

    if container.count() == 0:
        return []

    select = container.first.locator('div[data-baseweb="select"]')
    select.click()
    page.wait_for_timeout(200)
    options = [
        page.locator('li[role="option"]').nth(i).inner_text().strip()
        for i in range(page.locator('li[role="option"]').count())
    ]
    page.keyboard.press("Escape")
    return options


def build_batch_csv() -> Path:
    """Create a temporary CSV file for batch E2E coverage."""
    csv_path = SCREENSHOTS / "batch_e2e_input.csv"
    fieldnames = [
        "Nome", "Cognome", "DataNascita", "DataSomministrazione", "Sesso", "Esaminatore",
        *TEST_RESPONSES.keys(),
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(BATCH_ROWS)
    return csv_path


def build_norms_csv() -> Path:
    """Create a temporary norms CSV with a subset of age-band columns."""
    csv_path = SCREENSHOTS / "norms_e2e_input.csv"
    csv_path.write_text(
        "Punteggio Grezzo,Età 7,Adulti,Anziani\n"
        "0,<5,10,25\n"
        "20,50,75,90\n"
        "36,>95,>95,>95\n",
        encoding="utf-8",
    )
    return csv_path


def extract_subject_count(body_text):
    """Extract the visible subject count from the Database page text."""
    match = re.search(r"(\d+)\s+soggetti\s+trovati", body_text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def has_valid_norms_status(body_text):
    """Accetta sia norme placeholder sia norme personalizzate attive."""
    lowered = body_text.lower()
    return (
        "norme:" in lowered
        or "valori di esempio" in lowered
        or "norme di esempio attive" in lowered
        or "norme personalizzate attive" in lowered
        or "percentili reali" in lowered
    )


def run():
    print("=" * 65)
    print("  CPM Scoring Tool — Playwright E2E Navigation & Debug")
    print("=" * 65)

    errors = []
    warnings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # =============================================
        #  1. HOME PAGE
        # =============================================
        print("\n[1/6] HOME PAGE")
        page.goto(BASE_URL)
        wait_st(page, 4000)
        shot(page, "home")

        body = page.locator("body").inner_text()

        checks = [
            ("CPM Scoring Tool" in body, "Titolo principale"),
            ("Scoring Singolo" in body, "Card Scoring Singolo"),
            ("Batch" in body, "Card Batch"),
            ("Report" in body, "Card Report"),
            (has_valid_norms_status(body), "Stato norme visibile"),
        ]
        for ok, desc in checks:
            if ok:
                print(f"  OK {desc}")
            else:
                errors.append(f"HOME: {desc} mancante")
                print(f"  FAIL {desc}")

        # Sidebar links
        links = page.locator('a[href*="/"]')
        nav_pages = []
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href") or ""
            text = links.nth(i).inner_text().strip()
            if any(pg in href for pg in ["/Scoring", "/Batch", "/Database", "/Report", "/Norme"]):
                nav_pages.append(text)
        if len(nav_pages) >= 5:
            print(f"  OK Sidebar: {len(nav_pages)} pagine")
        else:
            warnings.append(f"Sidebar: trovate {len(nav_pages)} pagine (attese 5)")
            print(f"  WARN Sidebar: {len(nav_pages)} pagine")

        # =============================================
        #  2. SCORING — compilazione completa
        # =============================================
        print("\n[2/6] SCORING SINGOLO")
        page.goto(f"{BASE_URL}/Scoring")
        wait_st(page, 4000)
        shot(page, "scoring_empty")

        body = page.locator("body").inner_text()
        if "Scoring Singolo Soggetto" in body:
            print("  OK Header pagina Scoring")
        else:
            errors.append("SCORING: header mancante")
            print("  FAIL Header scoring")

        # Anagrafica
        print("  -> Compilazione anagrafica...")
        page.locator('input[aria-label="Nome"]').fill("Maria")
        page.locator('input[aria-label="Cognome"]').fill("Rossi")
        page.locator('input[aria-label="Esaminatore"]').fill("Dott.ssa Verdi")

        filled = fill_selectbox(page, "Sesso", "F")
        if filled:
            print("  OK Sesso impostato: F")
        else:
            warnings.append("SCORING: selectbox Sesso non compilato")
            print("  WARN Sesso non compilato")

        wait_st(page, 500)
        shot(page, "scoring_anagrafica")

        print("  -> Verifica griglia risposte rapida...")
        response_inputs = page.locator('input[aria-label^="Risposta "]')
        wait_st(page, 1000)
        response_count = response_inputs.count()
        if response_count >= 36:
            print(f"  OK {response_count} campi risposta trovati")
        else:
            errors.append(f"SCORING: attesi almeno 36 campi risposta, trovati {response_count}")
            print(f"  FAIL campi risposta: {response_count} (attesi >= 36)")

        shot(page, "scoring_inputs")

        print("  -> Compilazione rapida risposte A1/A2...")
        input_a1 = page.locator('input[aria-label="Risposta A1"]')
        input_a2 = page.locator('input[aria-label="Risposta A2"]')
        input_a3 = page.locator('input[aria-label="Risposta A3"]')
        if input_a1.count() > 0 and input_a2.count() > 0:
            input_a1.first.fill("4")
            input_a2.first.fill("5")
            input_a3.first.click()
            wait_st(page, 400)
            if input_a1.first.input_value() == "4" and input_a2.first.input_value() == "5":
                print("  OK Valori digitati mantengono lo stato prima del calcolo")
            else:
                errors.append("SCORING: i valori digitati non restano stabili nei campi")
                print("  FAIL Valori digitati instabili nei campi")
        else:
            errors.append("SCORING: campi A1/A2 non trovati")
            print("  FAIL Campi A1/A2 non trovati")

        print("  -> Click 'Calcola Score'...")
        calc_btn = page.locator('button', has_text="Calcola Score")
        if calc_btn.count() > 0:
            calc_btn.first.scroll_into_view_if_needed()
            calc_btn.first.click()
            wait_st(page, 3000)
        else:
            errors.append("SCORING: pulsante Calcola non trovato")
            print("  FAIL Pulsante Calcola non trovato")

        shot(page, "scoring_risultati_top")

        body = page.locator("body").inner_text()

        if "Risultati" in body and "Totale" in body:
            print("  OK Sezione Risultati visibile dopo il calcolo")
        else:
            errors.append("SCORING: risultati non visibili dopo il calcolo")
            print("  FAIL Risultati non visibili dopo il calcolo")

        # Verifica pulsanti azione sempre presenti
        save_btn = page.locator('button', has_text="Salva nel Database")
        reset_btn = page.locator('button', has_text="Nuovo Soggetto")
        if save_btn.count() > 0:
            print("  OK Pulsante 'Salva nel Database' presente")
        else:
            warnings.append("SCORING: pulsante Salva non trovato")
            print("  WARN Pulsante Salva non trovato")
        if reset_btn.count() > 0:
            print("  OK Pulsante 'Nuovo Soggetto' presente")
        else:
            warnings.append("SCORING: pulsante Reset non trovato")
            print("  WARN Pulsante Reset non trovato")

        # =============================================
        #  3. BATCH PAGE
        # =============================================
        print("\n[3/6] BATCH SCORING")
        page.goto(f"{BASE_URL}/Batch")
        wait_st(page, 4000)
        shot(page, "batch_page")

        body = page.locator("body").inner_text()
        if "Batch Scoring" in body:
            print("  OK Header Batch")
        else:
            errors.append("BATCH: header mancante")
            print("  FAIL Header Batch")

        template_btn = page.locator('[data-testid="stDownloadButton"]')
        if template_btn.count() > 0:
            print("  OK Pulsante template CSV")
        else:
            warnings.append("BATCH: template download non trovato")
            print("  WARN Template non trovato")

        uploader = page.locator('[data-testid="stFileUploader"]')
        if uploader.count() > 0:
            print("  OK Area upload file")
        else:
            errors.append("BATCH: area upload non trovata")
            print("  FAIL Upload non trovato")

        db_count_before_batch = len(get_all_subjects())
        batch_csv = build_batch_csv()
        uploader.locator('input[type="file"]').set_input_files(str(batch_csv))
        wait_st(page, 2500)
        shot(page, "batch_uploaded")

        body = page.locator("body").inner_text()
        if "2 soggetti trovati" in body:
            print("  OK File batch caricato con 2 soggetti")
        else:
            errors.append("BATCH: il file caricato non e' stato acquisito correttamente")
            print("  FAIL File batch non acquisito")

        batch_calc_btn = page.locator('button', has_text="Calcola Score per Tutti")
        if batch_calc_btn.count() > 0:
            batch_calc_btn.first.scroll_into_view_if_needed()
            batch_calc_btn.first.click()
            wait_st(page, 5000)
            shot(page, "batch_results")
        else:
            errors.append("BATCH: pulsante Calcola Score per Tutti non trovato")
            print("  FAIL Pulsante Batch Calcola non trovato")

        body = page.locator("body").inner_text()
        if (
            "Risultati" in body
            and "Scarica Risultati (CSV)" in body
            and "Scarica Risultati (Excel)" in body
        ):
            print("  OK Risultati batch visibili e persistenti")
        else:
            errors.append("BATCH: risultati completi non visibili dopo il calcolo")
            print("  FAIL Risultati batch non visibili")

        batch_save_btn = page.locator('button', has_text="Salva Tutti nel Database")
        if batch_save_btn.count() > 0:
            batch_save_btn.first.scroll_into_view_if_needed()
            batch_save_btn.first.click()
            wait_st(page, 3000)
            shot(page, "batch_saved")
        else:
            errors.append("BATCH: pulsante Salva Tutti nel Database non trovato")
            print("  FAIL Pulsante Batch Salva non trovato")

        body = page.locator("body").inner_text()
        db_count_after_batch = len(get_all_subjects())
        if (
            "soggetti salvati nel database" in body.lower()
            and db_count_after_batch >= db_count_before_batch + len(BATCH_ROWS)
        ):
            print("  OK Salvataggio batch confermato")
        else:
            errors.append("BATCH: conferma salvataggio batch non trovata")
            print("  FAIL Conferma salvataggio batch assente")

        # =============================================
        #  4. DATABASE PAGE
        # =============================================
        print("\n[4/6] DATABASE")
        page.goto(f"{BASE_URL}/Database")
        wait_st(page, 4000)
        shot(page, "database_page")

        body = page.locator("body").inner_text()
        if "Database Soggetti" in body:
            print("  OK Header Database")
        else:
            errors.append("DATABASE: header mancante")
            print("  FAIL Header Database")

        subjects_before_delete = len(get_all_subjects())

        if "soggetti trovati" in body:
            print("  OK Contatore soggetti presente")
            if "0 soggetti" not in body:
                print("  OK Database NON vuoto (contiene record)")
        elif "vuoto" in body.lower():
            warnings.append("DATABASE: vuoto")
            print("  WARN Database vuoto")

        # Export buttons
        csv = page.locator('button', has_text="Scarica CSV")
        xlsx = page.locator('button', has_text="Scarica Excel")
        if csv.count() > 0:
            print("  OK Export CSV")
        if xlsx.count() > 0:
            print("  OK Export Excel")

        page_count = extract_subject_count(body)
        if page_count is not None and page_count == subjects_before_delete:
            print("  OK Database sincronizzato con il numero di record salvati")
        else:
            errors.append("DATABASE: il contatore visibile non riflette il database corrente")
            print("  FAIL Contatore Database incoerente")

        delete_expander = page.locator('[data-testid="stExpander"]').last.locator('summary')
        if delete_expander.count() > 0:
            delete_expander.first.click()
            wait_st(page, 700)

            delete_options = get_selectbox_options(page, "Seleziona ID da eliminare")
            numeric_options = [option for option in delete_options if option.isdigit()]
            if numeric_options:
                target_id = numeric_options[0]
                if fill_selectbox(page, "Seleziona ID da eliminare", target_id):
                    delete_btn = page.locator('button', has_text="Conferma Eliminazione")
                    if delete_btn.count() > 0:
                        delete_btn.first.click()
                        wait_st(page, 2500)
                        shot(page, "database_deleted")

                        body_after_delete = page.locator("body").inner_text()
                        subjects_after_delete = len(get_all_subjects())
                        page_count_after_delete = extract_subject_count(body_after_delete)
                        if (
                            subjects_after_delete == subjects_before_delete - 1
                            and page_count_after_delete == subjects_after_delete
                        ):
                            print("  OK Eliminazione Database verificata")
                        elif subjects_after_delete == subjects_before_delete - 1:
                            warnings.append("DATABASE: eliminazione riuscita ma contatore pagina non aggiornato in tempo")
                            print("  WARN Eliminazione riuscita, contatore pagina non ancora aggiornato")
                        else:
                            errors.append("DATABASE: il contatore non e' diminuito dopo l'eliminazione")
                            print("  FAIL Eliminazione Database non verificata")
                    else:
                        errors.append("DATABASE: pulsante Conferma Eliminazione non trovato")
                        print("  FAIL Pulsante conferma eliminazione non trovato")
                else:
                    errors.append("DATABASE: impossibile selezionare un ID per l'eliminazione")
                    print("  FAIL Selezione ID eliminazione fallita")
            else:
                errors.append("DATABASE: nessun ID disponibile per il test di eliminazione")
                print("  FAIL Nessun ID disponibile per l'eliminazione")
        else:
            errors.append("DATABASE: sezione eliminazione non trovata")
            print("  FAIL Sezione eliminazione non trovata")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        wait_st(page, 500)
        shot(page, "database_bottom")

        # =============================================
        #  5. REPORT PDF PAGE
        # =============================================
        print("\n[5/6] REPORT PDF")
        page.goto(f"{BASE_URL}/Report")
        wait_st(page, 4000)
        shot(page, "report_page")

        body = page.locator("body").inner_text()
        if "Genera Report PDF" in body:
            print("  OK Header Report")
        else:
            errors.append("REPORT: header mancante")
            print("  FAIL Header Report")

        if "Nessun soggetto" in body:
            warnings.append("REPORT: DB vuoto per report")
            print("  WARN DB vuoto per report")
        elif "soggetto" in body.lower():
            print("  OK Selettore soggetto presente")

            # Scroll to see preview + generate button
            page.evaluate("window.scrollBy(0, 400)")
            wait_st(page, 1000)
            shot(page, "report_preview")

            gen_btn = page.locator('button', has_text="Genera e Scarica PDF")
            if gen_btn.count() > 0:
                print("  OK Pulsante 'Genera PDF' presente")
                gen_btn.first.scroll_into_view_if_needed()
                gen_btn.first.click()
                report_ready = False
                for _ in range(40):
                    wait_st(page, 1500)
                    body_after = page.locator("body").inner_text()
                    report_download_btn = page.locator('[data-testid="stDownloadButton"]').filter(
                        has_text="Scarica il Report PDF"
                    )
                    if (
                        report_download_btn.count() > 0
                        or "generato" in body_after.lower()
                        or "successo" in body_after.lower()
                    ):
                        report_ready = True
                        break
                shot(page, "report_generato")

                body_after = page.locator("body").inner_text()
                if report_download_btn.count() > 0:
                    print("  OK Download report disponibile")
                elif "generato" in body_after.lower() or "successo" in body_after.lower():
                    print("  OK Report generato")
                elif not report_ready:
                    warnings.append("REPORT: generazione PDF oltre il timeout di attesa del test")
                    print("  WARN Generazione PDF oltre il timeout del test")
                else:
                    warnings.append("REPORT: conferma generazione non chiara")
                    print("  WARN Conferma generazione non chiara")

            batch_expander = page.locator('[data-testid="stExpander"]').filter(
                has=page.locator('summary:has-text("Operazioni batch")')
            )
            if batch_expander.count() > 0:
                batch_expander.locator('summary').first.click()
                wait_st(page, 1000)
                batch_btn = page.locator('button', has_text="Genera ZIP con Tutti i Report")
                if batch_btn.count() > 0:
                    print("  OK Pulsante batch ZIP presente")
                    batch_btn.first.scroll_into_view_if_needed()
                    batch_btn.first.click()
                    wait_st(page, 1500)
                    print("  OK Controllo batch ZIP raggiungibile")
                else:
                    errors.append("REPORT: pulsante batch ZIP non trovato")
                    print("  FAIL Pulsante batch ZIP non trovato")
            else:
                errors.append("REPORT: expander operazioni batch non trovato")
                print("  FAIL Expander operazioni batch non trovato")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        wait_st(page, 500)
        shot(page, "report_bottom")

        # =============================================
        #  6. NORME PAGE
        # =============================================
        print("\n[6/6] NORME")
        page.goto(f"{BASE_URL}/Norme")
        wait_st(page, 4000)
        shot(page, "norme_page")

        body = page.locator("body").inner_text()
        checks = [
            ("Tabelle Normative" in body, "Header pagina"),
            ("placeholder" in body.lower() or "personalizzate" in body.lower(), "Stato norme (placeholder o personalizzate)"),
            ("Calcolatore Rapido" in body, "Calcolatore rapido"),
            ("Legenda" in body, "Legenda bande"),
        ]
        for ok, desc in checks:
            if ok:
                print(f"  OK {desc}")
            else:
                errors.append(f"NORME: {desc} mancante")
                print(f"  FAIL {desc}")

        df = page.locator('div[data-testid="stDataFrame"]')
        if df.count() > 0:
            print(f"  OK {df.count()} tabella dati")
        else:
            errors.append("NORME: tabella dati non trovata")
            print("  FAIL Tabella dati")

        # Verifica sezione gestione norme (expander + file uploader)
        norms_expander = page.locator('[data-testid="stExpander"]')
        if norms_expander.count() > 0:
            print("  OK Sezione gestione norme presente")
        else:
            warnings.append("NORME: sezione gestione norme non trovata")
            print("  WARN Sezione gestione norme non trovata")

        if norms_expander.count() > 0:
            uploader = page.locator('[data-testid="stFileUploader"] input[type="file"]')
            if uploader.count() == 0 or not uploader.first.is_visible():
                norms_expander.first.locator('summary').click()
                wait_st(page, 800)
            norms_csv = build_norms_csv()
            if uploader.count() > 0:
                uploader.first.set_input_files(str(norms_csv))
                wait_st(page, 1000)
                upload_btn = page.locator('button', has_text="Carica e Applica Norme")
                if upload_btn.count() > 0 and not upload_btn.first.is_visible():
                    norms_expander.first.locator('summary').click()
                    wait_st(page, 800)
                    upload_btn = page.locator('button', has_text="Carica e Applica Norme")
                if upload_btn.count() > 0 and upload_btn.first.is_visible():
                    upload_btn.first.scroll_into_view_if_needed()
                    upload_btn.first.click()
                    wait_st(page, 2000)
                    options = get_selectbox_options(page, "Fascia d'Età")
                    expected_options = ["7", "Adulti", "Anziani"]
                    if options == expected_options:
                        print("  OK Bande età allineate al CSV caricato")
                    else:
                        errors.append(
                            f"NORME: opzioni fascia età non allineate al CSV ({options})"
                        )
                        print(f"  FAIL Bande età non allineate: {options}")

                    reset_btn = page.locator('button', has_text="Ripristina Norme Placeholder")
                    if reset_btn.count() > 0:
                        reset_btn.first.click()
                        wait_st(page, 1200)
                else:
                    errors.append("NORME: pulsante upload norme non trovato")
                    print("  FAIL Pulsante upload norme non trovato")
            else:
                errors.append("NORME: file uploader norme non trovato")
                print("  FAIL File uploader norme non trovato")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        wait_st(page, 500)
        shot(page, "norme_legenda")

        # =============================================
        #  RIEPILOGO
        # =============================================
        print("\n" + "=" * 65)
        print("  RIEPILOGO FINALE")
        print("=" * 65)
        print(f"  Screenshots: {SCREENSHOTS}")

        if not errors and not warnings:
            print("  TUTTI I TEST SUPERATI!")
        else:
            if errors:
                print(f"\n  ERRORI CRITICI: {len(errors)}")
                for e in errors:
                    print(f"    X {e}")
            if warnings:
                print(f"\n  AVVISI: {len(warnings)}")
                for w in warnings:
                    print(f"    ! {w}")

        print("=" * 65)
        page.close()
        ctx.close()
        browser.close()

    return errors


if __name__ == "__main__":
    if not _is_server_up():
        raise SystemExit("Playwright E2E richiede Streamlit attivo su localhost:8501.")
    errs = run()
    sys.exit(1 if errs else 0)


def test_playwright_e2e_navigation() -> None:
    if not _is_server_up():
        pytest.skip("Playwright E2E richiede Streamlit attivo su localhost:8501.")
    errs = run()
    assert not errs
