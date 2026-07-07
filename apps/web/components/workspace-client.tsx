"use client";

import { Fragment, useState, type ReactNode } from "react";
import Link from "next/link";
import { Card, InsightCard, Seal, SectionTitle } from "@/components/ui";

export type WorkspaceProps = {
  family: string;
  dateLabel: string;
  status: string;
  run: { short: string; engineVersion: string; policyVersion: number; asOf: string; drawerSources: string };
  kpis: { label: string; value: string }[];
  resumo: string;
  mudancas: string[];
  insights: { severity: "alta" | "média" | "baixa"; title: string; detail: string }[];
  agenda: string[];
  carteira: {
    cls: string;
    subtotal: string;
    pct: string;
    reading: string;
    positions: { name: string; holder: string; index: string; maturity: string; liq: string; seal: string; value: string; pct: string }[];
  }[];
  liquidez: { bucket: string; value: string; pct: number }[];
  concentracoes: { label: string; value: string; note: string; bad: boolean }[];
  confMix: { grade: string; count: number }[];
  qa: { question: string; answer: string };
};

const JOURNEY: { key: string; label: string }[] = [
  { key: "scheduled", label: "Agendada" },
  { key: "preparing", label: "Em preparação" },
  { key: "material_generated", label: "Material gerado" },
  { key: "material_sent", label: "Material enviado" },
  { key: "held", label: "Realizada" },
];

const NUM_RE = /(R\$\s?[\d.]+,\d{2}|\d{1,3}(?:\.\d{3})*,\d{2,4}\s?%|\d+,\d{2,4}\s?%|\d+,\d{2,4})/g;

export function WorkspaceClient(p: WorkspaceProps) {
  const [drawer, setDrawer] = useState(false);
  const [tab, setTab] = useState<"briefing" | "carteira" | "atencao">("briefing");
  const currentIdx = JOURNEY.findIndex((j) => j.key === p.status);

  const Num = ({ children }: { children: ReactNode }) => (
    <button
      onClick={() => setDrawer(true)}
      className="tnum cursor-pointer rounded-sm border-b border-dashed border-gold/70 font-medium text-navy transition-colors hover:bg-gold-soft"
      title="Ver proveniência deste número"
    >
      {children}
    </button>
  );

  const withNums = (text: string) => {
    const parts = text.split(NUM_RE);
    return parts.map((part, i) =>
      NUM_RE.test(part) && i % 2 === 1 ? <Num key={i}>{part}</Num> : <Fragment key={i}>{part}</Fragment>
    );
  };

  return (
    <div className="mx-auto max-w-[1240px] px-10 py-9">
      <nav className="mb-2 text-[12px] text-muted">
        <Link href="/app" className="hover:underline">Mesa de Reuniões</Link>
        <span className="mx-1.5 text-faint">/</span>
        {p.family}
      </nav>

      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-[26px] tracking-tight text-navy">{p.family} — Revisão</h1>
          <p className="mt-1 text-[13px] text-muted">{p.dateLabel}</p>
        </div>
        <button className="rounded-full bg-navy px-5 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep">
          Gerar material do cliente
        </button>
      </header>

      <div className="mb-7 flex items-center gap-2">
        {JOURNEY.map((step, i) => (
          <div key={step.key} className="flex items-center gap-2">
            <span
              className={`rounded-full px-3 py-1.5 text-[11.5px] font-medium ${
                i < currentIdx
                  ? "bg-ok-soft text-ok"
                  : i === currentIdx
                    ? "bg-navy text-white shadow-card"
                    : "bg-surface text-faint ring-1 ring-hairline"
              }`}
            >
              {i < currentIdx ? "✓ " : ""}{step.label}
            </span>
            {i < JOURNEY.length - 1 && <span className="h-px w-4 bg-hairline" />}
          </div>
        ))}
      </div>

      <div className="mb-8 grid grid-cols-4 gap-4">
        {p.kpis.map((k) => (
          <Card key={k.label} className="p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-faint">{k.label}</div>
            <div className="mt-1.5 text-[17px]"><Num>{k.value}</Num></div>
          </Card>
        ))}
      </div>

      <div className="flex items-start gap-8">
        <section className="min-w-0 flex-[1.9]">
          <div className="mb-4 flex gap-1 border-b border-hairline">
            {[
              { id: "briefing" as const, label: "Briefing" },
              { id: "carteira" as const, label: "Carteira" },
              { id: "atencao" as const, label: `Pontos de atenção (${p.insights.length})` },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`-mb-px border-b-2 px-4 py-2.5 text-[13.5px] transition-colors ${
                  tab === t.id ? "border-gold font-semibold text-navy" : "border-transparent text-muted hover:text-navy"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "briefing" && (
            <>
              <Card className="p-6 text-[14px] leading-[1.75] text-ink/90">
                <p><strong className="text-navy">Resumo executivo.</strong> {withNums(p.resumo)}</p>
                <p className="mt-4">
                  <strong className="text-navy">O que mudou desde a última reunião.</strong>{" "}
                  {p.mudancas.map((m, i) => <Fragment key={i}>{withNums(m)}{" "}</Fragment>)}
                </p>
                <p className="mt-4 border-t border-hairline pt-3 text-[11.5px] text-faint">
                  Gerado do run <code className="rounded bg-paper px-1.5 py-0.5">{p.run.short.slice(0, 8)}</code> ·
                  motor v{p.run.engineVersion.replace("-prototype", "")} · política v{p.run.policyVersion} ·
                  todos os números são clicáveis
                </p>
              </Card>

              <Card className="mt-6 p-4">
                <div className="flex gap-2.5">
                  <input
                    defaultValue={p.qa.question}
                    placeholder="Pergunte sobre a carteira…"
                    className="flex-1 rounded-xl border border-hairline bg-paper px-4 py-2.5 text-[13px] outline-none transition-shadow focus:ring-2 focus:ring-gold/40"
                  />
                  <button className="rounded-full bg-navy px-5 py-2 text-[13px] font-medium text-white transition-colors hover:bg-navy-deep">
                    Perguntar
                  </button>
                </div>
                <div className="mt-3 rounded-xl bg-paper p-4 text-[13px] leading-relaxed text-ink/85">
                  {withNums(p.qa.answer)}
                  <div className="mt-2.5 flex items-center justify-between text-[11px] text-faint">
                    <span>
                      Fundamentado no run <code className="rounded bg-surface px-1 py-0.5">{p.run.short.slice(0, 8)}</code> · verificador: aprovado
                    </span>
                    <span className="cursor-help" title="Interações com a IA são registradas na trilha de auditoria, conforme os termos de uso e a política de retenção da sua organização.">
                      ⛨ registrado
                    </span>
                  </div>
                </div>
              </Card>
            </>
          )}

          {tab === "atencao" && (
            <div className="flex flex-col gap-3">
              {p.insights.map((ins) => (
                <InsightCard key={ins.title} severity={ins.severity} title={ins.title}>
                  {withNums(ins.detail)}
                </InsightCard>
              ))}
            </div>
          )}

          {tab === "carteira" && (
            <div className="flex flex-col gap-4">
              {p.carteira.map((g) => (
                <Card key={g.cls} className="overflow-hidden">
                  <div className="flex items-baseline justify-between border-b border-hairline bg-paper/60 px-5 py-3">
                    <div className="flex items-baseline gap-3">
                      <span className="font-display text-[15px] text-navy">{g.cls}</span>
                      <span className="text-[12px] text-muted">
                        {g.positions.length} {g.positions.length > 1 ? "posições" : "posição"}
                      </span>
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
                      {g.positions.map((pos) => (
                        <tr key={pos.name} className="transition-colors hover:bg-paper/50">
                          <td className="px-5 py-2.5 font-medium text-ink">{pos.name}</td>
                          <td className="py-2.5 text-muted">{pos.holder}</td>
                          <td className="py-2.5 text-muted">{pos.index}</td>
                          <td className="py-2.5 text-muted">{pos.maturity}</td>
                          <td className="py-2.5 text-muted">{pos.liq}</td>
                          <td className="py-2.5 text-center"><Seal grade={pos.seal} /></td>
                          <td className="py-2.5 pr-5 text-right">
                            <Num>{pos.value}</Num>
                            <span className="tnum ml-2 text-[11px] text-faint">{pos.pct}</span>
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

              <div className="grid grid-cols-2 gap-4">
                <Card className="p-5">
                  <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-faint">Escada de liquidez</div>
                  <div className="space-y-3">
                    {p.liquidez.map((l) => (
                      <div key={l.bucket}>
                        <div className="mb-1 flex items-baseline justify-between text-[12px]">
                          <span className="text-ink/80">{l.bucket}</span>
                          <span className="tnum text-muted">{l.value} · {l.pct.toFixed(2).replace(".", ",")}%</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-paper">
                          <div className="h-full rounded-full bg-navy/80" style={{ width: `${Math.min(l.pct, 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
                <Card className="p-5">
                  <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-faint">Concentrações e FGC</div>
                  <div className="divide-y divide-hairline">
                    {p.concentracoes.map((c) => (
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
        </section>

        {tab !== "carteira" && (
          <aside className="w-[340px] shrink-0">
            <SectionTitle>Material da reunião</SectionTitle>
            <Card className="p-4">
              <div className="text-[13px] font-semibold text-navy">Briefing interno — v1</div>
              <div className="mt-1 text-[11.5px] leading-relaxed text-muted">
                run <code className="rounded bg-paper px-1 py-0.5">{p.run.short}</code>
                <br />motor v{p.run.engineVersion.replace("-prototype", "")} · política v{p.run.policyVersion} · dados de {p.run.asOf}
              </div>
            </Card>
            <Card className="mt-3 border-dashed p-4">
              <div className="text-[13px] font-semibold text-muted">Relatório do cliente</div>
              <div className="mt-1 text-[11.5px] leading-relaxed text-muted">
                Produzido com a marca do escritório a partir do run atual. Após o envio, o material é{" "}
                <b>congelado</b>; alterações criam nova versão, preservando as anteriores.
              </div>
            </Card>
            <div className="mt-6">
              <SectionTitle>Pauta sugerida</SectionTitle>
              <Card className="p-4">
                <ol className="list-decimal space-y-2 pl-4 text-[12.5px] leading-relaxed text-ink/85 marker:font-semibold marker:text-gold">
                  {p.agenda.map((a) => <li key={a}>{a}</li>)}
                </ol>
              </Card>
            </div>
            <p className="mt-4 text-[11.5px] leading-relaxed text-faint">
              Todos os números desta tela têm proveniência: clique em qualquer valor sublinhado.
            </p>
          </aside>
        )}
      </div>

      {drawer && (
        <>
          <div className="fixed inset-0 z-40 bg-navy-deep/20 backdrop-blur-[2px]" onClick={() => setDrawer(false)} />
          <div className="drawer-in fixed inset-y-0 right-0 z-50 w-[420px] overflow-y-auto bg-surface p-7 shadow-drawer">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display text-[19px] text-navy">Proveniência</h3>
                <p className="mt-0.5 text-[12px] text-muted">Execução do motor que originou esta análise</p>
              </div>
              <button onClick={() => setDrawer(false)} className="rounded-lg p-1.5 text-muted transition-colors hover:bg-paper hover:text-navy" aria-label="Fechar">
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
              </button>
            </div>
            <dl className="mt-6 space-y-5">
              <DrawerRow t="Metodologia">Modified Dietz mensal encadeado (aproximação de TWR), fluxos ponderados por dia — ENGINE_METHODOLOGY §4. Benchmark CDI acumulado por capitalização diária (BCB/SGS 12).</DrawerRow>
              <DrawerRow t="Dados de origem">{p.run.drawerSources}</DrawerRow>
              <DrawerRow t="Execução">
                run <code className="rounded bg-paper px-1 py-0.5">{p.run.short}</code> · motor{" "}
                <code className="rounded bg-paper px-1 py-0.5">v{p.run.engineVersion}</code> · política{" "}
                <code className="rounded bg-paper px-1 py-0.5">v{p.run.policyVersion}</code> · dados de {p.run.asOf}
              </DrawerRow>
              <DrawerRow t="Confiança dos dados">
                <span className="flex items-center gap-2">
                  {p.confMix.map((c) => (
                    <span key={c.grade} className="flex items-center gap-1">
                      <Seal grade={c.grade} /> ×{c.count}
                    </span>
                  ))}
                </span>
              </DrawerRow>
            </dl>
            <p className="mt-7 rounded-xl bg-navy-soft p-3.5 text-[12px] leading-relaxed text-navy">
              Reproduzível: o mesmo snapshot e a mesma versão do motor produzem exatamente este resultado, para sempre.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

function DrawerRow({ t, children }: { t: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-faint">{t}</dt>
      <dd className="mt-1 text-[13px] leading-relaxed text-ink/85">{children}</dd>
    </div>
  );
}
