"""Smoke test of the engine service API — golden values end-to-end.

Runs the FastAPI app in-process (TestClient); asserts the known Família
Almeida golden numbers come back through the HTTP contract.
Run:  py services/engine/tests/smoke_api.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

DATA = BASE / "tests" / "data"
FAILURES: list[str] = []


def check(name: str, got, expected) -> None:
    if got == expected:
        print(f"  PASS  {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}: got={got!r} expected={expected!r}")


def main() -> None:
    client = TestClient(app)

    print("== Smoke: /engine/health ==")
    r = client.get("/engine/health")
    check("health 200", r.status_code, 200)
    check("engine version", r.json()["engine_version"], "0.2.0-prototype")

    print("== Smoke: /engine/analyze (golden Família Almeida) ==")
    portfolio = json.loads((DATA / "portfolio_familia_almeida.json").read_text(encoding="utf-8"))
    cdi = json.loads((DATA / "cdi_daily_2026S1.json").read_text(encoding="utf-8"))
    r = client.post("/engine/analyze", json={
        "reference_date": "2026-06-30",
        "positions": portfolio["positions"],
        "history": portfolio["history"],
        "market": {"cdi": cdi},
        "benchmark": {"kind": "cdi", "name": "CDI"},
    })
    check("analyze 200", r.status_code, 200)
    run = r.json()
    out = run["outputs"]
    check("total_value", out["total_value"], "2913933.80")
    check("semester return", out["returns"]["total_return_pct"], "5.2017")
    check("benchmark pct", out["benchmark_pct"], "6.8434")
    check("benchmark mode", out["benchmark_comparison"]["mode"], "pct_of_benchmark")
    check("pct of CDI", out["benchmark_comparison"]["value"], "76.01")
    check("6 insights", len(out["insights"]), 6)
    check("run id present", len(run["run_id"]) == 16, True)
    check("no limitations on golden portfolio", out["declared_limitations"], [])

    print("== Smoke: /engine/analyze com política relaxada ==")
    r = client.post("/engine/analyze", json={
        "reference_date": "2026-06-30",
        "positions": portfolio["positions"],
        "policy": {"issuer_concentration_limit_pct": "25", "fgc_limit": "600000"},
    })
    codes = [i["code"] for i in r.json()["outputs"]["insights"]]
    check("política 25%/600k remove concentração e FGC",
          "CONCENTRACAO_EMISSOR" not in codes and "FGC_TITULAR" not in codes, True)

    print("== Smoke: /engine/valuate (VNA exato) ==")
    ipca = json.loads((DATA / "ipca_monthly_2026S1.json").read_text(encoding="utf-8"))
    r = client.post("/engine/valuate", json={
        "kind": "ipca_vna", "principal": "100000", "rate_aa": "6.20",
        "start": "2026-01-15", "reference_date": "2026-03-16",
        "anniversary_day": 15, "market": {"ipca": ipca},
    })
    check("valuate 200", r.status_code, 200)
    check("VNA sem fallback no aniversário", r.json()["stub_used_fallback"], False)

    r = client.post("/engine/valuate", json={
        "kind": "coe_exotico", "principal": "1", "start": "2026-01-01", "reference_date": "2026-06-30",
    })
    check("kind não suportado -> 422 com limitação declarada", r.status_code, 422)

    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("RESULT: SMOKE API PASSED")


if __name__ == "__main__":
    main()
