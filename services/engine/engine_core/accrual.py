"""Asset valuation by accrual — ENGINE_METHODOLOGY §3 (v1.1, approved).

Every function returns the raw Decimal value (caller quantizes for display)
plus, where the spec demands it, provenance flags (e.g. VNA stub fallback).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import NamedTuple

from .calendar_br import business_days_between, next_business_day

HUNDRED = Decimal("100")
ONE = Decimal("1")
D252 = Decimal("252")


def parse_bcb_series(series: list[dict]) -> list[tuple[date, Decimal]]:
    return [
        (datetime.strptime(item["data"], "%d/%m/%Y").date(), Decimal(item["valor"]))
        for item in series
    ]


def cdi_percent_accrual(
    principal: Decimal, pct_cdi: Decimal, cdi_daily: list[tuple[date, Decimal]],
    start: date, ref: date,
) -> Decimal:
    """§3.1 — V = P × ∏[1 + (fator_diário − 1) × p], SGS 12 daily rate as published."""
    p = pct_cdi / HUNDRED
    factor = ONE
    for day, rate in cdi_daily:
        if start < day <= ref:
            factor *= ONE + (rate / HUNDRED) * p
    return principal * factor


def prefixado_du252(principal: Decimal, rate_aa: Decimal, start: date, ref: date) -> Decimal:
    """§3.2 — curve accrual: V = P × (1 + taxa)^(du/252)."""
    du = business_days_between(start, ref)
    return principal * (ONE + rate_aa / HUNDRED) ** (Decimal(du) / D252)


class VnaResult(NamedTuple):
    value: Decimal
    ipca_factor: Decimal
    stub_factor: Decimal
    real_factor: Decimal
    stub_used_fallback: bool  # True = projection fallback (last published IPCA) — flag provenance


def _add_months(d: date, months: int, day: int) -> date:
    month_index = d.year * 12 + (d.month - 1) + months
    year, month = divmod(month_index, 12)
    month += 1
    # clamp day to month length
    for dd in (day, 30, 29, 28):
        try:
            return date(year, month, dd)
        except ValueError:
            continue
    raise AssertionError("unreachable")


def _last_published_ipca(ipca_monthly: list[tuple[date, Decimal]], at: date) -> Decimal:
    """IPCA of the month PRIOR to `at`'s month (last published at an anniversary, §3.3)."""
    prior = _add_months(date(at.year, at.month, 1), -1, 1)
    for month_ref, value in ipca_monthly:
        if (month_ref.year, month_ref.month) == (prior.year, prior.month):
            return value
    # walk back to the most recent available before `prior` (data gaps)
    candidates = [(m, v) for m, v in ipca_monthly if m <= prior]
    if not candidates:
        raise ValueError(f"no IPCA available before {at}")
    return max(candidates, key=lambda mv: mv[0])[1]


def ipca_vna(
    principal: Decimal, real_rate_aa: Decimal, start: date, ref: date,
    ipca_monthly: list[tuple[date, Decimal]],
    anniversary_day: int | None = None,
    projection_pct: Decimal | None = None,
) -> VnaResult:
    """§3.3 — VNA exato: anniversaries (adjusted to next business day),
    monthly factor = last IPCA published at the anniversary, open-period
    pro-rata by DU with ANBIMA projection (fallback: last published IPCA,
    flagged for provenance)."""
    ann_day = anniversary_day if anniversary_day is not None else start.day

    # nominal anniversaries after start, adjusted; collect those <= ref
    ipca_factor = ONE
    last_anniv_adj = start
    k = 1
    while True:
        nominal = _add_months(start, k, ann_day)
        adjusted = next_business_day(nominal)
        if adjusted > ref:
            next_anniv_adj = adjusted
            break
        ipca_factor *= ONE + _last_published_ipca(ipca_monthly, adjusted) / HUNDRED
        last_anniv_adj = adjusted
        k += 1

    # open-period stub (§3.3)
    stub_factor = ONE
    used_fallback = False
    du_elapsed = business_days_between(last_anniv_adj, ref)
    if du_elapsed > 0:
        du_period = business_days_between(last_anniv_adj, next_anniv_adj)
        proj = projection_pct
        if proj is None:
            proj = _last_published_ipca(ipca_monthly, ref)
            used_fallback = True
        stub_factor = (ONE + proj / HUNDRED) ** (Decimal(du_elapsed) / Decimal(du_period))

    real_factor = (ONE + real_rate_aa / HUNDRED) ** (
        Decimal(business_days_between(start, ref)) / D252
    )
    value = principal * ipca_factor * stub_factor * real_factor
    return VnaResult(value, ipca_factor, stub_factor, real_factor, used_fallback)
