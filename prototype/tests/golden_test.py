"""Golden tests — hand-derived expected values vs. the engine.

The expected figures below are computed IN THE TEST with explicit literal
arithmetic (independent derivation), never by calling engine helpers.
This file is the seed of the golden-test constitution
(ENGINEERING_PRINCIPLES.md §2). Run:  py tests/golden_test.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from engine import insights, metrics  # noqa: E402
from engine.models import Flow, Position, Valuation  # noqa: E402

PCT_Q = Decimal("0.0001")
FAILURES: list[str] = []


def check(name: str, got, expected) -> None:
    if got == expected:
        print(f"  PASS  {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}: got={got} expected={expected}")


def main() -> None:
    raw = json.loads((BASE / "data" / "portfolio_familia_almeida.json").read_text(encoding="utf-8"))
    positions = [Position.from_dict(d) for d in raw["positions"]]
    valuations = [Valuation.from_dict(d) for d in raw["history"]["valuations"]]
    flows = [Flow.from_dict(d) for d in raw["history"]["flows"]]
    ref = date(2026, 6, 30)

    print("== Golden: totals and allocation ==")
    # Hand sum of the 12 position values in the JSON:
    check("total_value", metrics.total_value(positions), Decimal("2913933.80"))

    alloc = metrics.allocation_by_class(positions)
    check("allocation value sum equals total",
          sum(a["value"] for a in alloc.values()), Decimal("2913933.80"))
    pct_sum = sum(a["pct"] for a in alloc.values())
    check("allocation pct sums to ~100 (±0.01)",
          abs(pct_sum - Decimal("100")) <= Decimal("0.01"), True)
    # renda_fixa_pos = 412350.75 + 121480.30 + 305880.65 = 839711.70
    check("renda_fixa_pos value", alloc["renda_fixa_pos"]["value"], Decimal("839711.70"))
    expected_rf_pos_pct = (Decimal("839711.70") / Decimal("2913933.80") * 100).quantize(PCT_Q)
    check("renda_fixa_pos pct", alloc["renda_fixa_pos"]["pct"], expected_rf_pos_pct)

    print("== Golden: issuer concentration ==")
    conc = metrics.concentration_by_issuer(positions)
    # Banco Beta = 150000.00 + 412350.75 = 562350.75
    check("Banco Beta value", conc["Banco Beta"]["value"], Decimal("562350.75"))
    expected_beta_pct = (Decimal("562350.75") / Decimal("2913933.80") * 100).quantize(PCT_Q)
    check("Banco Beta pct", conc["Banco Beta"]["pct"], expected_beta_pct)
    check("Banco Beta above 15% threshold", conc["Banco Beta"]["pct"] > Decimal("15"), True)

    print("== Golden: Modified Dietz (March, with mid-month inflow) ==")
    # Period 2026-02-28 -> 2026-03-31 (31 days), flow +50,000 on 2026-03-15.
    # weight = (31-15 days remaining)/31 = 16/31
    # denom  = 2,805,200 + 50,000*16/31 ; numer = 2,883,450 - 2,805,200 - 50,000 = 28,250
    expected_march = (
        Decimal("28250")
        / (Decimal("2805200") + Decimal("50000") * Decimal(16) / Decimal(31))
        * 100
    ).quantize(PCT_Q)
    march_flow = [f for f in flows if f.day == date(2026, 3, 15)]
    got_march = (
        metrics.modified_dietz(
            Decimal("2805200.00"), Decimal("2883450.00"),
            march_flow, date(2026, 2, 28), date(2026, 3, 31),
        ) * 100
    ).quantize(PCT_Q)
    check("March Modified Dietz", got_march, expected_march)

    print("== Golden: chained semester return ==")
    # Independent derivation: six monthly Dietz factors from literals.
    def dietz(v0, v1, flow, w_num, w_den):
        f = Decimal(flow)
        denom = Decimal(v0) + f * Decimal(w_num) / Decimal(w_den)
        return (Decimal(v1) - Decimal(v0) - f) / denom

    months = [
        dietz("2750000", "2778100.00", "0", 0, 1),
        dietz("2778100", "2805200.00", "0", 0, 1),
        dietz("2805200", "2883450.00", "50000", 16, 31),   # flow 15/03, 16 of 31 days remaining
        dietz("2883450", "2896920.00", "0", 0, 1),
        dietz("2896920", "2884350.00", "-30000", 21, 31),  # flow 10/05, 21 of 31 days remaining
        dietz("2884350", "2913933.80", "0", 0, 1),
    ]
    factor = Decimal("1")
    for r in months:
        factor *= Decimal("1") + r
    expected_total = ((factor - 1) * 100).quantize(PCT_Q)
    got = metrics.chained_returns(valuations, flows)
    # Engine chains QUANTIZED period returns; rebuild the same way for comparison:
    engine_factor = Decimal("1")
    for p in got["periods"]:
        engine_factor *= Decimal("1") + p["return_pct"] / 100
    engine_total_rebuilt = ((engine_factor - 1) * 100).quantize(PCT_Q)
    check("engine total consistent with its own periods", got["total_return_pct"].quantize(Decimal("0.01")), engine_total_rebuilt.quantize(Decimal("0.01")))
    check("semester TWR (±0.0002 p.p. vs. independent derivation)",
          abs(got["total_return_pct"] - expected_total) <= Decimal("0.0002"), True)

    print("== Golden: index accumulation ==")
    synthetic = [
        {"data": "01/06/2026", "valor": "0.05"},
        {"data": "02/06/2026", "valor": "0.05"},
        {"data": "03/06/2026", "valor": "0.05"},
    ]
    expected_acc = (
        (Decimal("1.0005") * Decimal("1.0005") * Decimal("1.0005") - 1) * 100
    ).quantize(PCT_Q)
    check("3-day accumulation", metrics.accumulate_bcb_series(synthetic, date(2026, 6, 1), date(2026, 6, 3)), expected_acc)

    print("== Golden: liquidity and maturities ==")
    ladder = metrics.liquidity_ladder(positions, ref)
    check("ladder pct sums to ~100 (±0.01)",
          abs(sum(b["pct"] for b in ladder.values()) - Decimal("100")) <= Decimal("0.01"), True)
    check("ladder value sum equals total",
          sum(b["value"] for b in ladder.values()), Decimal("2913933.80"))
    mats = metrics.upcoming_maturities(positions, ref, 90)
    check("one maturity inside 90 days", len(mats), 1)
    check("LCA Banco Gama in 46 days", (mats[0]["position"].issuer, mats[0]["days"]), ("Banco Gama", 46))

    print("== Golden: deterministic insights ==")
    # DOMAIN_MODEL §9.1: FGC per holder (José/Banco Beta 562.350,75; Maria/Banco
    # Delta 262.110,45 — both above 250k) + aggregate family concentration alert.
    att = insights.generate(positions, ref)
    codes = sorted(i["code"] for i in att)
    check("expected insight codes",
          codes, ["CONCENTRACAO_EMISSOR", "CONFIANCA_DADO", "CUSTO_ACIMA_MEDIANA",
                  "FGC_TITULAR", "FGC_TITULAR", "VENCIMENTO_PROXIMO"])

    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("RESULT: ALL GOLDEN TESTS PASSED")


if __name__ == "__main__":
    main()
