"""Captures real screenshots of the app using a real headless browser
(Playwright): the public marketing landing (no auth), then the
authenticated product injecting the same Clerk session cookies our e2e
verification proved valid. Saves PNGs for visual review.

Usage:  py scripts/capture_screenshots.py
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

        # marketing landing — public, unauthenticated context
        marketing_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        mpage = marketing_ctx.new_page()
        mpage.goto("http://localhost:3000/", wait_until="networkidle", timeout=20000)
        mpage.wait_for_timeout(500)
        mpage.screenshot(path=str(OUT / "00_marketing_landing.png"), full_page=True)
        print("captured: 00_marketing_landing.png ·", mpage.url)
        marketing_ctx.close()

        # authenticated product
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_cookies(cookies)
        page = context.new_page()

        page.goto("http://localhost:3000/app", wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "01_mesa_de_reunioes.png"), full_page=True)
        print("captured: 01_mesa_de_reunioes.png ·", page.url)

        link = page.locator("a[href^='/app/reunioes/']").first
        href = link.get_attribute("href")
        page.goto(f"http://localhost:3000{href}", wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "02_workspace_briefing.png"), full_page=True)
        print("captured: 02_workspace_briefing.png ·", page.url)

        page.get_by_text("Carteira", exact=True).click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "03_workspace_carteira.png"), full_page=True)
        print("captured: 03_workspace_carteira.png")

        page.get_by_text("Pontos de atenção", exact=False).click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "04_workspace_atencao.png"), full_page=True)
        print("captured: 04_workspace_atencao.png")

        page.locator("button.tnum").first.click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "05_gaveta_provenencia.png"), full_page=True)
        print("captured: 05_gaveta_provenencia.png")

        page.goto("http://localhost:3000/app/radar", wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "06_radar_consenso.png"), full_page=True)
        print("captured: 06_radar_consenso.png")

        browser.close()
    print(f"\n== screenshots salvas em {OUT} ==")


if __name__ == "__main__":
    main()
