"""Verifies the Familia -> Cliente rename end-to-end: sidebar label, /app/clientes
route, "Adicionar cliente" button, no leftover "familia" wording, and that
Familia Castro (deactivated, no analysis run) no longer shows up. Also
re-checks the Analise tab still renders after the family_id-driven queries
were touched. Saves screenshots for visual review.

Usage:  py scripts/verify_clientes_rename.py
"""
from __future__ import annotations

import re
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

        page.goto("http://localhost:3000/app/clientes", wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(300)
        body = page.content()
        print("h1:", page.locator("h1").first.text_content())
        print("sidebar 'Clientes' visível:", page.get_by_role("link", name="Clientes", exact=True).count() > 0)
        print("botão 'Adicionar cliente' visível:", page.get_by_role("button", name="Adicionar cliente").count() > 0)
        print("nomes de clientes:", [page.locator(".font-display.text-\\[17px\\].text-navy").nth(i).text_content() for i in range(page.locator(".font-display.text-\\[17px\\].text-navy").count())])
        print("'Castro' na lista:", "Castro" in body)
        leftover = re.findall(r"[Ff]am[íi]lia", body)
        print("sobras 'família' no HTML:", leftover)
        page.screenshot(path=str(OUT / "clientes_lista.png"), full_page=True)

        page.goto("http://localhost:3000/app", wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "mesa_de_reunioes.png"), full_page=True)
        first_meeting_link = page.locator("a[href^='/app/reunioes/']").first
        href = first_meeting_link.get_attribute("href")
        page.goto(f"http://localhost:3000{href}", wait_until="networkidle", timeout=20000)
        print("\nworkspace h1:", page.locator("h1").first.text_content())
        page.get_by_role("button", name="Análise", exact=True).click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "analise_pos_rename.png"), full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
