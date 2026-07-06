import Link from "next/link";
import { Card, SectionTitle, Seal, StatusChip, type MeetingStatus } from "@/components/ui";

const meetings: {
  day: string;
  rest: string;
  family: string;
  status: MeetingStatus;
  wealth: string;
  note?: string;
  attention?: { total: number; high: number };
  action: string;
  href: string;
  primary?: boolean;
}[] = [
  {
    day: "09",
    rest: "jul · qui · 10:00",
    family: "Família Almeida",
    status: "preparing",
    wealth: "R$ 2.913.933,80",
    attention: { total: 6, high: 3 },
    action: "Continuar preparação",
    href: "/reunioes/familia-almeida",
    primary: true,
  },
  {
    day: "10",
    rest: "jul · sex · 14:30",
    family: "Família Souza",
    status: "scheduled",
    wealth: "R$ 1.480.220,00",
    note: "última análise há 12 dias",
    action: "Preparar",
    href: "#",
  },
  {
    day: "14",
    rest: "jul · ter · 09:00",
    family: "Família Castro",
    status: "material_sent",
    wealth: "R$ 5.104.870,33",
    note: "congelado em 02/07 às 17:12",
    action: "Marcar realizada",
    href: "#",
  },
];

const attention = [
  {
    group: "Análises pendentes",
    items: [
      { tone: "bg-info", text: <>Extração aguardando confirmação — <b>Posição Detalhada XP</b> (Família Souza)</>, act: "Conferir" },
      { tone: "bg-info", text: <>Contrato incompleto: <b>CDB IPCA+ Banco Delta</b> — falta data de aniversário</>, act: "Completar" },
    ],
  },
  {
    group: "Alertas de risco",
    items: [
      { tone: "bg-bad", text: <><b>2 titulares acima do teto do FGC</b> — José Almeida (Banco Beta) e Maria Almeida (Banco Delta)</>, act: "Ver", href: "/reunioes/familia-almeida" },
      { tone: "bg-bad", text: <>Concentração da família em <b>Banco Beta: 19,30%</b> (política: 15%)</>, act: "Ver", href: "/reunioes/familia-almeida" },
    ],
  },
  {
    group: "Carteiras para revisão",
    items: [
      {
        tone: "bg-warn",
        text: <>Previdência FIE Zafira com selo <Seal grade="C" title="Confiança C — documento parseado, não reconciliado" /> há 9 dias (Família Almeida)</>,
        act: "Atualizar",
      },
    ],
  },
  {
    group: "Tarefas",
    items: [
      { tone: "bg-warn", text: <>LCA Banco Gama vence em <b>46 dias</b> — definir destino antes de 15/08</>, act: "Levar à reunião", href: "/reunioes/familia-almeida" },
    ],
  },
];

export default function MesaDeReunioes() {
  return (
    <div className="mx-auto max-w-[1240px] px-10 py-9">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="font-display text-[28px] tracking-tight text-navy">Mesa de Reuniões</h1>
          <p className="mt-1 text-[13px] text-muted">segunda-feira, 6 de julho de 2026</p>
        </div>
        <button className="rounded-xl bg-navy px-4 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep">
          Agendar reunião
        </button>
      </header>

      <div className="flex items-start gap-8">
        <section className="min-w-0 flex-[1.8]">
          <SectionTitle>Próximas reuniões</SectionTitle>
          <div className="flex flex-col gap-3">
            {meetings.map((m) => (
              <Card key={m.family} hover className="flex items-center gap-5 p-5">
                <div className="w-[76px] shrink-0 border-r border-hairline pr-5 text-center">
                  <div className="font-display text-[26px] leading-none text-navy">{m.day}</div>
                  <div className="mt-1.5 text-[10px] font-medium uppercase tracking-wider text-muted">
                    {m.rest}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-display text-[17px] text-navy">{m.family}</span>
                    <StatusChip status={m.status} />
                  </div>
                  <div className="mt-1.5 flex items-center gap-2 text-[12.5px] text-muted">
                    <span className="tnum">{m.wealth}</span>
                    {m.attention && (
                      <>
                        <span className="text-faint">·</span>
                        <span>
                          {m.attention.total} pontos de atenção{" "}
                          <span className="font-semibold text-bad">({m.attention.high} alta)</span>
                        </span>
                      </>
                    )}
                    {m.note && (
                      <>
                        <span className="text-faint">·</span>
                        <span>{m.note}</span>
                      </>
                    )}
                  </div>
                </div>
                <Link
                  href={m.href}
                  className={`shrink-0 rounded-xl px-4 py-2 text-[12.5px] font-medium transition-colors ${
                    m.primary
                      ? "bg-navy text-white hover:bg-navy-deep"
                      : "border border-hairline bg-surface text-navy hover:bg-navy-soft"
                  }`}
                >
                  {m.action}
                </Link>
              </Card>
            ))}
          </div>
        </section>

        <section className="w-[380px] shrink-0">
          <SectionTitle>Precisa da sua atenção</SectionTitle>
          <div className="flex flex-col gap-4">
            {attention.map((g) => (
              <Card key={g.group} className="p-4">
                <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
                  {g.group}
                </div>
                <div className="divide-y divide-hairline">
                  {g.items.map((item, i) => (
                    <div key={i} className="flex items-start gap-2.5 py-2.5 first:pt-0 last:pb-0">
                      <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${item.tone}`} />
                      <span className="flex-1 text-[12.5px] leading-relaxed text-ink/85">
                        {item.text}
                      </span>
                      <Link
                        href={"href" in item && item.href ? item.href : "#"}
                        className="shrink-0 text-[12px] font-medium text-info hover:underline"
                      >
                        {item.act}
                      </Link>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
