import Link from "next/link";
import { Card, SectionTitle, Seal, StatusChip, type MeetingStatus } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getMeetings } from "@/lib/data";
import { brl, dayParts, dateBR } from "@/lib/format";

export const dynamic = "force-dynamic";

const ACTION: Record<string, string> = {
  scheduled: "Preparar",
  preparing: "Continuar preparação",
  material_generated: "Enviar material",
  material_sent: "Marcar realizada",
  held: "Ver registro",
};

export default async function MesaDeReunioes() {
  const { orgId } = await requireOrg();
  const meetings = await getMeetings(orgId);
  const today = new Date().toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "America/Sao_Paulo",
  });

  const almeida = meetings.find((m) => m.family === "Família Almeida");

  return (
    <div className="mx-auto max-w-[1240px] px-10 py-9">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="font-display text-[28px] tracking-tight text-navy">Mesa de Reuniões</h1>
          <p className="mt-1 text-[13px] capitalize text-muted">{today}</p>
        </div>
        <button className="rounded-xl bg-navy px-4 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep">
          Agendar reunião
        </button>
      </header>

      <div className="flex items-start gap-8">
        <section className="min-w-0 flex-[1.8]">
          <SectionTitle>Próximas reuniões</SectionTitle>
          <div className="flex flex-col gap-3">
            {meetings.map((m) => {
              const parts = dayParts(m.scheduled_for);
              const insights = m.insights ?? [];
              const high = insights.filter((i) => i.severity === "alta").length;
              const hasRun = insights.length > 0;
              return (
                <Card key={m.id} hover className="flex items-center gap-5 p-5">
                  <div className="w-[76px] shrink-0 border-r border-hairline pr-5 text-center">
                    <div className="font-display text-[26px] leading-none text-navy">{parts.day}</div>
                    <div className="mt-1.5 text-[10px] font-medium uppercase tracking-wider text-muted">
                      {parts.rest}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
                      <span className="font-display text-[17px] text-navy">{m.family}</span>
                      <StatusChip status={m.status as MeetingStatus} />
                    </div>
                    <div className="mt-1.5 flex items-center gap-2 text-[12.5px] text-muted">
                      <span className="tnum">{brl(m.wealth)}</span>
                      {hasRun && (
                        <>
                          <span className="text-faint">·</span>
                          <span>
                            {insights.length} pontos de atenção{" "}
                            {high > 0 && <span className="font-semibold text-bad">({high} alta)</span>}
                          </span>
                        </>
                      )}
                      {m.material_sent_at && (
                        <>
                          <span className="text-faint">·</span>
                          <span>congelado em {dateBR(m.material_sent_at)}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <Link
                    href={hasRun ? `/reunioes/${m.id}` : "#"}
                    className={`shrink-0 rounded-xl px-4 py-2 text-[12.5px] font-medium transition-colors ${
                      m.status === "preparing"
                        ? "bg-navy text-white hover:bg-navy-deep"
                        : "border border-hairline bg-surface text-navy hover:bg-navy-soft"
                    }`}
                  >
                    {ACTION[m.status] ?? "Abrir"}
                  </Link>
                </Card>
              );
            })}
          </div>
        </section>

        <section className="w-[380px] shrink-0">
          <SectionTitle>Precisa da sua atenção</SectionTitle>
          <div className="flex flex-col gap-4">
            <Card className="p-4">
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
                Alertas de risco
              </div>
              <div className="divide-y divide-hairline">
                {(almeida?.insights ?? [])
                  .filter((i) => i.severity === "alta")
                  .map((i: { severity: string; title?: string }, idx: number) => (
                    <div key={idx} className="flex items-start gap-2.5 py-2.5 first:pt-0 last:pb-0">
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-bad" />
                      <span className="flex-1 text-[12.5px] leading-relaxed text-ink/85">{i.title}</span>
                      {almeida && (
                        <Link href={`/reunioes/${almeida.id}`} className="shrink-0 text-[12px] font-medium text-info hover:underline">
                          Ver
                        </Link>
                      )}
                    </div>
                  ))}
              </div>
            </Card>

            <Card className="p-4">
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
                Carteiras para revisão
              </div>
              <div className="flex items-start gap-2.5">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-warn" />
                <span className="flex-1 text-[12.5px] leading-relaxed text-ink/85">
                  Previdência FIE Zafira com selo{" "}
                  <Seal grade="C" title="Confiança C — documento parseado, não reconciliado" /> (Família
                  Almeida)
                </span>
              </div>
            </Card>

            <Card className="p-4">
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
                Tarefas
              </div>
              <div className="flex items-start gap-2.5">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-warn" />
                <span className="flex-1 text-[12.5px] leading-relaxed text-ink/85">
                  LCA Banco Gama vence em <b>46 dias</b> — definir destino antes de 15/08
                </span>
                {almeida && (
                  <Link href={`/reunioes/${almeida.id}`} className="shrink-0 text-[12px] font-medium text-info hover:underline">
                    Ver
                  </Link>
                )}
              </div>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}
