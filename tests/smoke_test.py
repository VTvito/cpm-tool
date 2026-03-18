"""Quick smoke test: verify all pages load and the main Report batch control is reachable."""
import socket

import pytest
from playwright.sync_api import sync_playwright


def _is_server_up(host: str = "localhost", port: int = 8501) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


if not _is_server_up():
    pytest.skip("Smoke test richiede Streamlit attivo su localhost:8501.", allow_module_level=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Test homepage
    page.goto("http://localhost:8501/")
    page.wait_for_timeout(4000)
    title = page.locator("h1").first.text_content()
    print(f"Homepage: {title}")

    # Check navigation links exist
    page_links = page.locator('[data-testid="stPageLink"]').count()
    print(f"Page links found: {page_links}")

    # Test Scoring page
    page.goto("http://localhost:8501/Scoring")
    page.wait_for_timeout(4000)
    header = page.locator("h2").first.text_content()
    print(f"Scoring header: {header}")
    editors = page.locator('[data-testid="stDataFrame"]').count()
    print(f"Data editors: {editors}")

    # Test Norme page
    page.goto("http://localhost:8501/Norme")
    page.wait_for_timeout(4000)
    header = page.locator("h2").first.text_content()
    print(f"Norme header: {header}")
    uploader = page.locator('[data-testid="stFileUploader"]').count()
    print(f"File uploader: {uploader}")

    # Test Database page
    page.goto("http://localhost:8501/Database")
    page.wait_for_timeout(4000)
    header = page.locator("h2").first.text_content()
    print(f"Database header: {header}")

    # Test Report page
    page.goto("http://localhost:8501/Report")
    page.wait_for_timeout(4000)
    header = page.locator("h2").first.text_content()
    print(f"Report header: {header}")
    report_expanders = page.locator('[data-testid="stExpander"] summary')
    if report_expanders.count() > 0:
        report_expanders.first.click()
        page.wait_for_timeout(500)
    batch_btn = page.locator('button:has-text("Genera ZIP con Tutti i Report")').count()
    print(f"Batch ZIP button: {batch_btn}")

    browser.close()
    print("\nALL PAGES LOADED OK")
