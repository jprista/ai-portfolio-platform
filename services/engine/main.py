"""Engine service — internal API (API_SPEC.md §5).

Stateless and tenant-unaware by design (ARCHITECTURE.md §4): receives
snapshots, returns immutable run outputs. The web service is the only
caller; auth, tenancy and persistence live outside.

Run:  uvicorn main:app --app-dir services/engine --port 8500
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from engine_core import accrual, benchmark, insights, metrics
from engine_core import run as run_mod
from engine_core.models import Flow, Position, Valuation

app = FastAPI(title="AI Portfolio Platform — Engine", version=run_mod.ENGINE_VERSION)


class AnalyzeRequest(BaseModel):
    reference_date: date
    positions: list[dict]
    history: dict = Field(default_factory=lambda: {"valuations": [], "flows": []})
    market: dict = Field(default_factory=dict)          # {"cdi": [...sgs 12...], "ipca": [...]}
    benchmark: dict | None = None                        # BenchmarkDef meta; default CDI
    policy: dict | None = None                           # threshold overrides (InsightConfig)
    last_meeting_date: date | None = None


class ValuateRequest(BaseModel):
    kind: str                                            # cdi_percent | prefixado | ipca_vna
    principal: str
    start: date
    reference_date: date
    rate_aa: str | None = None
    pct_cdi: str | None = None
    anniversary_day: int | None = None
    market: dict = Field(default_factory=dict)


def _insight_config(policy: dict | None) -> insights.InsightConfig:
    if not policy:
        return insights.DEFAULT_CONFIG
    kwargs: dict[str, Any] = {}
    if "issuer_concentration_limit_pct" in policy:
        kwargs["issuer_concentration_limit_pct"] = Decimal(str(policy["issuer_concentration_limit_pct"]))
    if "fgc_limit" in policy:
        kwargs["fgc_limit"] = Decimal(str(policy["fgc_limit"]))
    if "maturity_window_days" in policy:
        kwargs["maturity_window_days"] = int(policy["maturity_window_days"])
    return insights.InsightConfig(**kwargs)


@app.get("/engine/health")
def health() -> dict:
    return {"status": "ok", "engine_version": run_mod.ENGINE_VERSION}


@app.post("/engine/analyze")
def analyze(req: AnalyzeRequest) -> JSONResponse:
    try:
        positions = [Position.from_dict(d) for d in req.positions]
        valuations = [Valuation.from_dict(d) for d in req.history.get("valuations", [])]
        flows = [Flow.from_dict(d) for d in req.history.get("flows", [])]
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"VALIDATION_FAILED: {e}")

    cfg = _insight_config(req.policy)
    ref = req.reference_date

    outputs: dict[str, Any] = {
        "total_value": metrics.total_value(positions),
        "allocation": metrics.allocation_by_class(positions),
        "concentration": metrics.concentration_by_issuer(positions),
        "liquidity": metrics.liquidity_ladder(positions, ref),
        "insights": insights.generate(positions, ref, cfg),
        "declared_limitations": [],
    }

    if len(valuations) >= 2:
        returns = metrics.chained_returns(valuations, flows)
        outputs["returns"] = returns
        if req.market.get("cdi"):
            bench_def = benchmark.from_meta(req.benchmark)
            try:
                bench_total = benchmark.accumulate(
                    bench_def, valuations[0].day + timedelta(days=1), ref, req.market
                )
                outputs["benchmark_pct"] = bench_total
                outputs["benchmark_comparison"] = metrics.benchmark_comparison(
                    returns["total_return_pct"], bench_total
                )
            except NotImplementedError as e:
                outputs["declared_limitations"].append(
                    {"code": "BENCHMARK_UNSUPPORTED", "detail": str(e)}
                )
    else:
        outputs["declared_limitations"].append(
            {"code": "DATA_INSUFFICIENT", "detail": "menos de 2 valorações — retornos não calculados"}
        )

    run = run_mod.build_run(
        {"positions": req.positions, "history": req.history, "reference_date": str(ref)},
        {"market_keys": sorted(req.market.keys()), "policy": req.policy or "default"},
        outputs,
    )
    return JSONResponse(content=json.loads(run_mod.serialize(run)))


@app.post("/engine/valuate")
def valuate(req: ValuateRequest) -> JSONResponse:
    principal = Decimal(req.principal)
    result: dict[str, Any]
    if req.kind == "cdi_percent":
        series = accrual.parse_bcb_series(req.market.get("cdi", []))
        value = accrual.cdi_percent_accrual(
            principal, Decimal(req.pct_cdi or "100"), series, req.start, req.reference_date
        )
        result = {"value": str(value.quantize(Decimal("0.01")))}
    elif req.kind == "prefixado":
        value = accrual.prefixado_du252(principal, Decimal(req.rate_aa or "0"), req.start, req.reference_date)
        result = {"value": str(value.quantize(Decimal("0.01")))}
    elif req.kind == "ipca_vna":
        ipca = accrual.parse_bcb_series(req.market.get("ipca", []))
        vna = accrual.ipca_vna(
            principal, Decimal(req.rate_aa or "0"), req.start, req.reference_date,
            ipca, anniversary_day=req.anniversary_day,
        )
        result = {
            "value": str(vna.value.quantize(Decimal("0.01"))),
            "stub_used_fallback": vna.stub_used_fallback,
            "declared_limitations": (
                [{"code": "VNA_PROJECTION_FALLBACK",
                  "detail": "período em aberto pro-rata com último IPCA publicado (projeção ANBIMA pendente)"}]
                if vna.stub_used_fallback else []
            ),
        }
    else:
        raise HTTPException(status_code=422, detail=f"INSTRUMENT_UNSUPPORTED: kind '{req.kind}'")
    result["engine_version"] = run_mod.ENGINE_VERSION
    return JSONResponse(content=result)
