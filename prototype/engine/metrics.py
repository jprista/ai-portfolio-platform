"""Deterministic portfolio metrics — the single source of numeric truth (I1).

All returns use chained Modified Dietz over valuation periods, an accepted
TWR approximation when intra-period pricing is unavailable. The methodology
is declared in the report (PRODUCT_VISION.md: declared confidence).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, getcontext
from typing import Iterable

from .models import Flow, Position, Valuation

getcontext().prec = 28

HUNDRED = Decimal("100")
PCT_Q = Decimal("0.0001")  # percentages carried at 4 decimal places
MONEY_Q = Decimal("0.01")


def q_pct(x: Decimal) -> Decimal:
    return x.quantize(PCT_Q)


def total_value(positions: Iterable[Position]) -> Decimal:
    return sum((p.value for p in positions), Decimal("0")).quantize(MONEY_Q)


def allocation_by_class(positions: list[Position]) -> dict[str, dict[str, Decimal]]:
    total = total_value(positions)
    out: dict[str, dict[str, Decimal]] = {}
    for p in positions:
        entry = out.setdefault(p.asset_class, {"value": Decimal("0")})
        entry["value"] += p.value
    for entry in out.values():
        entry["value"] = entry["value"].quantize(MONEY_Q)
        entry["pct"] = q_pct(entry["value"] / total * HUNDRED)
    return out


def concentration_by_issuer(positions: list[Position]) -> dict[str, dict[str, Decimal]]:
    total = total_value(positions)
    out: dict[str, dict[str, Decimal]] = {}
    for p in positions:
        entry = out.setdefault(p.issuer, {"value": Decimal("0")})
        entry["value"] += p.value
    for entry in out.values():
        entry["value"] = entry["value"].quantize(MONEY_Q)
        entry["pct"] = q_pct(entry["value"] / total * HUNDRED)
    return dict(sorted(out.items(), key=lambda kv: kv[1]["value"], reverse=True))


_LIQ_BUCKETS = ("D0", "até 30 dias", "31–360 dias", "acima de 360 dias")


def _bucket_for(p: Position, ref: date) -> str:
    if p.liquidity == "vencimento":
        days = (p.maturity - ref).days if p.maturity else 99999
        if days <= 0:
            return "D0"
        if days <= 30:
            return "até 30 dias"
        if days <= 360:
            return "31–360 dias"
        return "acima de 360 dias"
    return {"D0": "D0", "D+2": "até 30 dias", "D+30": "até 30 dias", "D+60": "31–360 dias"}.get(
        p.liquidity, "31–360 dias"
    )


def liquidity_ladder(positions: list[Position], ref: date) -> dict[str, dict[str, Decimal]]:
    total = total_value(positions)
    out = {b: {"value": Decimal("0")} for b in _LIQ_BUCKETS}
    for p in positions:
        out[_bucket_for(p, ref)]["value"] += p.value
    for entry in out.values():
        entry["value"] = entry["value"].quantize(MONEY_Q)
        entry["pct"] = q_pct(entry["value"] / total * HUNDRED)
    return out


def upcoming_maturities(positions: list[Position], ref: date, within_days: int = 90) -> list[dict]:
    found = []
    for p in positions:
        if p.maturity is not None:
            days = (p.maturity - ref).days
            if 0 <= days <= within_days:
                found.append({"position": p, "days": days})
    return sorted(found, key=lambda item: item["days"])


def modified_dietz(v0: Decimal, v1: Decimal, flows: list[Flow], start: date, end: date) -> Decimal:
    """Modified Dietz return for one period. Flows are day-weighted."""
    period_days = (end - start).days
    net_flow = sum((f.amount for f in flows), Decimal("0"))
    weighted = Decimal("0")
    for f in flows:
        w = Decimal((end - f.day).days) / Decimal(period_days)
        weighted += f.amount * w
    denominator = v0 + weighted
    return (v1 - v0 - net_flow) / denominator


def chained_returns(valuations: list[Valuation], flows: list[Flow]) -> dict:
    """Chain Modified Dietz sub-period returns across consecutive valuations."""
    vals = sorted(valuations, key=lambda v: v.day)
    periods = []
    factor = Decimal("1")
    for prev, cur in zip(vals, vals[1:]):
        in_period = [f for f in flows if prev.day < f.day <= cur.day]
        r = modified_dietz(prev.total, cur.total, in_period, prev.day, cur.day)
        periods.append({"start": prev.day, "end": cur.day, "return_pct": q_pct(r * HUNDRED)})
        factor *= Decimal("1") + r
    return {"periods": periods, "total_return_pct": q_pct((factor - 1) * HUNDRED)}


def benchmark_comparison(portfolio_pct: Decimal, benchmark_pct: Decimal) -> dict:
    """ENGINE_METHODOLOGY §5: '% of benchmark' only when meaningful
    (portfolio >= 0 and benchmark > 0); otherwise difference in p.p.,
    explained in the report (founder decision 2026-07-03)."""
    if portfolio_pct >= 0 and benchmark_pct > 0:
        return {
            "mode": "pct_of_benchmark",
            "value": (portfolio_pct / benchmark_pct * HUNDRED).quantize(Decimal("0.01")),
        }
    return {
        "mode": "pp_difference",
        "value": (portfolio_pct - benchmark_pct).quantize(Decimal("0.01")),
    }


def accumulate_bcb_series(series: list[dict], start: date, end: date) -> Decimal:
    """Accumulate a BCB/SGS daily percentage series (e.g. CDI) into a period return (%).

    Series items look like {"data": "dd/mm/yyyy", "valor": "0.053400"}.
    """
    factor = Decimal("1")
    for item in series:
        day = datetime.strptime(item["data"], "%d/%m/%Y").date()
        if start <= day <= end:
            factor *= Decimal("1") + Decimal(item["valor"]) / HUNDRED
    return q_pct((factor - 1) * HUNDRED)
