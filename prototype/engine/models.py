"""Prototype domain models — Fase 0 demonstrable prototype.

Inherited rule (ENGINEERING_PRINCIPLES.md): float is forbidden on money
paths; every monetary value is Decimal, parsed from strings.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Position:
    name: str
    asset_class: str  # caixa | renda_fixa_pos | renda_fixa_inflacao | multimercado | renda_variavel | previdencia
    issuer: str
    value: Decimal  # market/curve value at reference date
    liquidity: str  # D0 | D+2 | D+30 | D+60 | vencimento
    confidence: str  # A | B | C | D (DATA_STRATEGY.md §5)
    maturity: date | None = None
    index_desc: str | None = None  # e.g. "110% CDI", "IPCA + 6,20%"
    fund_fee_pct: Decimal | None = None  # management fee, % p.a.

    @staticmethod
    def from_dict(d: dict) -> "Position":
        return Position(
            name=d["name"],
            asset_class=d["asset_class"],
            issuer=d["issuer"],
            value=Decimal(d["value"]),
            liquidity=d["liquidity"],
            confidence=d["confidence"],
            maturity=date.fromisoformat(d["maturity"]) if d.get("maturity") else None,
            index_desc=d.get("index_desc"),
            fund_fee_pct=Decimal(d["fund_fee_pct"]) if d.get("fund_fee_pct") else None,
        )


@dataclass(frozen=True)
class Flow:
    day: date
    amount: Decimal  # positive = contribution; negative = withdrawal

    @staticmethod
    def from_dict(d: dict) -> "Flow":
        return Flow(day=date.fromisoformat(d["date"]), amount=Decimal(d["amount"]))


@dataclass(frozen=True)
class Valuation:
    day: date
    total: Decimal

    @staticmethod
    def from_dict(d: dict) -> "Valuation":
        return Valuation(day=date.fromisoformat(d["date"]), total=Decimal(d["total"]))
