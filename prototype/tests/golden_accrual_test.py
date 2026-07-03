"""Golden tests for ENGINE_METHODOLOGY v1.1 (§2, §3, §5) — accrual layer.

Expected values are hand-derived with explicit Decimal literals in the test
(independent of the engine). Run:  py tests/golden_accrual_test.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from engine import accrual, insights, metrics  # noqa: E402
from engine.calendar_br import business_days_between, easter, holidays  # noqa: E402
from engine.models import Position  # noqa: E402

Q6 = Decimal("0.000001")
Q2 = Decimal("0.01")
FAILURES: list[str] = []


def check(name: str, got, expected) -> None:
    if got == expected:
        print(f"  PASS  {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}: got={got} expected={expected}")


def main() -> None:
    print("== Golden: calendar (ANBIMA) ==")
    # Easter 2026 = April 5 (known). Carnaval Feb 16/17, Good Friday Apr 3, Corpus Jun 4.
    check("easter 2026", easter(2026), date(2026, 4, 5))
    hs = holidays(2026)
    check("carnaval monday", date(2026, 2, 16) in hs, True)
    check("carnaval tuesday", date(2026, 2, 17) in hs, True)
    check("good friday", date(2026, 4, 3) in hs, True)
    check("corpus christi", date(2026, 6, 4) in hs, True)
    check("consciencia negra (nacional desde 2024)", date(2026, 11, 20) in hs, True)
    # June/2026 by hand: 22 weekdays - Corpus Christi (Jun 4) = 21 DU
    check("DU June 2026 (hand-counted 21)",
          business_days_between(date(2026, 5, 31), date(2026, 6, 30)), 21)
    # Jan15->Mar16 2026 by hand: 11 (Jan) + 18 (Feb, -2 Carnaval) + 11 (Mar) = 40
    check("DU 15/01->16/03 2026 (hand-counted 40)",
          business_days_between(date(2026, 1, 15), date(2026, 3, 16)), 40)

    print("== Golden: %CDI accrual (§3.1) ==")
    synthetic = [(date(2026, 6, 1), Decimal("0.053400")),
                 (date(2026, 6, 2), Decimal("0.053400")),
                 (date(2026, 6, 3), Decimal("0.053400"))]
    # hand: daily factor = 1 + 0.000534*1.10 = 1.0005874 ; three explicit multiplications
    f = Decimal("1.0005874")
    expected = (Decimal("100000") * f * f * f).quantize(Q2)
    got = accrual.cdi_percent_accrual(
        Decimal("100000"), Decimal("110"), synthetic, date(2026, 5, 31), date(2026, 6, 3)
    ).quantize(Q2)
    check("CDB 110% CDI, 3 days", got, expected)

    print("== Golden: prefixado DU/252 (§3.2) ==")
    # hand: du = 21 (June above); V = 50000 * 1.135^(21/252)
    expected = (Decimal("50000") * Decimal("1.135") ** (Decimal(21) / Decimal(252))).quantize(Q6)
    got = accrual.prefixado_du252(
        Decimal("50000"), Decimal("13.5"), date(2026, 5, 31), date(2026, 6, 30)
    ).quantize(Q6)
    check("CDB pre 13,50%, June 2026", got, expected)

    print("== Golden: VNA exato (§3.3) ==")
    ipca = [(date(2026, 1, 1), Decimal("0.33")), (date(2026, 2, 1), Decimal("0.70")),
            (date(2026, 3, 1), Decimal("0.88"))]
    # Hand derivation: start 15/01/2026, ref 16/03/2026 (adjusted anniversary; 15/03 is Sunday).
    # Anniversary 1: 15/02 (Sun) -> 18/02 (16-17 = Carnaval) -> applies IPCA Jan = 0.33
    # Anniversary 2: 15/03 (Sun) -> 16/03            -> applies IPCA Feb = 0.70
    # No stub (ref == last adjusted anniversary). du(15/01->16/03) = 40 (hand-counted above).
    expected = (
        Decimal("100000")
        * Decimal("1.0033") * Decimal("1.0070")
        * Decimal("1.062") ** (Decimal(40) / Decimal(252))
    ).quantize(Q6)
    res = accrual.ipca_vna(
        Decimal("100000"), Decimal("6.20"), date(2026, 1, 15), date(2026, 3, 16), ipca
    )
    check("VNA on-anniversary value", res.value.quantize(Q6), expected)
    check("VNA no stub on anniversary", res.stub_factor, Decimal("1"))
    check("VNA no fallback flag on anniversary", res.stub_used_fallback, False)

    # Open period: ref 10/04/2026 -> stub from 16/03, projection fallback = IPCA Mar (0.88)
    res2 = accrual.ipca_vna(
        Decimal("100000"), Decimal("6.20"), date(2026, 1, 15), date(2026, 4, 10), ipca
    )
    check("VNA stub fallback flagged (provenance)", res2.stub_used_fallback, True)
    check("VNA stub grows the value", res2.value > res.value, True)

    print("== Golden: benchmark comparison rule (§5) ==")
    pos_case = metrics.benchmark_comparison(Decimal("5.2017"), Decimal("6.8434"))
    check("positive case -> pct_of_benchmark", pos_case["mode"], "pct_of_benchmark")
    check("positive case value", pos_case["value"], Decimal("76.01"))
    neg_case = metrics.benchmark_comparison(Decimal("-1.50"), Decimal("5.00"))
    check("negative case -> pp_difference", neg_case["mode"], "pp_difference")
    check("negative case value", neg_case["value"], Decimal("-6.50"))

    print("== Golden: parameterizable thresholds (§6) ==")
    raw = json.loads((BASE / "data" / "portfolio_familia_almeida.json").read_text(encoding="utf-8"))
    positions = [Position.from_dict(d) for d in raw["positions"]]
    relaxed = insights.InsightConfig(issuer_concentration_limit_pct=Decimal("25"))
    codes_default = [i["code"] for i in insights.generate(positions, date(2026, 6, 30))]
    codes_relaxed = [i["code"] for i in insights.generate(positions, date(2026, 6, 30), relaxed)]
    check("default config flags concentration", "CONCENTRACAO_EMISSOR" in codes_default, True)
    check("relaxed 25% limit removes the flag", "CONCENTRACAO_EMISSOR" in codes_relaxed, False)

    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("RESULT: ALL ACCRUAL GOLDEN TESTS PASSED")


if __name__ == "__main__":
    main()
