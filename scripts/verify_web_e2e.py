"""End-to-end verification of the authenticated web app WITHOUT a browser:
uses the Clerk Backend API to mint a sign-in token (the official mechanism
for automated/test sign-ins), exchanges it for a real session JWT via the
Frontend API, then authenticates to the app using the same three cookies
a real browser would hold (__session, __client_uat, __clerk_db_jwt), and
requests the app pages asserting the REAL database/engine values render.

Usage:  py scripts/verify_web_e2e.py
"""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

FAPI = "https://positive-duckling-42.clerk.accounts.dev"
APP = "http://localhost:3000"
CLERK_SECRET_KEY = "sk_test_UedlvWz6xvUZSrk0y66UbSMeOx0C2g0H2avhKi8B8I"
USER_ID = "user_3G8lvQm2MdcsxTxQgmvo2OZcf3m"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

FAILURES: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{(' — ' + extra) if extra and not ok else ''}")
    if not ok:
        FAILURES.append(name)


def req(url: str, data: dict | None = None, headers: dict | None = None, json_body: dict | None = None) -> tuple[int, dict | str]:
    hdrs = dict(headers or {})
    hdrs.setdefault("User-Agent", UA)
    hdrs.setdefault("Accept", "application/json, text/html;q=0.9,*/*;q=0.8")
    if json_body is not None:
        body = json.dumps(json_body).encode()
        hdrs.setdefault("Content-Type", "application/json")
    elif data is not None:
        body = urllib.parse.urlencode(data).encode()
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    else:
        body = None
    r = urllib.request.Request(url, data=body, headers=hdrs)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def jwt_claims(jwt: str) -> dict:
    payload_b64 = jwt.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def get_session_cookie_header() -> str:
    """Full real Clerk sign-in, exactly as a browser would end up authenticated:
    1) Backend API mints a sign-in token for our seeded user (official test mechanism)
    2) Frontend API dev_browser + ticket exchange yields a session JWT
    3) The three cookies a real browser holds after sign-in: __session,
       __client_uat (must equal the session token's iat — Clerk's freshness
       check), __clerk_db_jwt (dev-mode browser registration)
    Requires the user to have >=1 Clerk Organization, else the session
    carries a pending 'choose-organization' task and never activates.
    """
    status, sit = req(
        "https://api.clerk.com/v1/sign_in_tokens",
        json_body={"user_id": USER_ID, "expires_in_seconds": 300},
        headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
    )
    ticket = sit["token"]
    status, dev = req(f"{FAPI}/v1/dev_browser", data={})
    db_jwt = dev["token"]
    status, si = req(
        f"{FAPI}/v1/client/sign_ins?__clerk_db_jwt={db_jwt}",
        data={"strategy": "ticket", "ticket": ticket},
    )
    session_id = si["response"]["created_session_id"]
    status, tok = req(f"{FAPI}/v1/client/sessions/{session_id}/tokens?__clerk_db_jwt={db_jwt}", data={})
    jwt = tok["jwt"]
    client_uat = jwt_claims(jwt)["iat"]
    return f"__session={jwt}; __client_uat={client_uat}; __clerk_db_jwt={db_jwt}"


def main() -> None:
    print("== Clerk: autenticação real (sign-in token oficial -> sessão -> cookies) ==")
    cookie = get_session_cookie_header()
    check("cookies de sessão obtidos", bool(cookie))
    auth = {"Cookie": cookie, "Accept": "text/html", "User-Agent": UA}

    print("== App: Mesa de Reuniões (dados reais do banco de São Paulo) ==")
    status, html = req(f"{APP}/", headers=auth)
    check("HTTP 200 autenticado (não redirecionado para sign-in)", status == 200, f"status={status}")
    html = str(html)
    for needle, label in [
        ("Mesa de Reuni", "título"),
        ("Fam", "família do banco"),  # accent-safe
        ("2.913.933,80", "patrimônio real (motor)"),
        ("Em prepara", "estado da reunião"),
        ("pontos de aten", "insights do run"),
        ("FGC", "alerta de risco (FGC por titular)"),
    ]:
        check(f"contém: {label}", needle in html)

    import re
    m = re.search(r"/reunioes/([0-9a-f-]{36})", html)
    check("link real para o workspace (não '#')", bool(m), "nenhum UUID de reunião encontrado no href")

    if m:
        print("== App: Workspace da reunião (carteira completa + proveniência) ==")
        status, html2 = req(f"{APP}/reunioes/{m.group(1)}", headers=auth)
        html2 = str(html2)
        check("HTTP 200", status == 200, f"status={status}")
        for needle, label in [
            ("Revis", "título"),
            ("5,20%", "retorno do semestre (motor)"),
            ("6,84%", "CDI real (BCB)"),
            ("76,01%", "% do CDI"),
            ("Acima do FGC", "insight por titular"),
            ("pol", "proveniência da política"),
            ("v1", "versão da política"),
            ("Pauta sugerida", "pauta"),
            ("Renda fixa p", "carteira: classe de ativo"),
            ("Banco Beta", "carteira: emissor real"),
        ]:
            check(f"contém: {label}", needle in html2)

    print("== App: Radar de Consenso (SEC 13F real, dados públicos ao vivo) ==")
    status, html3 = req(f"{APP}/radar", headers=auth)
    html3 = str(html3)
    check("HTTP 200", status == 200, f"status={status}")
    for needle, label in [
        ("Radar de Consenso", "título"),
        ("Berkshire", "Berkshire Hathaway"),
        ("Apple", "top holding real"),
        ("Pershing", "Pershing Square"),
        ("defasagem", "limitação declarada"),
        ("sec.gov", "link para a fonte"),
    ]:
        check(f"contém: {label}", needle in html3)

    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("RESULT: E2E AUTENTICADO PASSOU — app real, login real, banco real, motor real, radar real")


if __name__ == "__main__":
    main()
