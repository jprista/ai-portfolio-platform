import { notFound } from "next/navigation";
import { WorkspaceClient, type WorkspaceProps } from "@/components/workspace-client";
import { requireOrg } from "@/lib/auth";
import { getMeetingDetail, type PositionRow } from "@/lib/data";
import { brl, pct } from "@/lib/format";

export const dynamic = "force-dynamic";

const CLASS_LABEL: Record<string, string> = {
  renda_fixa_pos: "Renda fixa pós-fixada",
  renda_variavel: "Renda variável",
  renda_fixa_inflacao: "Renda fixa inflação",
  multimercado: "Multimercado",
  caixa: "Caixa e liquidez",
  previdencia: "Previdência",
};
const LIQ_LABEL: Record<string, string> = {
  "D0 — imediata": "D0 — imediata", "até 30 dias": "Até 30 dias",
  "31–360 dias": "31 a 360 dias", "acima de 360 dias": "Acima de 360 dias",
  D0: "D0 — imediata",
};
const INDEX_LABEL: Record<string, string> = {
  cdi_pct: "% CDI", ipca_plus: "IPCA+", selic: "SELIC", pre: "Prefixado", none: "—",
};
const AGENDA_BY_CODE: Record<string, string> = {
  CONCENTRACAO_EMISSOR: "Revisar concentração por emissor apontada pelo motor.",
  FGC_TITULAR: "Revisar exposições acima do teto do FGC por titular.",
  VENCIMENTO_PROXIMO: "Definir destino dos vencimentos próximos identificados pelo motor.",
  CUSTO_ACIMA_MEDIANA: "Revisar custos de fundos acima da mediana da classe.",
  CONFIANCA_DADO: "Atualizar fontes de dados com selo de confiança C ou D.",
};

// category (identifiers->>'category') tem prioridade — dado real informado na confirmação
// de extração (DOMAIN_MODEL §9.3); heurística por kind/index_kind é o fallback para dados
// sem categoria explícita (ex.: carteira sintética Almeida).
function classify(p: PositionRow): string {
  if (p.category) return p.category;
  if (p.kind === "pension_fund") return "previdencia";
  if (p.kind === "fund") return "multimercado";
  if (["equity", "etf", "fii", "bdr"].includes(p.kind)) return "renda_variavel";
  if (p.index_kind === "ipca_plus") return "renda_fixa_inflacao";
  if (p.name.toLowerCase().includes("liquidez diária") || p.kind === "cash") return "caixa";
  return "renda_fixa_pos";
}

function liqOf(p: PositionRow): string {
  if (p.name.toLowerCase().includes("liquidez diária") || p.kind === "cash") return "D0";
  if (p.kind === "pension_fund") return "D+60";
  if (p.kind === "fund") return "D+30";
  if (p.maturity) return "Vencimento";
  return "D+2";
}

type Outputs = {
  total_value: string;
  allocation: Record<string, { value: string; pct: string }>;
  liquidity: Record<string, { value: string; pct: string }>;
  returns?: { total_return_pct: string };
  benchmark_pct?: string;
  benchmark_comparison?: { mode: string; value: string };
  insights: { severity: "alta" | "média" | "baixa"; title: string; detail: string }[];
  narrative?: {
    risk_assets_alloc_pct: string;
    changes: string[];
    agenda: string[];
    class_readings: Record<string, string>;
    concentrations: { label: string; value: string; note: string; bad: boolean }[];
  };
};

export default async function ReuniaoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { orgId } = await requireOrg();
  const detail = await getMeetingDetail(orgId, id);
  if (!detail || !detail.run) notFound();

  const out = detail.run.outputs as Outputs;
  const total = Number(out.total_value);
  const hasHistory = Boolean(out.returns && out.benchmark_comparison);
  const bench = out.benchmark_comparison;
  const nAlta = out.insights.filter((i) => i.severity === "alta").length;

  const groups = Object.entries(out.allocation)
    .sort((a, b) => Number(b[1].value) - Number(a[1].value))
    .map(([cls, agg]) => {
      const clsPositions = detail.positions.filter((p) => classify(p) === cls);
      const byIssuer = new Map<string, number>();
      for (const p of clsPositions) byIssuer.set(p.issuer, (byIssuer.get(p.issuer) ?? 0) + Number(p.value));
      const [topIssuer, topValue] = [...byIssuer.entries()].sort((a, b) => b[1] - a[1])[0] ?? ["—", 0];
      const reading =
        out.narrative?.class_readings[cls] ??
        `${clsPositions.length} posiç${clsPositions.length > 1 ? "ões" : "ão"}, ${pct(agg.pct)} da carteira` +
          (topValue / Number(agg.value) > 0.4 ? `, com maior exposição em ${topIssuer} (${pct((topValue / total) * 100)}).` : ".");
      return {
        cls: CLASS_LABEL[cls] ?? cls,
        subtotal: brl(agg.value),
        pct: pct(agg.pct),
        reading,
        positions: clsPositions.map((p) => ({
          name: p.name,
          holder: p.holder ?? "—",
          index: p.index_kind === "cdi_pct" || p.index_kind === "ipca_plus" ? p.name.match(/(\d{2,3}(?:,\d+)?% CDI|IPCA\s?\+\s?[\d,]+%)/)?.[0] ?? INDEX_LABEL[p.index_kind] : INDEX_LABEL[p.index_kind] ?? "—",
          maturity: p.maturity ? p.maturity.split("-").reverse().join("/") : "—",
          liq: liqOf(p),
          seal: p.confidence,
          value: brl(p.value),
          pct: pct((Number(p.value) / total) * 100),
        })),
      };
    });

  const dateLabel = new Date(detail.scheduled_for).toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo",
  });

  const confCount = new Map<string, number>();
  for (const p of detail.positions) confCount.set(p.confidence, (confCount.get(p.confidence) ?? 0) + 1);

  const topClassEntry = Object.entries(out.allocation).sort((a, b) => Number(b[1].value) - Number(a[1].value))[0];
  const topClassLabel = topClassEntry ? CLASS_LABEL[topClassEntry[0]] ?? topClassEntry[0] : "—";
  const topClassPct = topClassEntry ? pct(topClassEntry[1].pct) : "—";

  const kpis = hasHistory && out.returns && bench
    ? [
        { label: "Patrimônio consolidado", value: brl(out.total_value) },
        { label: "Retorno no semestre", value: pct(out.returns.total_return_pct) },
        { label: "CDI no período", value: pct(out.benchmark_pct!) },
        bench.mode === "pct_of_benchmark"
          ? { label: "% do CDI", value: pct(bench.value) }
          : { label: "Diferença vs. CDI", value: `${pct(bench.value)} p.p.` },
      ]
    : [
        { label: "Patrimônio consolidado", value: brl(out.total_value) },
        { label: "Classes de ativos", value: String(Object.keys(out.allocation).length) },
        { label: "Posições", value: String(detail.positions.length) },
        { label: "Pontos de atenção", value: nAlta > 0 ? `${out.insights.length} (${nAlta} alta)` : String(out.insights.length) },
      ];

  const resumo = out.narrative
    ? `No semestre, a carteira rendeu ${pct(out.returns!.total_return_pct)}, contra ${pct(out.benchmark_pct!)} do CDI no mesmo período` +
      (bench!.mode === "pct_of_benchmark" ? ` (${pct(bench!.value)} do CDI).` : ` (${pct(bench!.value)} p.p. vs. CDI — em retorno negativo, % do CDI não é significativo).`) +
      ` A diferença é explicada principalmente pela parcela de renda variável e multimercado (${pct(out.narrative.risk_assets_alloc_pct)} da carteira), cujo objetivo é retorno acima do CDI em horizonte longo. O ponto estrutural desta reunião não é performance: são concentração e vencimento.`
    : `Primeira análise consolidada desta carteira, com patrimônio total de ${brl(out.total_value)} distribuído em ${Object.keys(out.allocation).length} classes de ativos. Maior concentração em ${topClassLabel} (${topClassPct}). Ainda não há histórico de retorno suficiente para comparação com o CDI — a evolução passa a ser acompanhada a partir desta análise.`;

  const mudancas = out.narrative?.changes ?? ["Primeira análise desta carteira nesta plataforma — sem reunião anterior para comparação."];

  function agendaLineFor(insight: { title: string; detail: string }): string {
    const t = insight.title.toLowerCase();
    if (insight.detail.includes("FGC")) return AGENDA_BY_CODE.FGC_TITULAR;
    if (t.includes("concentra")) return AGENDA_BY_CODE.CONCENTRACAO_EMISSOR;
    if (t.includes("vencimento")) return AGENDA_BY_CODE.VENCIMENTO_PROXIMO;
    if (t.includes("taxa") || t.includes("custo")) return AGENDA_BY_CODE.CUSTO_ACIMA_MEDIANA;
    if (t.includes("confiança")) return AGENDA_BY_CODE.CONFIANCA_DADO;
    return insight.title;
  }

  const agenda = out.narrative?.agenda ??
    [...new Set(out.insights.map(agendaLineFor))].concat("Revisar objetivos e horizonte de investimento da família.");

  const concentracoes = out.narrative?.concentrations ?? out.insights
    .filter((i) => i.detail.includes("FGC") || i.title.toLowerCase().includes("concentra"))
    .map((i) => {
      const m = i.detail.match(/(R\$\s?[\d.,]+|\d+,\d+%)/g) ?? [];
      return { label: i.title, value: m[0] ?? "—", note: i.detail, bad: true };
    });

  const qa = out.narrative
    ? {
        question: "Por que rendemos menos que o CDI no semestre?",
        answer:
          `A carteira rendeu ${pct(out.returns!.total_return_pct)} contra ${pct(out.benchmark_pct!)} do CDI. A decomposição do motor mostra que a renda fixa acompanhou o CDI, enquanto renda variável e multimercado (${pct(out.narrative.risk_assets_alloc_pct)} da alocação) tiveram semestre abaixo do indexador — comportamento esperado para o horizonte dessas classes. Não há erro de execução: é efeito de alocação.`,
      }
    : {
        question: "Quais são os principais pontos de atenção desta carteira?",
        answer:
          `A carteira soma ${brl(out.total_value)}, com maior concentração em ${topClassLabel} (${topClassPct}). O motor identificou ${out.insights.length} ponto${out.insights.length !== 1 ? "s" : ""} de atenção${nAlta > 0 ? `, sendo ${nAlta} de severidade alta` : ""} — veja a aba Pontos de atenção para o detalhe completo, com origem em cada dado.`,
      };

  const props: WorkspaceProps = {
    family: detail.family,
    dateLabel,
    status: detail.status,
    run: {
      short: detail.run.short,
      engineVersion: detail.run.engine_version ?? "0.2.0-prototype",
      policyVersion: detail.run.policy_version ?? 1,
      asOf: new Date(detail.scheduled_for).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" }),
      drawerSources: hasHistory
        ? "7 valorações mensais (31/12/2025 a 30/06/2026) · 2 fluxos · CDI: BCB/SGS série 12 · posições: extrato confirmado"
        : "Posições: extrato do custodiante confirmado manualmente nesta data — ainda sem série histórica de valorações.",
    },
    kpis,
    resumo,
    mudancas,
    insights: out.insights,
    agenda,
    carteira: groups,
    liquidez: Object.entries(out.liquidity).map(([bucket, l]) => ({
      bucket: LIQ_LABEL[bucket] ?? bucket,
      value: brl(l.value),
      pct: Number(l.pct),
    })),
    concentracoes,
    confMix: [...confCount.entries()].sort().map(([grade, count]) => ({ grade, count })),
    qa,
  };

  return <WorkspaceClient {...props} />;
}
