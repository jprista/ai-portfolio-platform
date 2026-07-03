"""Deterministic attention-point rules (MVP_SCOPE.md §3.3).

Detection is NEVER done by an LLM: rules fire here, with engine numbers;
the narrative layer only phrases what was detected (I1).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .models import Position
from . import metrics

ISSUER_CONCENTRATION_LIMIT_PCT = Decimal("15")
FGC_LIMIT = Decimal("250000")
MATURITY_WINDOW_DAYS = 90
# Demo reference medians (production: computed from CVM universe per class)
FUND_FEE_MEDIAN_PCT = {"multimercado": Decimal("1.50"), "renda_variavel": Decimal("2.00")}
SOVEREIGN_ISSUERS = {"Tesouro Nacional"}


def _brl(value: Decimal) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


def generate(positions: list[Position], ref: date) -> list[dict]:
    out: list[dict] = []
    total = metrics.total_value(positions)

    # Rule 1 — private CREDIT issuer concentration (and FGC ceiling).
    # Scope: credit-risk classes only. Concentration in a fund MANAGER is a
    # different risk with a different threshold — deliberately out of the
    # prototype (candidate for v1 rules), caught by golden test on 2026-07-03.
    credit_classes = ("caixa", "renda_fixa_pos", "renda_fixa_inflacao")
    credit_positions = [p for p in positions if p.asset_class in credit_classes]
    issuer_credit: dict[str, Decimal] = {}
    for p in credit_positions:
        issuer_credit[p.issuer] = issuer_credit.get(p.issuer, Decimal("0")) + p.value
    for issuer, value in sorted(issuer_credit.items(), key=lambda kv: kv[1], reverse=True):
        if issuer in SOVEREIGN_ISSUERS:
            continue
        data = {"value": value.quantize(Decimal("0.01")), "pct": metrics.q_pct(value / total * Decimal("100"))}
        bank_like = True
        if data["pct"] > ISSUER_CONCENTRATION_LIMIT_PCT:
            detail = (
                f"O emissor {issuer} responde por {str(data['pct']).replace('.', ',')}% da carteira "
                f"({_brl(data['value'])}), acima do limite de referência de "
                f"{ISSUER_CONCENTRATION_LIMIT_PCT}%."
            )
            if bank_like and data["value"] > FGC_LIMIT:
                detail += (
                    f" O volume também excede o teto de cobertura do FGC "
                    f"({_brl(FGC_LIMIT)} por emissor/CPF)."
                )
            out.append(
                {
                    "code": "CONCENTRACAO_EMISSOR",
                    "severity": "alta",
                    "title": f"Concentração em {issuer}",
                    "detail": detail,
                }
            )

    # Rule 2 — maturities inside the window
    for item in metrics.upcoming_maturities(positions, ref, MATURITY_WINDOW_DAYS):
        p = item["position"]
        out.append(
            {
                "code": "VENCIMENTO_PROXIMO",
                "severity": "média",
                "title": f"Vencimento em {item['days']} dias: {p.name}",
                "detail": (
                    f"{p.name} ({_brl(p.value)}) vence em {p.maturity:%d/%m/%Y}. "
                    "Definir destino do recurso antes do vencimento evita dias parados em caixa."
                ),
            }
        )

    # Rule 3 — fund fee above class reference median
    for p in positions:
        median = FUND_FEE_MEDIAN_PCT.get(p.asset_class)
        if p.fund_fee_pct is not None and median is not None and p.fund_fee_pct > median:
            out.append(
                {
                    "code": "CUSTO_ACIMA_MEDIANA",
                    "severity": "média",
                    "title": f"Taxa acima da mediana: {p.name}",
                    "detail": (
                        f"{p.name} cobra {p.fund_fee_pct}% a.a. de administração, contra mediana de "
                        f"{median}% a.a. da classe (referência demo). Impacto anual estimado: "
                        f"{_brl((p.value * (p.fund_fee_pct - median) / Decimal('100')).quantize(Decimal('0.01')))}."
                    ),
                }
            )

    # Rule 4 — data confidence below B
    for p in positions:
        if p.confidence in ("C", "D"):
            out.append(
                {
                    "code": "CONFIANCA_DADO",
                    "severity": "baixa",
                    "title": f"Dado com confiança {p.confidence}: {p.name}",
                    "detail": (
                        f"A posição {p.name} tem selo de confiança {p.confidence} "
                        "(DATA_STRATEGY §5). Recomenda-se atualizar a fonte antes da reunião."
                    ),
                }
            )

    severity_order = {"alta": 0, "média": 1, "baixa": 2}
    out.sort(key=lambda i: severity_order[i["severity"]])
    return out
