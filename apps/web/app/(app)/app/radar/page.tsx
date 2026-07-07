import { Card, SectionTitle } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getRadar, type ManagerCard } from "@/lib/data";
import { pct } from "@/lib/format";

export const dynamic = "force-dynamic";

const CHANGE: Record<string, { label: string; cls: string }> = {
  new: { label: "Nova", cls: "bg-ok-soft text-ok" },
  increased: { label: "Aumentou", cls: "bg-info-soft text-info" },
  reduced: { label: "Reduziu", cls: "bg-warn-soft text-warn" },
};

function ManagerCardView({ m, sourceLabel }: { m: ManagerCard; sourceLabel: string }) {
  return (
    <Card hover className="p-5">
      <div className="flex items-baseline justify-between border-b border-hairline pb-3">
        <div className="font-display text-[16px] text-navy">{m.name}</div>
        <div className="text-[11px] text-faint">
          {sourceLabel} · {m.period_end.split("-").reverse().join("/")}
        </div>
      </div>
      <div className="mt-3 space-y-2.5">
        {m.holdings.map((h) => (
          <div key={h.rank} className="flex items-center gap-3">
            <span className="tnum w-4 text-[11px] text-faint">{h.rank}</span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-[13px] font-medium text-ink">
                  {h.instrument ? `${h.instrument} · ` : ""}{h.issuer_name}
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  {h.change_kind && CHANGE[h.change_kind] && (
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${CHANGE[h.change_kind].cls}`}>
                      {CHANGE[h.change_kind].label}
                    </span>
                  )}
                  <span className="tnum text-[12px] text-muted">{pct(h.pct_of_total)}</span>
                </span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-paper">
                <div
                  className="h-full rounded-full bg-navy/70"
                  style={{ width: `${Math.min(Number(h.pct_of_total), 100)}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      {m.source_url && (
        <a
          href={m.source_url}
          target="_blank"
          className="mt-3 inline-block text-[11.5px] font-medium text-info hover:underline"
        >
          Fonte: declaração regulatória original ↗
        </a>
      )}
    </Card>
  );
}

export default async function RadarPage() {
  await requireOrg();
  const managers = await getRadar();
  const br = managers.filter((m) => m.jurisdiction === "BR");
  const us = managers.filter((m) => m.jurisdiction === "US");

  return (
    <div className="mx-auto max-w-[1240px] px-10 py-9">
      <header className="mb-3">
        <h1 className="font-display text-[28px] tracking-tight text-navy">Radar de Consenso</h1>
        <p className="mt-1 max-w-[780px] text-[13px] leading-relaxed text-muted">
          O que as maiores casas <b>detêm e mudaram</b> — direto das declarações regulatórias públicas
          (carteiras de fundos na CVM e 13F na SEC). Evidência para a sua decisão; a recomendação é
          sempre sua.
        </p>
      </header>
      <p className="mb-7 inline-block rounded-lg bg-gold-soft px-3 py-1.5 text-[11.5px] text-ink/70">
        Defasagem regulatória declarada por desenho: a CVM permite sigilo de até 90 dias por posição
        (casas de ações usam intensamente — mostramos o mês completo mais recente de cada casa);
        o 13F sai ~45 dias após o fim do trimestre.
      </p>

      <SectionTitle>Casas brasileiras — carteiras de ações declaradas à CVM</SectionTitle>
      <div className="mb-9 grid grid-cols-2 gap-5">
        {br.map((m) => (
          <ManagerCardView key={m.name} m={m} sourceLabel="CVM · CDA" />
        ))}
      </div>

      <SectionTitle>Casas globais — SEC 13F</SectionTitle>
      <div className="grid grid-cols-2 gap-5">
        {us.map((m) => (
          <ManagerCardView key={m.name} m={m} sourceLabel="13F" />
        ))}
      </div>

      <div className="mt-8">
        <SectionTitle>Como isto vira decisão</SectionTitle>
        <Card className="p-5 text-[13px] leading-relaxed text-ink/80">
          Na próxima versão, o Radar cruza com as <b>listas de ativos aprovados do seu escritório</b>:
          cada candidato da sua lista ganha o painel de evidências (quem detém, quem aumentou, citações
          em cartas de gestão) — e a <b>proposta assistida</b> monta o rascunho da recomendação com as
          evidências anexadas, para você revisar e assinar. A curadoria é da casa; a autoria é sua; a
          plataforma organiza a prova.
        </Card>
      </div>
    </div>
  );
}
