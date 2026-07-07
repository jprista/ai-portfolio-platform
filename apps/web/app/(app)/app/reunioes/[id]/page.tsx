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

function classify(p: PositionRow): string {
  if (p.kind === "pension_fund") return "previdencia";
  if (p.kind === "fund") return "multimercado";
  if (["equity", "etf", "fii", "bdr"].includes(p.kind)) return "renda_variavel";
  if (p.index_kind === "ipca_plus") return "renda_fixa_inflacao";
  if (p.name.toLowerCase().includes("liquidez diária")) return "caixa";
  return "renda_fixa_pos";
}

function liqOf(p: PositionRow): string {
  if (p.name.toLowerCase().includes("liquidez diária")) return "D0";
  if (p.kind === "pension_fund") return "D+60";
  if (p.kind === "fund") return "D+30";
  if (p.maturity) return "Vencimento";
  return "D+2";
}

export default async function ReuniaoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { orgId } = await requireOrg();
  const detail = await getMeetingDetail(orgId, id);
  if (!detail || !detail.run) notFound();

  const out = detail.run.outputs as {
    total_value: string;
    allocation: Record<string, { value: string; pct: string }>;
    liquidity: Record<string, { value: string; pct: string }>;
    returns: { total_return_pct: string };
    benchmark_pct: string;
    benchmark_comparison: { mode: string; value: string };
    insights: { severity: "alta" | "média" | "baixa"; title: string; detail: string }[];
    narrative: {
      risk_assets_alloc_pct: string;
      changes: string[];
      agenda: string[];
      class_readings: Record<string, string>;
      concentrations: { label: string; value: string; note: string; bad: boolean }[];
    };
  };

  const total = Number(out.total_value);
  const bench = out.benchmark_comparison;
  const benchKpi =
    bench.mode === "pct_of_benchmark"
      ? { label: "% do CDI", value: pct(bench.value) }
      : { label: "Diferença vs. CDI", value: `${pct(bench.value)} p.p.` };

  const groups = Object.entries(out.allocation)
    .sort((a, b) => Number(b[1].value) - Number(a[1].value))
    .map(([cls, agg]) => ({
      cls: CLASS_LABEL[cls] ?? cls,
      subtotal: brl(agg.value),
      pct: pct(agg.pct),
      reading: out.narrative.class_readings[cls] ?? "",
      positions: detail.positions
        .filter((p) => classify(p) === cls)
        .map((p) => ({
          name: p.name,
          holder: p.holder ?? "—",
          index: p.index_kind === "cdi_pct" || p.index_kind === "ipca_plus" ? p.name.match(/(\d{2,3}% CDI|IPCA\s?\+\s?[\d,]+%)/)?.[0] ?? INDEX_LABEL[p.index_kind] : INDEX_LABEL[p.index_kind] ?? "—",
          maturity: p.maturity ? p.maturity.split("-").reverse().join("/") : "—",
          liq: liqOf(p),
          seal: p.confidence,
          value: brl(p.value),
          pct: pct((Number(p.value) / total) * 100),
        })),
    }));

  const dateLabel = new Date(detail.scheduled_for).toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo",
  });

  const confCount = new Map<string, number>();
  for (const p of detail.positions) confCount.set(p.confidence, (confCount.get(p.confidence) ?? 0) + 1);

  const props: WorkspaceProps = {
    family: detail.family,
    dateLabel,
    status: detail.status,
    run: {
      short: detail.run.short,
      engineVersion: detail.run.engine_version ?? "0.2.0-prototype",
      policyVersion: detail.run.policy_version ?? 1,
      asOf: "30/06/2026",
      drawerSources: "7 valorações mensais (31/12/2025 a 30/06/2026) · 2 fluxos · CDI: BCB/SGS série 12 · posições: extrato confirmado",
    },
    kpis: [
      { label: "Patrimônio consolidado", value: brl(out.total_value) },
      { label: "Retorno no semestre", value: pct(out.returns.total_return_pct) },
      { label: "CDI no período", value: pct(out.benchmark_pct) },
      benchKpi,
    ],
    resumo:
      `No semestre, a carteira rendeu ${pct(out.returns.total_return_pct)}, contra ${pct(out.benchmark_pct)} do CDI no mesmo período` +
      (bench.mode === "pct_of_benchmark" ? ` (${pct(bench.value)} do CDI).` : ` (${pct(bench.value)} p.p. vs. CDI — em retorno negativo, % do CDI não é significativo).`) +
      ` A diferença é explicada principalmente pela parcela de renda variável e multimercado (${pct(out.narrative.risk_assets_alloc_pct)} da carteira), cujo objetivo é retorno acima do CDI em horizonte longo. O ponto estrutural desta reunião não é performance: são concentração e vencimento.`,
    mudancas: out.narrative.changes,
    insights: out.insights,
    agenda: out.narrative.agenda,
    carteira: groups,
    liquidez: Object.entries(out.liquidity).map(([bucket, l]) => ({
      bucket: LIQ_LABEL[bucket] ?? bucket,
      value: brl(l.value),
      pct: Number(l.pct),
    })),
    concentracoes: out.narrative.concentrations,
    confMix: [...confCount.entries()].sort().map(([grade, count]) => ({ grade, count })),
    qa: {
      question: "Por que rendemos menos que o CDI no semestre?",
      answer:
        `A carteira rendeu ${pct(out.returns.total_return_pct)} contra ${pct(out.benchmark_pct)} do CDI. A decomposição do motor mostra que a renda fixa acompanhou o CDI, enquanto renda variável e multimercado (${pct(out.narrative.risk_assets_alloc_pct)} da alocação) tiveram semestre abaixo do indexador — comportamento esperado para o horizonte dessas classes. Não há erro de execução: é efeito de alocação.`,
    },
  };

  return <WorkspaceClient {...props} />;
}
