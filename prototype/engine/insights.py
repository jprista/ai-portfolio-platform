"""Deterministic attention-point rules (MVP_SCOPE.md §3.3).

Detection is NEVER done by an LLM: rules fire here, with engine numbers;
the narrative layer only phrases what was detected (I1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .models import Position
from . import metrics


@dataclass(frozen=True)
class InsightConfig:
    """Thresholds are engine PARAMETERS with v1 defaults, never fixed
    constants (ENGINE_METHODOLOGY §6, founder decision 2026-07-03).
    Future: populated from OrganizationPolicy (per-office investment policy)."""
    issuer_concentration_limit_pct: Decimal = Decimal("15")
    fgc_limit: Decimal = Decimal("250000")
    maturity_window_days: int = 90
    # Demo reference medians (production: computed from CVM universe per class)
    fund_fee_median_pct: dict = field(
        default_factory=lambda: {"multimercado": Decimal("1.50"), "renda_variavel": Decimal("2.00")}
    )
    sovereign_issuers: frozenset = frozenset({"Tesouro Nacional"})


DEFAULT_CONFIG = InsightConfig()


def _brl(value: Decimal) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


def generate(
    positions: list[Position], ref: date, config: InsightConfig | None = None
) -> list[dict]:
    cfg = config or DEFAULT_CONFIG
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
        if issuer in cfg.sovereign_issuers:
            continue
        data = {"value": value.quantize(Decimal("0.01")), "pct": metrics.q_pct(value / total * Decimal("100"))}
        bank_like = True
        if data["pct"] > cfg.issuer_concentration_limit_pct:
            detail = (
                f"O emissor {issuer} responde por {str(data['pct']).replace('.', ',')}% da carteira "
                f"({_brl(data['value'])}), acima do limite de referência de "
                f"{cfg.issuer_concentration_limit_pct}%."
            )
            if bank_like and data["value"] > cfg.fgc_limit:
                detail += (
                    f" O volume também excede o teto de cobertura do FGC "
                    f"({_brl(cfg.fgc_limit)} por emissor/CPF)."
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
    for item in metrics.upcoming_maturities(positions, ref, cfg.maturity_window_days):
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
        median = cfg.fund_fee_median_pct.get(p.asset_class)
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
