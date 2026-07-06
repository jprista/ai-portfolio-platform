"""Extensible benchmark abstraction — DOMAIN_MODEL §4 (founder decision 9.4).

v1 USES only CDI as default, but the structure accommodates ipca_plus, index,
custom_portfolio and composite without structural refactoring (extensibility
directive, DOMAIN_MODEL §1.6). Unsupported kinds fail with a declared
limitation, never silently.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from . import metrics
from .calendar_br import business_days_between

HUNDRED = Decimal("100")
ONE = Decimal("1")
D252 = Decimal("252")


@dataclass(frozen=True)
class BenchmarkDef:
    kind: str                      # cdi | ipca_plus | index | custom_portfolio | composite
    name: str = ""
    real_rate_aa: Decimal | None = None   # ipca_plus
    index_code: str | None = None         # index


DEFAULT_CDI = BenchmarkDef(kind="cdi", name="CDI")


def from_meta(meta: dict | None) -> BenchmarkDef:
    if not meta:
        return DEFAULT_CDI
    return BenchmarkDef(
        kind=meta.get("kind", "cdi"),
        name=meta.get("name", meta.get("kind", "CDI")),
        real_rate_aa=Decimal(meta["real_rate_aa"]) if meta.get("real_rate_aa") else None,
        index_code=meta.get("index_code"),
    )


def accumulate(bench: BenchmarkDef, start: date, end: date, market: dict) -> Decimal:
    """Accumulated benchmark return (%) in (start, end].

    `market` carries raw series: {"cdi": [...sgs 12...], "ipca": [...sgs 433...]}.
    """
    if bench.kind == "cdi":
        return metrics.accumulate_bcb_series(market["cdi"], start, end)

    if bench.kind == "ipca_plus":
        if bench.real_rate_aa is None:
            raise ValueError("benchmark ipca_plus requires real_rate_aa")
        # informational convention: whole published months inside the window,
        # plus the real rate over DU/252 of the full window
        factor = ONE
        for item in market["ipca"]:
            month_ref = metrics.parse_bcb_date(item["data"])
            month_start = month_ref  # SGS 433 dates the value at day 1 of the month
            month_end = _last_day_of_month(month_ref)
            if month_start > start and month_end <= end:
                factor *= ONE + Decimal(item["valor"]) / HUNDRED
        du = business_days_between(start, end)
        factor *= (ONE + bench.real_rate_aa / HUNDRED) ** (Decimal(du) / D252)
        return metrics.q_pct((factor - ONE) * HUNDRED)

    # extensible by design; unsupported = declared limitation (Princípio 2)
    raise NotImplementedError(
        f"benchmark '{bench.kind}' ainda não suportado na v1 — limitação declarada"
    )


def _last_day_of_month(d: date) -> date:
    if d.month == 12:
        return date(d.year, 12, 31)
    from datetime import timedelta
    return date(d.year, d.month + 1, 1) - timedelta(days=1)
