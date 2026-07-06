"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, InsightCard, Seal, SectionTitle } from "@/components/ui";

const kpis = [
  { label: "Patrimônio consolidado", value: "R$ 2.913.933,80", prov: true },
  { label: "Retorno no semestre", value: "5,20%", prov: true },
  { label: "CDI no período", value: "6,84%", prov: true },
  { label: "% do CDI", value: "76,01%", prov: true },
];

const journey = ["Agendada", "Em preparação", "Material gerado", "Material enviado", "Realizada"];

const insights: { severity: "alta" | "média" | "baixa"; title: string; body: React.ReactNode }[] = [
  {
    severity: "alta",
    title: "Acima do FGC: José Almeida em Banco Beta",
    body: <>O titular possui <Num>R$ 562.350,75</Num> em instrumentos de crédito do emissor — R$ 312.350,75 acima do teto de cobertura do FGC (R$ 250.000,00 por CPF/CNPJ por emissor).</>,
  },
  {
    severity: "alta",
    title: "Acima do FGC: Maria Almeida em Banco Delta",
    body: <>R$ 262.110,45 em CDB IPCA+ — R$ 12.110,45 acima do teto. Estouro pequeno e invisível na visão agregada da família; detectado pelo cálculo por titular.</>,
  },
  {
    severity: "alta",
    title: "Concentração da família em Banco Beta",
    body: <>Na visão consolidada, o emissor responde por <Num>19,30%</Num> da carteira (limite da política: 15%).</>,
  },
  {
    severity: "média",
    title: "Vencimento em 46 dias: LCA 93% CDI — Banco Gama",
    body: <>R$ 121.480,30 vencem em 15/08/2026. Definir destino evita dias parados em caixa.</>,
  },
  {
    severity: "média",
    title: "Taxa acima da mediana: FIM Órion Multiestratégia",
    body: <>1,90% a.a. contra mediana de 1,50% da classe. Impacto anual estimado: R$ 1.795,04.</>,
  },
  {
    severity: "baixa",
    title: "Dado com confiança C: Previdência VGBL — FIE Zafira",
    body: <>Selo de confiança C (documento parseado, não reconciliado). Atualizar a fonte antes da reunião.</>,
  },
];

const agenda = [
  "Exposições acima do FGC por titular (2 casos)",
  "Concentração da família em Banco Beta",
  "Destino da LCA que vence em 15/08",
  "Custo do FIM Órion vs. mediana da classe",
  "Objetivos e horizonte das parcelas de risco",
];

type Pos = {
  name: string;
  holder: string;
  index: string;
  maturity: string;
  liq: string;
  seal: string;
  value: string;
  pct: string;
};

const carteira: {
  cls: string;
  subtotal: string;
  pct: string;
  reading: string;
  positions: Pos[];
}[] = [
  {
    cls: "Renda fixa pós-fixada",
    subtotal: "R$ 839.711,70",
    pct: "28,82%",
    reading:
      "Carrego médio ponderado de ≈104% do CDI. A LCA Banco Gama vence em 46 dias — decidir destino nesta reunião evita recurso parado.",
    positions: [
      { name: "CDB 110% CDI — Banco Beta", holder: "José", index: "110% CDI", maturity: "20/08/2027", liq: "Vencimento", seal: "A", value: "R$ 412.350,75", pct: "14,15%" },
      { name: "Tesouro Selic 2029", holder: "Maria", index: "SELIC", maturity: "—", liq: "D+2", seal: "A", value: "R$ 305.880,65", pct: "10,50%" },
      { name: "LCA 93% CDI — Banco Gama", holder: "Maria", index: "93% CDI", maturity: "15/08/2026", liq: "Vencimento", seal: "A", value: "R$ 121.480,30", pct: "4,17%" },
    ],
  },
  {
    cls: "Renda variável",
    subtotal: "R$ 725.571,35",
    pct: "24,90%",
    reading:
      "Quatro veículos, maior posição no FIA Vértice (8,63% da carteira). Semestre abaixo do CDI — comportamento esperado do horizonte da classe, não erro de execução.",
    positions: [
      { name: "FIA Vértice Ações", holder: "Maria", index: "—", maturity: "—", liq: "D+30", seal: "A", value: "R$ 251.340,55", pct: "8,63%" },
      { name: "BOVA11 — ETF Ibovespa", holder: "José", index: "—", maturity: "—", liq: "D+2", seal: "A", value: "R$ 180.250,00", pct: "6,19%" },
      { name: "HGLG11 — FII CSHG Logística", holder: "Maria", index: "—", maturity: "—", liq: "D+2", seal: "A", value: "R$ 151.200,80", pct: "5,19%" },
      { name: "ITUB4 — Itaú Unibanco PN", holder: "José", index: "—", maturity: "—", liq: "D+2", seal: "A", value: "R$ 142.780,00", pct: "4,90%" },
    ],
  },
  {
    cls: "Renda fixa inflação",
    subtotal: "R$ 646.330,55",
    pct: "22,18%",
    reading:
      "Proteção real de longo prazo com vencimentos 2028 e 2035. CDB Banco Delta responde pelo estouro de FGC da titular Maria (R$ 12.110,45 acima do teto).",
    positions: [
      { name: "Tesouro IPCA+ 2035", holder: "José", index: "IPCA + mercado", maturity: "15/05/2035", liq: "D+2", seal: "A", value: "R$ 384.220,10", pct: "13,19%" },
      { name: "CDB IPCA+ 6,20% — Banco Delta", holder: "Maria", index: "IPCA + 6,20%", maturity: "10/05/2028", liq: "Vencimento", seal: "B", value: "R$ 262.110,45", pct: "9,00%" },
    ],
  },
  {
    cls: "Multimercado",
    subtotal: "R$ 448.760,20",
    pct: "15,40%",
    reading:
      "Taxa de administração de 1,90% a.a. contra mediana de 1,50% da classe — impacto anual estimado de R$ 1.795,04. Item de custo na pauta.",
    positions: [
      { name: "FIM Órion Multiestratégia", holder: "José", index: "—", maturity: "—", liq: "D+30", seal: "A", value: "R$ 448.760,20", pct: "15,40%" },
    ],
  },
  {
    cls: "Caixa e liquidez",
    subtotal: "R$ 150.000,00",
    pct: "5,15%",
    reading:
      "Liquidez imediata concentrada no mesmo emissor do maior CDB (Banco Beta) — contribui para a concentração de 19,30% da família no emissor.",
    positions: [
      { name: "CDB liquidez diária 100% CDI — Banco Beta", holder: "José", index: "100% CDI", maturity: "—", liq: "D0", seal: "A", value: "R$ 150.000,00", pct: "5,15%" },
    ],
  },
  {
    cls: "Previdência",
    subtotal: "R$ 103.560,00",
    pct: "3,55%",
    reading:
      "Fonte com selo C (extrato parseado, não reconciliado) — atualizar antes da reunião para restaurar a confiança do dado.",
    positions: [
      { name: "Previdência VGBL — FIE Zafira", holder: "Maria", index: "—", maturity: "—", liq: "D+60", seal: "C", value: "R$ 103.560,00", pct: "3,55%" },
    ],
  },
];

const liquidez = [
  { bucket: "D0 — imediata", value: "R$ 150.000,00", pct: 5.15 },
  { bucket: "Até 30 dias", value: "R$ 1.864.432,30", pct: 63.98 },
  { bucket: "31 a 360 dias", value: "R$ 225.040,30", pct: 7.72 },
  { bucket: "Acima de 360 dias", value: "R$ 674.461,20", pct: 23.15 },
];

const concentracoes = [
  { label: "Banco Beta (família)", value: "19,30%", note: "limite da política: 15%", bad: true },
  { label: "José em Banco Beta (FGC)", value: "R$ 562.350,75", note: "R$ 312.350,75 acima do teto", bad: true },
  { label: "Maria em Banco Delta (FGC)", value: "R$ 262.110,45", note: "R$ 12.110,45 acima do teto", bad: true },
  { label: "Banco Gama (família)", value: "4,17%", note: "dentro da política", bad: false },
];

let openDrawerFn: (() => void) | null = null;

function Num({ children }: { children: React.ReactNode }) {
  return (
    <button
      onClick={() => openDrawerFn?.()}
      className="tnum cursor-pointer rounded-sm border-b border-dashed border-gold/70 font-medium text-navy transition-colors hover:bg-gold-soft"
      title="Ver proveniência deste número"
    >
      {children}
    </button>
  );
}

export default function WorkspaceReuniao() {
  const [drawer, setDrawer] = useState(false);
  const [tab, setTab] = useState<"briefing" | "atencao" | "carteira">("briefing");
  openDrawerFn = () => setDrawer(true);

  return (
    <div className="mx-auto max-w-[1240px] px-10 py-9">
      <nav className="mb-2 text-[12px] text-muted">
        <Link href="/" className="hover:underline">Mesa de Reuniões</Link>
        <span className="mx-1.5 text-faint">/</span>
        Família Almeida
        <span className="mx-1.5 text-faint">/</span>
        Revisão trimestral
      </nav>

      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-[26px] tracking-tight text-navy">
            Família Almeida — Revisão trimestral
          </h1>
          <p className="mt-1 text-[13px] text-muted">quinta-feira, 9 de julho de 2026 · 10:00</p>
        </div>
        <button className="rounded-xl bg-navy px-4 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep">
          Gerar material do cliente
        </button>
      </header>

      {/* jornada de estados */}
      <div className="mb-7 flex items-center gap-2">
        {journey.map((step, i) => (
          <div key={step} className="flex items-center gap-2">
            <span
              className={`rounded-full px-3 py-1.5 text-[11.5px] font-medium ${
                i === 0
                  ? "bg-ok-soft text-ok"
                  : i === 1
                    ? "bg-navy text-white shadow-card"
                    : "bg-surface text-faint ring-1 ring-hairline"
              }`}
            >
              {i === 0 ? "✓ " : ""}{step}
            </span>
            {i < journey.length - 1 && <span className="h-px w-4 bg-hairline" />}
          </div>
        ))}
      </div>

      {/* KPIs */}
      <div className="mb-8 grid grid-cols-4 gap-4">
        {kpis.map((k) => (
          <Card key={k.label} className="p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-faint">{k.label}</div>
            <div className="mt-1.5">
              <Num>{k.value}</Num>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex items-start gap-8">
        <section className="min-w-0 flex-[1.9]">
          {/* abas */}
          <div className="mb-4 flex gap-1 border-b border-hairline">
            {[
              { id: "briefing" as const, label: "Briefing" },
              { id: "carteira" as const, label: "Carteira" },
              { id: "atencao" as const, label: "Pontos de atenção (6)" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`-mb-px border-b-2 px-4 py-2.5 text-[13.5px] transition-colors ${
                  tab === t.id
                    ? "border-gold font-semibold text-navy"
                    : "border-transparent text-muted hover:text-navy"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "briefing" ? (
            <Card className="p-6 text-[14px] leading-[1.75] text-ink/90">
              <p>
                <strong className="text-navy">Resumo executivo.</strong> No semestre, a carteira rendeu{" "}
                <Num>5,20%</Num>, contra <Num>6,84%</Num> do CDI no mesmo período (<Num>76,01% do CDI</Num>).
                A diferença é explicada principalmente pela parcela de renda variável e multimercado
                (<Num>40,30%</Num> da carteira), cujo objetivo é retorno acima do CDI em horizonte longo —
                não no semestre. O ponto estrutural que merece decisão nesta reunião não é performance:
                são os itens de concentração e vencimento ao lado.
              </p>
              <p className="mt-4">
                <strong className="text-navy">O que mudou desde a última reunião (31/03/2026).</strong>{" "}
                Patrimônio passou de <Num>R$ 2.883.450,00</Num> para <Num>R$ 2.913.933,80</Num>; retorno de{" "}
                <Num>2,11%</Num> no período; resgate de <Num>R$ 30.000,00</Num> em 10/05/2026.
              </p>
              <p className="mt-4 border-t border-hairline pt-3 text-[11.5px] text-faint">
                Narrativa gerada do run <code className="rounded bg-paper px-1.5 py-0.5">85fd25b3</code> ·
                verificador de proveniência: aprovado · todos os números são clicáveis
              </p>
            </Card>
          ) : tab === "atencao" ? (
            <div className="flex flex-col gap-3">
              {insights.map((ins) => (
                <InsightCard key={ins.title} severity={ins.severity} title={ins.title}>
                  {ins.body}
                </InsightCard>
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {/* posições por classe, com leitura analítica */}
              {carteira.map((g) => (
                <Card key={g.cls} className="overflow-hidden">
                  <div className="flex items-baseline justify-between border-b border-hairline bg-paper/60 px-5 py-3">
                    <div className="flex items-baseline gap-3">
                      <span className="font-display text-[15px] text-navy">{g.cls}</span>
                      <span className="text-[12px] text-muted">{g.positions.length} {g.positions.length > 1 ? "posições" : "posição"}</span>
                    </div>
                    <div className="flex items-baseline gap-3">
                      <span className="tnum text-[13.5px] font-semibold text-navy">{g.subtotal}</span>
                      <span className="tnum rounded-full bg-navy-soft px-2 py-0.5 text-[11px] font-semibold text-navy">{g.pct}</span>
                    </div>
                  </div>
                  <table className="w-full text-[12.5px]">
                    <thead>
                      <tr className="text-left text-[10.5px] font-semibold uppercase tracking-wider text-faint">
                        <th className="px-5 py-2.5 font-semibold">Ativo</th>
                        <th className="py-2.5 font-semibold">Titular</th>
                        <th className="py-2.5 font-semibold">Indexador</th>
                        <th className="py-2.5 font-semibold">Vencimento</th>
                        <th className="py-2.5 font-semibold">Liquidez</th>
                        <th className="py-2.5 text-center font-semibold">Selo</th>
                        <th className="py-2.5 pr-5 text-right font-semibold">Valor · %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-hairline">
                      {g.positions.map((p) => (
                        <tr key={p.name} className="transition-colors hover:bg-paper/50">
                          <td className="px-5 py-2.5 font-medium text-ink">{p.name}</td>
                          <td className="py-2.5 text-muted">{p.holder}</td>
                          <td className="py-2.5 text-muted">{p.index}</td>
                          <td className="py-2.5 text-muted">{p.maturity}</td>
                          <td className="py-2.5 text-muted">{p.liq}</td>
                          <td className="py-2.5 text-center"><Seal grade={p.seal} /></td>
                          <td className="py-2.5 pr-5 text-right">
                            <Num>{p.value}</Num>
                            <span className="tnum ml-2 text-[11px] text-faint">{p.pct}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="border-t border-hairline bg-gold-soft/40 px-5 py-2.5 text-[12px] leading-relaxed text-ink/75">
                    <span className="font-semibold text-gold">Leitura do motor · </span>
                    {g.reading}
                  </p>
                </Card>
              ))}

              {/* liquidez e concentrações */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-5">
                  <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-faint">Escada de liquidez</div>
                  <div className="space-y-3">
                    {liquidez.map((l) => (
                      <div key={l.bucket}>
                        <div className="mb-1 flex items-baseline justify-between text-[12px]">
                          <span className="text-ink/80">{l.bucket}</span>
                          <span className="tnum text-muted">{l.value} · {l.pct.toFixed(2).replace(".", ",")}%</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-paper">
                          <div className="h-full rounded-full bg-navy/80" style={{ width: `${l.pct}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
                <Card className="p-5">
                  <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-faint">Concentrações e FGC</div>
                  <div className="divide-y divide-hairline">
                    {concentracoes.map((c) => (
                      <div key={c.label} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0">
                        <div>
                          <div className="text-[12.5px] font-medium text-ink">{c.label}</div>
                          <div className={`text-[11px] ${c.bad ? "text-bad" : "text-ok"}`}>{c.note}</div>
                        </div>
                        <span className={`tnum text-[13px] font-semibold ${c.bad ? "text-bad" : "text-navy"}`}>{c.value}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* Q&A dock */}
          <Card className="mt-6 p-4">
            <div className="flex gap-2.5">
              <input
                defaultValue="Por que rendemos menos que o CDI no semestre?"
                placeholder="Pergunte sobre a carteira…"
                className="flex-1 rounded-xl border border-hairline bg-paper px-4 py-2.5 text-[13px] outline-none transition-shadow focus:ring-2 focus:ring-gold/40"
              />
              <button className="rounded-xl bg-navy px-4 py-2 text-[13px] font-medium text-white transition-colors hover:bg-navy-deep">
                Perguntar
              </button>
            </div>
            <div className="mt-3 rounded-xl bg-paper p-4 text-[13px] leading-relaxed text-ink/85">
              A carteira rendeu <Num>5,20%</Num> contra 6,84% do CDI. A decomposição do motor mostra que a
              renda fixa acompanhou o CDI, enquanto renda variável e multimercado (40,30% da alocação)
              tiveram semestre abaixo do indexador — comportamento esperado para o horizonte dessas
              classes. Não há erro de execução: é efeito de alocação, alinhado à política da família.
              <div className="mt-2.5 flex items-center justify-between text-[11px] text-faint">
                <span>
                  Fundamentado no run <code className="rounded bg-surface px-1 py-0.5">85fd25b3</code> ·
                  verificador: aprovado
                </span>
                <span className="cursor-help" title="Interações com a IA são registradas na trilha de auditoria, conforme os termos de uso e a política de retenção da sua organização.">
                  ⛨ registrado
                </span>
              </div>
            </div>
          </Card>
        </section>

        <aside className={`w-[340px] shrink-0 ${tab === "carteira" ? "hidden" : ""}`}>
          <SectionTitle>Material da reunião</SectionTitle>
          <Card className="p-4">
            <div className="text-[13px] font-semibold text-navy">Briefing interno — v1</div>
            <div className="mt-1 text-[11.5px] leading-relaxed text-muted">
              Gerado hoje às 15:37 por João Pedro
              <br />
              run <code className="rounded bg-paper px-1 py-0.5">85fd25b3152c43ab</code> · motor v0.2.0 · política v1
            </div>
          </Card>
          <Card className="mt-3 border-dashed p-4">
            <div className="text-[13px] font-semibold text-muted">Relatório do cliente</div>
            <div className="mt-1 text-[11.5px] leading-relaxed text-muted">
              Será produzido com a marca do escritório a partir do run atual. Após o envio, o material é{" "}
              <b>congelado</b>; alterações criam nova versão, preservando as anteriores.
            </div>
          </Card>

          <div className="mt-6">
            <SectionTitle>Pauta sugerida</SectionTitle>
            <Card className="p-4">
              <ol className="list-decimal space-y-2 pl-4 text-[12.5px] leading-relaxed text-ink/85 marker:font-semibold marker:text-gold">
                {agenda.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ol>
            </Card>
          </div>

          <p className="mt-4 text-[11.5px] leading-relaxed text-faint">
            Todos os números desta tela têm proveniência: clique em qualquer valor sublinhado para ver
            origem, metodologia e versões.
          </p>
        </aside>
      </div>

      {/* gaveta de proveniência */}
      {drawer && (
        <>
          <div className="fixed inset-0 z-40 bg-navy-deep/20 backdrop-blur-[2px]" onClick={() => setDrawer(false)} />
          <div className="drawer-in fixed inset-y-0 right-0 z-50 w-[420px] overflow-y-auto bg-surface p-7 shadow-drawer">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display text-[19px] text-navy">Proveniência do número</h3>
                <p className="mt-0.5 text-[12px] text-muted">Retorno da carteira no semestre</p>
              </div>
              <button
                onClick={() => setDrawer(false)}
                className="rounded-lg p-1.5 text-muted transition-colors hover:bg-paper hover:text-navy"
                aria-label="Fechar"
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
              </button>
            </div>

            <dl className="mt-6 space-y-5">
              {[
                { t: "Valor completo", d: <span className="tnum text-[15px] font-semibold text-navy">5,2017% <span className="text-[11px] font-normal text-faint">(exibido: 5,20%)</span></span> },
                { t: "Metodologia", d: <>Modified Dietz mensal encadeado (aproximação de TWR), fluxos ponderados por dia — ENGINE_METHODOLOGY §4.</> },
                { t: "Dados de origem", d: <>7 valorações mensais (31/12/2025 a 30/06/2026) · 2 fluxos (aporte R$ 50.000,00 em 15/03; resgate R$ 30.000,00 em 10/05) · CDI: BCB/SGS série 12.</> },
                { t: "Execução", d: <>run <code className="rounded bg-paper px-1 py-0.5">85fd25b3152c43ab</code> · motor <code className="rounded bg-paper px-1 py-0.5">v0.2.0</code> · política <code className="rounded bg-paper px-1 py-0.5">v1</code> · dados de 30/06/2026</> },
                { t: "Confiança dos dados", d: <span className="flex items-center gap-2"><Seal grade="A" /> ×9 <Seal grade="B" /> ×2 <Seal grade="C" /> ×1 <span className="text-[11.5px] text-muted">— 1 posição com fonte a atualizar</span></span> },
              ].map((row) => (
                <div key={row.t}>
                  <dt className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-faint">{row.t}</dt>
                  <dd className="mt-1 text-[13px] leading-relaxed text-ink/85">{row.d}</dd>
                </div>
              ))}
            </dl>

            <p className="mt-7 rounded-xl bg-navy-soft p-3.5 text-[12px] leading-relaxed text-navy">
              Reproduzível: o mesmo snapshot e a mesma versão do motor produzem exatamente este
              resultado, para sempre.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
