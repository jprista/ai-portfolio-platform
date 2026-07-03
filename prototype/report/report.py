"""Client-facing report generator (HTML, print-ready A4).

Prototype of the 'Fábrica de material' pillar: institutional visual standard,
the ADVISOR's brand (we are invisible), every figure from the engine run.
Production converts this HTML to PDF via Playwright (TECH_STACK.md).
"""
from __future__ import annotations

from .style import CSS  # separated to keep this file readable

CLASS_LABELS = {
    "caixa": "Caixa e liquidez",
    "renda_fixa_pos": "Renda fixa pós-fixada",
    "renda_fixa_inflacao": "Renda fixa inflação",
    "multimercado": "Multimercado",
    "renda_variavel": "Renda variável",
    "previdencia": "Previdência",
}

CONF_LABEL = {"A": "Alta", "B": "Boa", "C": "Atenção", "D": "Manual"}


def _brl(value) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


def _pct(value) -> str:
    return f"{value:.2f}".replace(".", ",") + "%"


def build_report(ctx: dict) -> str:
    meta = ctx["meta"]
    perf = ctx["performance"]

    alloc_rows = ""
    for cls, data in sorted(ctx["allocation"].items(), key=lambda kv: kv[1]["value"], reverse=True):
        pct = float(data["pct"])
        alloc_rows += f"""
        <div class="alloc-row">
          <div class="alloc-label">{CLASS_LABELS.get(cls, cls)}</div>
          <div class="alloc-bar-track"><div class="alloc-bar" style="width:{pct:.2f}%"></div></div>
          <div class="alloc-value">{_pct(data['pct'])} · {_brl(data['value'])}</div>
        </div>"""

    perf_rows = ""
    for p in perf["monthly"]:
        perf_rows += (
            f"<tr><td>{p['label']}</td><td class='num'>{_pct(p['portfolio_pct'])}</td>"
            f"<td class='num'>{_pct(p['cdi_pct'])}</td></tr>"
        )

    insight_cards = ""
    for insight in ctx["insights"]:
        insight_cards += f"""
        <div class="card sev-{insight['severity'].replace('é','e')}">
          <div class="card-sev">{insight['severity'].upper()}</div>
          <div class="card-title">{insight['title']}</div>
          <div class="card-detail">{insight['detail']}</div>
        </div>"""

    pos_rows = ""
    for p in ctx["positions"]:
        idx = p.index_desc or "—"
        mat = p.maturity.strftime("%d/%m/%Y") if p.maturity else "—"
        pos_rows += (
            f"<tr><td>{p.name}</td><td>{CLASS_LABELS.get(p.asset_class, p.asset_class)}</td>"
            f"<td>{idx}</td><td>{mat}</td><td class='num'>{_brl(p.value)}</td>"
            f"<td class='conf conf-{p.confidence}'>{p.confidence} · {CONF_LABEL[p.confidence]}</td></tr>"
        )

    conf_mix = " · ".join(f"{k}: {v}" for k, v in ctx["confidence_mix"].items())

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Revisão de carteira — {meta['family']}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="org">{meta['organization']}</div>
  <h1>Revisão de carteira</h1>
  <div class="family">{meta['family']}</div>
  <div class="ref">Data-base: {meta['reference_date']} · Preparado por {meta['advisor']}</div>
</header>

<section>
  <h2>Resumo</h2>
  <div class="kpis">
    <div class="kpi"><div class="kpi-label">Patrimônio consolidado</div><div class="kpi-value">{_brl(ctx['total_value'])}</div></div>
    <div class="kpi"><div class="kpi-label">Retorno no semestre</div><div class="kpi-value">{_pct(perf['portfolio_total_pct'])}</div></div>
    <div class="kpi"><div class="kpi-label">CDI no período</div><div class="kpi-value">{_pct(perf['cdi_total_pct'])}</div></div>
    <div class="kpi"><div class="kpi-label">% do CDI</div><div class="kpi-value">{_pct(perf['pct_of_cdi'])}</div></div>
  </div>
</section>

<section>
  <h2>Alocação por classe</h2>
  {alloc_rows}
</section>

<section>
  <h2>Performance mensal — carteira × CDI</h2>
  <table>
    <thead><tr><th>Mês</th><th class="num">Carteira</th><th class="num">CDI</th></tr></thead>
    <tbody>{perf_rows}</tbody>
    <tfoot><tr><td><strong>Acumulado</strong></td>
      <td class="num"><strong>{_pct(perf['portfolio_total_pct'])}</strong></td>
      <td class="num"><strong>{_pct(perf['cdi_total_pct'])}</strong></td></tr></tfoot>
  </table>
  <p class="method-note">Retornos calculados por Modified Dietz mensal encadeado (aproximação de TWR),
  com fluxos ponderados por dia. CDI: série SGS 12 do Banco Central, acumulada por capitalização diária.</p>
</section>

<section class="page-break">
  <h2>Pontos de atenção</h2>
  {insight_cards}
</section>

<section>
  <h2>Posições</h2>
  <table>
    <thead><tr><th>Ativo</th><th>Classe</th><th>Indexador</th><th>Vencimento</th>
      <th class="num">Valor</th><th>Confiança do dado</th></tr></thead>
    <tbody>{pos_rows}</tbody>
    <tfoot><tr><td colspan="4"><strong>Total</strong></td>
      <td class="num"><strong>{_brl(ctx['total_value'])}</strong></td><td></td></tr></tfoot>
  </table>
</section>

<section>
  <h2>Nota metodológica e de conformidade</h2>
  <p>Todos os valores deste material foram produzidos por motor de cálculo determinístico, versão
  <strong>{ctx['engine_version']}</strong>, execução <strong>{ctx['run_id']}</strong> — reproduzível e
  auditável. Mix de confiança dos dados (selos A–D): {conf_mix}. Posições com selo C ou D estão
  sinalizadas e devem ter a fonte atualizada.</p>
  <p class="disclaimer">Este material tem caráter exclusivamente informativo e analítico. Não constitui
  oferta, recomendação ou aconselhamento de investimento. As decisões de investimento são de
  responsabilidade do profissional habilitado que acompanha a família, nos termos da regulamentação
  CVM aplicável. Rentabilidade passada não é garantia de rentabilidade futura.</p>
</section>

<footer>
  {meta['organization']} · Revisão de carteira · {meta['family']} · run {ctx['run_id']}
</footer>
</body>
</html>"""
