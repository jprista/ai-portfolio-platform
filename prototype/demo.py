"""End-to-end prototype demo — Fase 0.

Pipeline: portfolio JSON -> deterministic engine -> immutable run ->
briefing (markdown) + client report (HTML).

Usage (from the prototype/ directory):  py demo.py
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from engine import insights, metrics, run as run_mod
from engine.models import Flow, Position, Valuation
from narrative.briefing import build_briefing
from report.report import build_report

BASE = Path(__file__).resolve().parent
OUT = BASE / "out"

MONTHS_PT = {1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
             7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"}


def _brl(value) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


def main() -> None:
    portfolio_raw = json.loads((BASE / "data" / "portfolio_familia_almeida.json").read_text(encoding="utf-8"))
    cdi_raw = json.loads((BASE / "data" / "cdi_daily_2026S1.json").read_text(encoding="utf-8"))

    meta = portfolio_raw["meta"]
    ref = date.fromisoformat(meta["reference_date"])
    last_meeting = date.fromisoformat(meta["last_meeting_date"])

    positions = [Position.from_dict(d) for d in portfolio_raw["positions"]]
    valuations = [Valuation.from_dict(d) for d in portfolio_raw["history"]["valuations"]]
    flows = [Flow.from_dict(d) for d in portfolio_raw["history"]["flows"]]

    # ---- engine (single source of numeric truth) ----
    total = metrics.total_value(positions)
    allocation = metrics.allocation_by_class(positions)
    concentration = metrics.concentration_by_issuer(positions)
    liquidity = metrics.liquidity_ladder(positions, ref)
    returns = metrics.chained_returns(valuations, flows)
    attention = insights.generate(positions, ref)

    monthly = []
    for p in returns["periods"]:
        cdi_pct = metrics.accumulate_bcb_series(cdi_raw, p["start"] + timedelta(days=1), p["end"])
        monthly.append({
            "label": f"{MONTHS_PT[p['end'].month]}/{p['end'].year}",
            "portfolio_pct": p["return_pct"],
            "cdi_pct": cdi_pct,
            "start": p["start"], "end": p["end"],
        })

    cdi_total = metrics.accumulate_bcb_series(cdi_raw, valuations[0].day + timedelta(days=1), ref)
    portfolio_total = returns["total_return_pct"]
    pct_of_cdi = (portfolio_total / cdi_total * Decimal("100")).quantize(Decimal("0.01"))
    risk_alloc = sum(
        (allocation[c]["pct"] for c in ("multimercado", "renda_variavel") if c in allocation),
        Decimal("0"),
    )

    # ---- deterministic "what changed since last meeting" ----
    val_at_meeting = max((v for v in valuations if v.day <= last_meeting), key=lambda v: v.day)
    factor = Decimal("1")
    for p in returns["periods"]:
        if p["start"] >= val_at_meeting.day:
            factor *= Decimal("1") + p["return_pct"] / Decimal("100")
    ret_since = ((factor - 1) * Decimal("100")).quantize(Decimal("0.0001"))
    changes = [
        f"Patrimônio passou de {_brl(val_at_meeting.total)} ({val_at_meeting.day:%d/%m/%Y}) "
        f"para {_brl(total)} ({ref:%d/%m/%Y}).",
        f"Retorno no período entre reuniões: {str(ret_since).replace('.', ',')}%.",
    ]
    for f in flows:
        if f.day > last_meeting:
            kind = "Aporte" if f.amount > 0 else "Resgate"
            changes.append(f"{kind} de {_brl(abs(f.amount))} em {f.day:%d/%m/%Y}.")

    agenda_by_code = {
        "CONCENTRACAO_EMISSOR": "Decidir tratamento da concentração por emissor apontada pelo motor.",
        "VENCIMENTO_PROXIMO": "Definir destino do vencimento próximo (LCA) antes da data.",
        "CUSTO_ACIMA_MEDIANA": "Revisar custo do fundo com taxa acima da mediana da classe.",
        "CONFIANCA_DADO": "Atualizar fonte da posição com selo de confiança C (previdência).",
    }
    agenda = [agenda_by_code[i["code"]] for i in attention if i["code"] in agenda_by_code]
    agenda.append("Revisar objetivos da família e horizonte das parcelas de risco.")
    # de-duplicate preserving order
    agenda = list(dict.fromkeys(agenda))

    conf_mix: dict[str, int] = {}
    for p in positions:
        conf_mix[p.confidence] = conf_mix.get(p.confidence, 0) + 1
    conf_mix = dict(sorted(conf_mix.items()))

    outputs = {
        "total_value": total,
        "allocation": allocation,
        "concentration": concentration,
        "liquidity": liquidity,
        "returns": returns,
        "cdi_total_pct": cdi_total,
        "insights": attention,
    }
    run = run_mod.build_run(portfolio_raw, {"cdi_series": "bcb/sgs.12 2026S1"}, outputs)

    ctx = {
        "meta": meta,
        "run_id": run["run_id"],
        "engine_version": run["engine_version"],
        "total_value": total,
        "allocation": allocation,
        "liquidity": liquidity,
        "positions": positions,
        "insights": attention,
        "confidence_mix": conf_mix,
        "changes_since_last_meeting": changes,
        "agenda": agenda,
        "performance": {
            "monthly": monthly,
            "portfolio_total_pct": portfolio_total,
            "cdi_total_pct": cdi_total,
            "pct_of_cdi": pct_of_cdi,
            "risk_assets_alloc_pct": risk_alloc,
        },
    }

    OUT.mkdir(exist_ok=True)
    (OUT / f"run_{run['run_id']}.json").write_text(run_mod.serialize(run), encoding="utf-8")
    (OUT / "briefing_familia_almeida.md").write_text(build_briefing(ctx), encoding="utf-8")
    (OUT / "relatorio_familia_almeida.html").write_text(build_report(ctx), encoding="utf-8")

    print(f"Run do motor      : {run['run_id']} (engine v{run['engine_version']})")
    print(f"Patrimonio total  : {_brl(total)}")
    print(f"Retorno semestre  : {portfolio_total}%  |  CDI: {cdi_total}%  |  %CDI: {pct_of_cdi}%")
    print(f"Pontos de atencao : {len(attention)}")
    for i in attention:
        print(f"  - [{i['severity']}] {i['title']}")
    print(f"Saidas em         : {OUT}")


if __name__ == "__main__":
    main()
