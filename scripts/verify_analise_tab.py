"""Verifies the new aba Analise end-to-end with a real headless browser:
navigates to each family's meeting workspace, opens the Analise tab, checks
that the expected sections rendered without console errors, and saves
screenshots for visual review.

Usage:  py scripts/verify_analise_tab.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_web_e2e import get_session_cookie_header  # noqa: E402

OUT = Path(r"C:\dev\screenshots")
OUT.mkdir(exist_ok=True)


def main() -> None:
    cookie_header = get_session_cookie_header()
    cookies = [
        {"name": part.split("=", 1)[0], "value": part.split("=", 1)[1], "domain": "localhost", "path": "/"}
        for part in cookie_header.split("; ")
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1400})
        context.add_cookies(cookies)
        page = context.new_page()
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto("http://localhost:3000/app/familias", wait_until="networkidle", timeout=20000)
        links = page.locator("a[href^='/app/reunioes/']")
        n = links.count()
        print(f"famílias com link direto para reunião: {n}")

        hrefs = [links.nth(i).get_attribute("href") for i in range(n)]

        for i, href in enumerate(hrefs):
            page.goto(f"http://localhost:3000{href}", wait_until="networkidle", timeout=20000)
            if page.locator("h1").first.text_content() == "404":
                print(f"\n=== {href}: sem analysis_run, pulado (404 esperado) ===")
                continue
            page.get_by_role("button", name="Análise", exact=True).click()
            page.wait_for_timeout(500)
            title = page.locator("h1").first.text_content()
            print(f"\n=== {title} ({href}) ===")
            for section in [
                "Leitura do gestor de patrimônio",
                "Exposição a juros e inflação",
                "Sensibilidade a cenários",
                "Cruzamento com o Radar de Consenso",
                "Recomendações para a pauta",
            ]:
                found = page.get_by_text(section, exact=True).count() > 0
                print(f"  [{'ok' if found else 'FALTOU'}] {section}")
            page.screenshot(path=str(OUT / f"analise_{i:02d}.png"), full_page=True)

        if errors:
            print("\nERROS DE CONSOLE:")
            for e in errors:
                print(" -", e)
        else:
            print("\nnenhum erro de console em nenhuma navegação")

        browser.close()


if __name__ == "__main__":
    main()
