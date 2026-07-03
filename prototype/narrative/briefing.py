"""Meeting briefing builder (deterministic template).

Prototype note: in production this layer is an LLM (Claude) constrained by
the AnalysisContext + Verificador de Proveniência Numérica
(AI_ARCHITECTURE.md). In the prototype the narrative is a deterministic
template filled exclusively with engine outputs — which by construction
satisfies I1 (no number is born outside the engine).
"""
from __future__ import annotations

CLASS_LABELS = {
    "caixa": "Caixa e liquidez",
    "renda_fixa_pos": "Renda fixa pós-fixada",
    "renda_fixa_inflacao": "Renda fixa inflação",
    "multimercado": "Multimercado",
    "renda_variavel": "Renda variável",
    "previdencia": "Previdência",
}


def _fmt_brl(value) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


def _fmt_pct(value) -> str:
    return f"{value:.2f}".replace(".", ",") + "%"


def build_briefing(ctx: dict) -> str:
    meta = ctx["meta"]
    perf = ctx["performance"]
    lines: list[str] = []
    add = lines.append

    add(f"# Briefing de reunião — {meta['family']}")
    add("")
    add(f"**Reunião:** {meta['next_meeting_date']} · **Última reunião:** {meta['last_meeting_date']} · "
        f"**Data-base dos dados:** {meta['reference_date']}")
    add(f"**Patrimônio consolidado:** {_fmt_brl(ctx['total_value'])} · "
        f"**Run do motor:** `{ctx['run_id']}` (v{ctx['engine_version']})")
    add("")

    add("## Resumo executivo")
    add("")
    add(f"No semestre, a carteira rendeu **{_fmt_pct(perf['portfolio_total_pct'])}**, contra "
        f"**{_fmt_pct(perf['cdi_total_pct'])}** do CDI no mesmo período "
        f"(**{_fmt_pct(perf['pct_of_cdi'])} do CDI**). A diferença é explicada principalmente pela "
        f"parcela de renda variável e multimercado ({_fmt_pct(perf['risk_assets_alloc_pct'])} da carteira), "
        "cujo objetivo é retorno acima do CDI em horizonte longo — não no semestre. "
        "O ponto estrutural que merece decisão nesta reunião não é performance: são os itens de "
        "concentração e vencimento listados abaixo.")
    add("")

    add("## O que mudou desde a última reunião")
    add("")
    for item in ctx["changes_since_last_meeting"]:
        add(f"- {item}")
    add("")

    add("## Pontos de atenção (detecção determinística do motor)")
    add("")
    for i, insight in enumerate(ctx["insights"], start=1):
        add(f"{i}. **[{insight['severity'].upper()}] {insight['title']}** — {insight['detail']}")
    add("")

    add("## Alocação atual")
    add("")
    add("| Classe | Valor | % |")
    add("|---|---|---|")
    for cls, data in sorted(ctx["allocation"].items(), key=lambda kv: kv[1]["value"], reverse=True):
        add(f"| {CLASS_LABELS.get(cls, cls)} | {_fmt_brl(data['value'])} | {_fmt_pct(data['pct'])} |")
    add("")

    add("## Liquidez")
    add("")
    add("| Janela | Valor | % |")
    add("|---|---|---|")
    for bucket, data in ctx["liquidity"].items():
        add(f"| {bucket} | {_fmt_brl(data['value'])} | {_fmt_pct(data['pct'])} |")
    add("")

    add("## Pauta sugerida")
    add("")
    for i, item in enumerate(ctx["agenda"], start=1):
        add(f"{i}. {item}")
    add("")
    add("---")
    add("*Material de uso interno do profissional. Análise descritiva gerada por motor determinístico "
        "auditável; não constitui recomendação de investimento. Todos os números são rastreáveis ao run "
        f"`{ctx['run_id']}`.*")
    return "\n".join(lines)
