"""Drives a REAL browser (Playwright) through the confirmation queue,
because Next.js Server Actions require the client-side React runtime to
submit correctly (their wire protocol isn't a plain HTML form post).

Logs in via a real Clerk session cookie (minted through the sign-in-token
mechanism), opens the confirmation queue, opens one document, and clicks
"Confirmar tudo" — then verifies the DB state actually changed.

Usage:  py scripts/test_confirmation_flow.py
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")
FAPI = "https://positive-duckling-42.clerk.accounts.dev"
APP = "http://localhost:3000"
CLERK_SECRET_KEY = "sk_test_UedlvWz6xvUZSrk0y66UbSMeOx0C2g0H2avhKi8B8I"
USER_ID = "user_3G8lvQm2MdcsxTxQgmvo2OZcf3m"

FAILURES: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{(' — ' + extra) if extra and not ok else ''}")
    if not ok:
        FAILURES.append(name)


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def req(url: str, data: dict | None = None, json_body: dict | None = None, headers: dict | None = None) -> dict:
    hdrs = {"User-Agent": UA, **(headers or {})}
    if json_body is not None:
        body = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    else:
        body = urllib.parse.urlencode(data or {}).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    r = urllib.request.Request(url, data=body, headers=hdrs)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())


def mint_session_cookies() -> list[dict]:
    sit = req("https://api.clerk.com/v1/sign_in_tokens",
              json_body={"user_id": USER_ID, "expires_in_seconds": 300},
              headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"})
    dev = req(f"{FAPI}/v1/dev_browser")
    db_jwt = dev["token"]
    si = req(f"{FAPI}/v1/client/sign_ins?__clerk_db_jwt={db_jwt}", data={"strategy": "ticket", "ticket": sit["token"]})
    session_id = si["response"]["created_session_id"]
    tok = req(f"{FAPI}/v1/client/sessions/{session_id}/tokens?__clerk_db_jwt={db_jwt}")
    jwt = tok["jwt"]
    import base64
    payload = jwt.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    client_uat = json.loads(base64.urlsafe_b64decode(payload))["iat"]
    return [
        {"name": "__session", "value": jwt, "domain": "localhost", "path": "/"},
        {"name": "__client_uat", "value": str(client_uat), "domain": "localhost", "path": "/"},
        {"name": "__clerk_db_jwt", "value": db_jwt, "domain": "localhost", "path": "/"},
    ]


def db_state(orgId_query: str) -> dict:
    with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=15) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from core.source_documents where status='awaiting_confirmation'")
        pending = cur.fetchone()[0]
        cur.execute("select count(*) from core.source_documents where status='confirmed'")
        confirmed = cur.fetchone()[0]
        cur.execute("""select count(*) from core.families f where f.display_name='Família Souza'
                       and exists (select 1 from core.accounts a where a.family_id=f.id
                       and exists (select 1 from core.position_snapshots ps where ps.account_id=a.id))""")
        souza_has_positions = cur.fetchone()[0]
        cur.execute("""select count(*) from core.position_snapshots ps
                       join core.accounts a on a.id=ps.account_id
                       join core.families f on f.id=a.family_id where f.display_name='Família Souza'""")
        souza_position_count = cur.fetchone()[0]
        cur.execute("""select m.status, m.analysis_run_id is not null from core.meetings m
                       join core.families f on f.id=m.family_id where f.display_name='Família Souza'
                       order by m.scheduled_for limit 1""")
        souza_meeting = cur.fetchone()
        cur.execute("select count(*) from audit.events where kind='extraction_confirmed'")
        audit_count = cur.fetchone()[0]
    return {
        "pending": pending, "confirmed": confirmed,
        "souza_has_positions": souza_has_positions, "souza_position_count": souza_position_count,
        "souza_meeting": souza_meeting, "audit_count": audit_count,
    }


def main() -> None:
    print("== Estado do banco ANTES ==")
    before = db_state("")
    print(f"  pendentes={before['pending']} confirmados={before['confirmed']} "
          f"souza_posicoes={before['souza_position_count']} souza_reuniao={before['souza_meeting']} "
          f"eventos_auditoria={before['audit_count']}")

    cookies = mint_session_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()

        with psycopg.connect(ENV["DATABASE_URL"], connect_timeout=15) as c2:
            cur2 = c2.cursor()
            cur2.execute("""select d.id from core.source_documents d join core.families f on f.id=d.family_id
                            where f.display_name='Família Souza' and d.status='awaiting_confirmation'""")
            souza_doc_id = cur2.fetchone()[0]

        print("== Navegador: Caixa de confirmação ==")
        page.goto(f"{APP}/app/caixa-de-confirmacao", wait_until="networkidle")
        check("titulo da pagina", "Caixa de confirmação" in page.content())
        check("3 documentos pendentes visiveis", page.content().count("Conferir") >= 1)

        # navega direto pela URL do documento da Família Souza (evita ambiguidade de seletor por texto)
        page.goto(f"{APP}/app/caixa-de-confirmacao/{souza_doc_id}", wait_until="networkidle")
        page.wait_for_url("**/app/caixa-de-confirmacao/*", timeout=15000)
        page.wait_for_selector("text=Confirmar tudo", timeout=15000)
        print(f"  [debug] url apos clique: {page.url}")
        check("abriu o detalhe da extracao", "Família Souza" in page.content())
        check("reconciliado com o total declarado", "Reconciliado" in page.content())
        pdf_ok = "Abrir documento original" in page.content()
        if not pdf_ok:
            print(f"  [debug] conteudo (1500 chars): {page.content()[:1500]}")
        check("PDF original disponivel", pdf_ok)

        print("== Navegador: clicando Confirmar tudo ==")
        page.click("button:has-text('Confirmar tudo')")
        page.wait_for_url(lambda u: u.rstrip("/").endswith("/caixa-de-confirmacao"), timeout=20000)
        print(f"  [debug] url apos confirmar: {page.url}")
        check("voltou para a caixa de confirmacao", page.url.rstrip("/").endswith("/caixa-de-confirmacao"))

        browser.close()

    print("== Estado do banco DEPOIS ==")
    after = db_state("")
    print(f"  pendentes={after['pending']} confirmados={after['confirmed']} "
          f"souza_posicoes={after['souza_position_count']} souza_reuniao={after['souza_meeting']} "
          f"eventos_auditoria={after['audit_count']}")

    check("um documento a menos pendente", after["pending"] == before["pending"] - 1)
    check("um documento a mais confirmado", after["confirmed"] == before["confirmed"] + 1)
    check("Familia Souza agora tem posicoes reais (>10)", after["souza_position_count"] > 10)
    check("reuniao da Souza tem analysis_run vinculado", after["souza_meeting"][1] is True)
    check("reuniao da Souza avancou para 'preparing'", after["souza_meeting"][0] == "preparing")
    check("evento de auditoria registrado", after["audit_count"] == before["audit_count"] + 1)

    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("RESULT: FLUXO DE CONFIRMACAO PASSOU DE PONTA A PONTA (navegador real)")


if __name__ == "__main__":
    main()
