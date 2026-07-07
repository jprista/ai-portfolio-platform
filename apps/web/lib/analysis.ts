import { sql } from "./db";
import type { PositionRow } from "./data";
import { brl, pct } from "./format";

/** Aba Análise: sintetiza o que já existe (posições, alocação, liquidez,
 * insights do motor) em leitura de gestor de patrimônio sênior — diagnóstico,
 * riscos, oportunidades, exposição a juros/inflação, sensibilidade a cenários,
 * contexto macro e cruzamento com o Radar de Consenso. Nunca recomenda um
 * ativo específico: motor calcula, esta camada traduz, o profissional decide
 * (MISSION.md). Todo número aqui é derivado de dados já existentes — nada é
 * inventado pela IA. */

// ---------------------------------------------------------------- macro ----

export type MacroSnapshot = {
  selicMetaPct: string;
  selicAsOf: string;
  ipca12mPct: string;
  ipcaAsOf: string;
  usdBrl: string;
  usdAsOf: string;
};

export async function getMacroSnapshot(): Promise<MacroSnapshot | null> {
  const rows = await sql`
    select selic_meta_pct::text as selic_meta_pct, selic_as_of::text as selic_as_of,
           ipca_12m_pct::text as ipca_12m_pct, ipca_as_of::text as ipca_as_of,
           usd_brl::text as usd_brl, usd_as_of::text as usd_as_of
    from market.macro_snapshot
    order by captured_at desc
    limit 1
  `;
  if (!rows.length) return null;
  const r = rows[0];
  return {
    selicMetaPct: r.selic_meta_pct,
    selicAsOf: r.selic_as_of,
    ipca12mPct: r.ipca_12m_pct,
    ipcaAsOf: r.ipca_as_of,
    usdBrl: r.usd_brl,
    usdAsOf: r.usd_as_of,
  };
}

// ------------------------------------------------------------ consenso -----

export type ConsensusHolder = { manager: string; rank: number; changeKind: string | null };
export type ConsensusMatch = { ticker: string; positionName: string; holders: ConsensusHolder[] };
export type ConsensusIdea = { ticker: string; issuerName: string; holders: ConsensusHolder[] };

function extractTicker(name: string): string | null {
  const m = name.match(/^([A-Z]{4}\d{1,2})\b/);
  return m ? m[1] : null;
}

export async function getRadarCrossref(positions: PositionRow[]): Promise<{
  convergence: ConsensusMatch[];
  ideas: ConsensusIdea[];
  trackedManagers: number;
}> {
  const equityLike = positions.filter((p) => ["equity", "etf", "fii", "bdr"].includes(p.kind));
  const familyTickers = new Map<string, PositionRow>();
  for (const p of equityLike) {
    const t = extractTicker(p.name);
    if (t) familyTickers.set(t, p);
  }

  const rows = await sql`
    select mg.name as manager, mh.rank, mh.instrument, mh.issuer_name, mh.change_kind
    from market.managers mg
    join lateral (
      select * from market.manager_filings f where f.manager_id = mg.id
      order by f.period_end desc limit 1
    ) mf on true
    join market.manager_holdings mh on mh.filing_id = mf.id
    where mg.jurisdiction = 'BR' and mh.instrument is not null
  `;

  const byTicker = new Map<string, { issuerName: string; holders: ConsensusHolder[] }>();
  const managerNames = new Set<string>();
  for (const r of rows) {
    managerNames.add(r.manager);
    const entry = byTicker.get(r.instrument) ?? { issuerName: r.issuer_name, holders: [] as ConsensusHolder[] };
    entry.holders.push({ manager: r.manager, rank: r.rank, changeKind: r.change_kind });
    byTicker.set(r.instrument, entry);
  }

  const convergence: ConsensusMatch[] = [];
  for (const [ticker, pos] of familyTickers) {
    const entry = byTicker.get(ticker);
    if (entry) {
      convergence.push({
        ticker,
        positionName: pos.name,
        holders: entry.holders.sort((a, b) => a.rank - b.rank),
      });
    }
  }
  convergence.sort((a, b) => b.holders.length - a.holders.length);

  const ideas: ConsensusIdea[] = [];
  for (const [ticker, entry] of byTicker) {
    if (familyTickers.has(ticker)) continue;
    if (entry.holders.length < 2) continue;
    ideas.push({ ticker, issuerName: entry.issuerName.replace(/\s{2,}/g, " ").trim(), holders: entry.holders.sort((a, b) => a.rank - b.rank) });
  }
  ideas.sort((a, b) => b.holders.length - a.holders.length || a.holders[0].rank - b.holders[0].rank);

  return { convergence, ideas: ideas.slice(0, 5), trackedManagers: managerNames.size };
}

// -------------------------------------------------------- classificação ----

const PRIVATE_CREDIT_KINDS = new Set(["cdb", "lci", "lca", "lc", "debenture", "coe"]);

type Bucket = "posFixado" | "prefixado" | "inflacao" | "rendaVariavel" | "fii" | "multimercado" | "caixa" | "outros";

const BUCKET_LABEL: Record<Bucket, string> = {
  posFixado: "Pós-fixado (CDI/Selic)",
  prefixado: "Prefixado",
  inflacao: "Inflação (IPCA+)",
  rendaVariavel: "Renda variável (ações/BDR/ETF)",
  fii: "Fundos imobiliários",
  multimercado: "Multimercado / alternativos",
  caixa: "Caixa",
  outros: "Não classificado",
};

function bucketOf(p: PositionRow): Bucket {
  if (p.name.toLowerCase().includes("liquidez diária") || p.kind === "cash") return "caixa";
  if (p.kind === "equity" || p.kind === "etf" || p.kind === "bdr") return "rendaVariavel";
  if (p.kind === "fii") return "fii";
  if (p.index_kind === "cdi_pct" || p.index_kind === "selic") return "posFixado";
  if (p.index_kind === "pre") return "prefixado";
  if (p.index_kind === "ipca_plus") return "inflacao";
  if (p.kind === "fund" || p.kind === "pension_fund") return "multimercado";
  return "outros";
}

// ------------------------------------------------------------ cenários -----

type ScenarioKey = "juros_alta" | "juros_queda" | "inflacao_surpresa" | "dolar_alta" | "bolsa_queda";

// Multimercado é deliberadamente OMITIDO como driver de juros/dólar: é uma
// "caixa-preta" (o motor não sabe o que o fundo carrega por baixo), então
// atribuir convicção direcional a ele nesses cenários seria inventar certeza
// que não existe. A única leitura defensável para multimercado é a genérica
// (beta a risco em estresse de bolsa), mantida só em bolsa_queda.
const SCENARIOS: { key: ScenarioKey; label: string; coef: Partial<Record<Bucket, number>> }[] = [
  { key: "juros_alta", label: "Alta de juros (Selic)", coef: { posFixado: 1, prefixado: -1, inflacao: -0.3, rendaVariavel: -0.3, fii: -0.4, caixa: 0.5 } },
  { key: "juros_queda", label: "Queda de juros (Selic)", coef: { posFixado: -0.4, prefixado: 1, inflacao: 0.2, rendaVariavel: 0.4, fii: 0.5, caixa: -0.3 } },
  { key: "inflacao_surpresa", label: "Inflação acima do esperado", coef: { posFixado: 0.1, prefixado: -0.6, inflacao: 1, rendaVariavel: -0.1, fii: 0.2, caixa: -0.2 } },
  { key: "dolar_alta", label: "Alta do dólar", coef: { prefixado: -0.2, inflacao: 0.1, rendaVariavel: 0.1 } },
  { key: "bolsa_queda", label: "Queda de bolsa (~15%)", coef: { rendaVariavel: -1, fii: -0.3, multimercado: -0.4 } },
];

// banda larga de propósito: só rotula uma direção quando um driver é
// claramente dominante na composição — o padrão é "neutro/misto", que é a
// resposta honesta quando a carteira não dá base para uma leitura confiante.
function impactLabel(score: number): "favoravel" | "neutro" | "desfavoravel" {
  if (score > 0.12) return "favoravel";
  if (score < -0.12) return "desfavoravel";
  return "neutro";
}

// -------------------------------------------------------------- output -----

export type AnalysisData = {
  diagnosis: string;
  risks: { title: string; detail: string; severity: "alta" | "média" | "baixa" }[];
  opportunities: { title: string; detail: string }[];
  exposure: { bucket: string; pct: string; value: string }[];
  scenarios: { label: string; impact: "favoravel" | "neutro" | "desfavoravel"; reading: string }[];
  macro: { selic: string; ipca: string; usd: string; asOf: string; reading: string } | null;
  consensus: {
    trackedManagers: number;
    convergence: { ticker: string; positionName: string; holders: ConsensusHolder[] }[];
    ideas: ConsensusIdea[];
    globalNote: string;
  };
  recommendations: string[];
};

export function buildAnalysis(args: {
  positions: PositionRow[];
  totalValue: string;
  hasHistory: boolean;
  returnPct?: string;
  benchmarkMode?: string;
  benchmarkValue?: string;
  macro: MacroSnapshot | null;
  crossref: { convergence: ConsensusMatch[]; ideas: ConsensusIdea[]; trackedManagers: number };
}): AnalysisData {
  const { positions, macro, crossref } = args;
  const total = Number(args.totalValue) || 1;

  const sums = new Map<Bucket, number>();
  for (const p of positions) {
    const b = bucketOf(p);
    sums.set(b, (sums.get(b) ?? 0) + Number(p.value));
  }
  const bucketPct = (b: Bucket) => ((sums.get(b) ?? 0) / total) * 100;

  const exposure = (Object.keys(BUCKET_LABEL) as Bucket[])
    .filter((b) => (sums.get(b) ?? 0) > 0)
    .sort((a, b) => (sums.get(b) ?? 0) - (sums.get(a) ?? 0))
    .map((b) => ({ bucket: BUCKET_LABEL[b], pct: pct(bucketPct(b)), value: brl(sums.get(b) ?? 0) }));

  // --------------------------------------------------------------- riscos
  const risks: AnalysisData["risks"] = [];

  const equities = positions.filter((p) => p.kind === "equity");
  const equityTotal = equities.reduce((acc, p) => acc + Number(p.value), 0);
  if (equities.length >= 2 && equityTotal > 0) {
    const top = [...equities].sort((a, b) => Number(b.value) - Number(a.value))[0];
    const topShare = Number(top.value) / equityTotal;
    if (topShare > 0.35) {
      risks.push({
        severity: topShare > 0.5 ? "alta" : "média",
        title: "Concentração dentro da carteira de ações",
        detail: `${top.name} responde por ${pct(topShare * 100)} da parcela em ações — mais que o dobro de uma posição bem diversificada dentro dessa classe. Não é o mesmo alerta de concentração por emissor do motor (que olha a carteira toda); aqui o ponto é que a própria fatia de renda variável está pouco pulverizada.`,
      });
    }
  }

  const creditPositions = positions.filter((p) => PRIVATE_CREDIT_KINDS.has(p.kind));
  const creditTotal = creditPositions.reduce((acc, p) => acc + Number(p.value), 0);
  if (creditPositions.length >= 2 && creditTotal > 0) {
    const byIssuer = new Map<string, number>();
    for (const p of creditPositions) byIssuer.set(p.issuer, (byIssuer.get(p.issuer) ?? 0) + Number(p.value));
    const [issuer, value] = [...byIssuer.entries()].sort((a, b) => b[1] - a[1])[0];
    const share = value / creditTotal;
    if (share > 0.4) {
      risks.push({
        severity: "média",
        title: "Dependência de poucos emissores de crédito privado",
        detail: `${issuer} concentra ${pct(share * 100)} do crédito privado da carteira (CDB/LCI/LCA/debêntures) — risco de crédito pouco diluído dentro dessa fatia, independente do risco soberano do Tesouro.`,
      });
    }
  }

  const riskAssetsPct = bucketPct("rendaVariavel") + bucketPct("fii") + bucketPct("multimercado");
  if (riskAssetsPct > 35) {
    risks.push({
      severity: riskAssetsPct > 55 ? "alta" : "média",
      title: "Classes de risco correlacionadas em cenário de estresse",
      detail: `Renda variável, FIIs e multimercado somam ${pct(riskAssetsPct)} da carteira. Em choques de mercado essas classes tendem a cair juntas — a diversificação entre elas reduz volatilidade no dia a dia, mas não protege tanto quanto parece num evento de estresse simultâneo.`,
    });
  }

  const inflacaoPct = bucketPct("inflacao");
  if (inflacaoPct < 5 && bucketPct("posFixado") > 40) {
    risks.push({
      severity: "baixa",
      title: "Baixa proteção explícita contra inflação",
      detail: `Apenas ${pct(inflacaoPct)} da carteira está indexada ao IPCA, contra ${pct(bucketPct("posFixado"))} em pós-fixado. O pós-fixado acompanha a Selic, não a inflação diretamente — em ciclos de corte de juros com inflação resiliente, essa parcela perde poder de compra relativo.`,
    });
  }

  // --------------------------------------------------------- oportunidades
  const opportunities: AnalysisData["opportunities"] = [];

  if (bucketPct("caixa") > 12) {
    opportunities.push({
      title: "Caixa acima do usual parado em liquidez imediata",
      detail: `${pct(bucketPct("caixa"))} da carteira está em liquidez D0. Vale confirmar com o cliente se há necessidade de curto prazo que justifique esse nível — caso não haja, é caixa que hoje rende CDI mas poderia estar alocado com um horizonte um pouco mais longo.`,
    });
  }

  const hasForeignExposure = positions.some((p) => p.kind === "bdr");
  if (!hasForeignExposure && total > 0) {
    opportunities.push({
      title: "Nenhuma exposição em moeda estrangeira",
      detail: "A carteira não tem BDRs, ETFs internacionais ou fundos com mandato global — 100% do risco é doméstico (Brasil e real). Não é necessariamente um problema, mas é uma decisão implícita que vale tornar explícita com o cliente: ele está confortável em concentrar todo o risco no ciclo econômico brasileiro?",
    });
  }

  if (args.hasHistory && args.returnPct && args.benchmarkValue) {
    const under = args.benchmarkMode === "pct_of_benchmark" ? Number(args.benchmarkValue) < 100 : Number(args.benchmarkValue) < 0;
    if (under) {
      opportunities.push({
        title: "Momento natural para revisitar a tese da parcela de risco",
        detail: "O período abaixo do CDI não é, por si só, um erro — mas é um bom gatilho de calendário para reconfirmar com o cliente se a tese original de cada fundo/posição de risco ainda se sustenta, em vez de deixar por inércia.",
      });
    }
  }

  const increasingConvergence = crossref.convergence.filter((c) => c.holders.some((h) => h.changeKind === "increased"));
  if (increasingConvergence.length > 0) {
    const c = increasingConvergence[0];
    opportunities.push({
      title: "Convergência crescente com gestoras acompanhadas",
      detail: `${c.positionName} é uma posição que ${c.holders.length} das gestoras do Radar de Consenso também carregam, e ao menos uma delas aumentou a posição no último trimestre — sinal de que o mercado profissional segue confortável com o papel.`,
    });
  }

  // ------------------------------------------------------------- cenários
  const scenarios = SCENARIOS.map((s) => {
    let score = 0;
    let driverBucket: Bucket | null = null;
    let driverAbs = 0;
    for (const [bucket, coef] of Object.entries(s.coef) as [Bucket, number][]) {
      const contribution = (bucketPct(bucket) / 100) * coef;
      score += contribution;
      if (Math.abs(contribution) > driverAbs) {
        driverAbs = Math.abs(contribution);
        driverBucket = bucket;
      }
    }
    const impact = impactLabel(score);
    const driverLabel = driverBucket ? BUCKET_LABEL[driverBucket] : "composição atual";
    const reading =
      impact === "favoravel"
        ? `Tende a favorecer a carteira, puxado principalmente por ${driverLabel.toLowerCase()}.`
        : impact === "desfavoravel"
          ? `Tende a pressionar a carteira, principalmente via ${driverLabel.toLowerCase()}.`
          : `Efeito líquido pequeno — ganhos e perdas entre classes se compensam parcialmente.`;
    return { label: s.label, impact, reading };
  });

  // ---------------------------------------------------------------- macro
  let macroOut: AnalysisData["macro"] = null;
  if (macro) {
    const realRate = Number(macro.selicMetaPct) - Number(macro.ipca12mPct);
    macroOut = {
      selic: pct(macro.selicMetaPct),
      ipca: pct(macro.ipca12mPct),
      usd: `R$ ${Number(macro.usdBrl).toFixed(2).replace(".", ",")}`,
      asOf: macro.selicAsOf,
      reading:
        `Selic em ${pct(macro.selicMetaPct)} e IPCA em ${pct(macro.ipca12mPct)} nos últimos 12 meses colocam o país em juro real de aproximadamente ${realRate.toFixed(1).replace(".", ",")} p.p. — regime historicamente favorável ao pós-fixado (${pct(bucketPct("posFixado"))} desta carteira). ` +
        (bucketPct("prefixado") > 0
          ? `A parcela prefixada (${pct(bucketPct("prefixado"))}) é a mais sensível a um eventual ciclo de alta adicional de juros. `
          : "") +
        `O câmbio em torno de ${`R$ ${Number(macro.usdBrl).toFixed(2).replace(".", ",")}`}/US$ reforça que, sem exposição cambial na carteira, toda a proteção contra um real mais fraco depende de decisões futuras, não da composição atual.`,
    };
  }

  // ------------------------------------------------------------ consenso
  const globalNote =
    "As gestoras globais acompanhadas (Berkshire, Bridgewater, Pershing Square, Duquesne, Scion) reportam via SEC 13F, que cobre apenas ações listadas nos EUA — não há sobreposição direta de papéis com uma carteira 100% doméstica. Ausência de match aqui não é um sinal negativo, só reflete o universo de ativos coberto pela fonte.";

  // -------------------------------------------------------- diagnóstico
  const goodParts: string[] = [];
  const badParts: string[] = [];
  if (crossref.convergence.length > 0) {
    goodParts.push(`${crossref.convergence.length} posiç${crossref.convergence.length > 1 ? "ões convergem" : "ão converge"} com o que as maiores gestoras brasileiras acompanhadas no Radar também carregam`);
  }
  if (bucketPct("posFixado") > 30) goodParts.push(`parcela relevante em pós-fixado (${pct(bucketPct("posFixado"))}) bem posicionada para o juro real atual`);
  if (risks.length === 0) goodParts.push("nenhum risco estrutural de concentração ou correlação identificado nesta leitura");

  if (risks.some((r) => r.severity === "alta")) badParts.push("há ao menos um ponto de concentração de severidade alta que merece prioridade");
  if (riskAssetsPct > 35) badParts.push(`${pct(riskAssetsPct)} da carteira está em classes que tendem a cair juntas num estresse de mercado`);
  if (opportunities.some((o) => o.title.includes("estrangeira"))) badParts.push("toda a carteira está exposta ao ciclo doméstico, sem diversificação cambial");

  const diagnosis =
    `${goodParts.length > 0 ? `O que está bom: ${goodParts.join("; ")}. ` : ""}` +
    `${badParts.length > 0 ? `O que pede atenção: ${badParts.join("; ")}. ` : "Não há pontos de atenção estruturais nesta leitura — o trabalho agora é de manutenção, não de correção. "}` +
    `Próximo passo natural: ${risks.length > 0 ? "tratar primeiro " + risks[0].title.toLowerCase() : "revisar com o cliente se a composição atual ainda reflete os objetivos e o horizonte declarados"}.`;

  // ------------------------------------------------------- recomendações
  const recommendations: string[] = [];
  if (risks.length > 0) recommendations.push(`Priorizar na pauta: ${risks[0].title.toLowerCase()}.`);
  if (opportunities.length > 0) recommendations.push(opportunities[0].title + " — vale uma conversa dedicada com o cliente.");
  if (crossref.ideas.length > 0) {
    const idea = crossref.ideas[0];
    recommendations.push(
      `${idea.issuerName} (${idea.ticker}) está entre as posições mais recorrentes no Radar de Consenso (${idea.holders.length} gestoras acompanhadas) e não está na carteira do cliente — não é uma recomendação de compra, mas um tema com evidência suficiente para entrar na discussão.`,
    );
  }
  if (macroOut) recommendations.push("Usar o contexto macro atual (juro real elevado) para validar se o mix pós-fixado/prefixado/inflação ainda reflete a visão da casa para os próximos meses.");
  recommendations.push("Registrar na ata da reunião qual destes pontos o cliente decidiu agir e qual decidiu conscientemente manter — isso também é uma decisão, e fica auditável.");

  return {
    diagnosis,
    risks,
    opportunities,
    exposure,
    scenarios,
    macro: macroOut,
    consensus: {
      trackedManagers: crossref.trackedManagers,
      convergence: crossref.convergence,
      ideas: crossref.ideas,
      globalNote,
    },
    recommendations,
  };
}
