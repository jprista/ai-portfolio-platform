import Link from "next/link";
import { Card, Seal, SectionTitle, StatusChip, type MeetingStatus } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getFamilies } from "@/lib/data";
import { brl, dateBR } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function FamiliasPage() {
  const { orgId } = await requireOrg();
  const families = await getFamilies(orgId);
  const totalWealth = families.reduce((acc, f) => acc + Number(f.wealth), 0);

  return (
    <div className="mx-auto max-w-[1100px] px-10 py-9">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="font-display text-[28px] tracking-tight text-navy">Famílias</h1>
          <p className="mt-1 text-[13px] text-muted">
            {families.length} famílias · {brl(totalWealth)} sob análise na plataforma
          </p>
        </div>
        <button className="rounded-full bg-navy px-5 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep">
          Nova família
        </button>
      </header>

      <SectionTitle>Carteiras</SectionTitle>
      <div className="flex flex-col gap-3">
        {families.map((f) => (
          <Card key={f.id} hover className="flex items-center gap-5 p-5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-navy-soft font-display text-[15px] text-navy">
              {f.display_name.replace("Família ", "").slice(0, 2)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-3">
                <span className="font-display text-[17px] text-navy">{f.display_name}</span>
                {f.pending_docs > 0 && (
                  <span className="rounded-full bg-warn-soft px-2 py-0.5 text-[10.5px] font-semibold text-warn">
                    {f.pending_docs} extração pendente
                  </span>
                )}
                {f.worst_confidence && ["C", "D"].includes(f.worst_confidence) && (
                  <Seal grade={f.worst_confidence} title="Há posições com selo de confiança a revisar" />
                )}
              </div>
              <div className="mt-1.5 flex items-center gap-2 text-[12.5px] text-muted">
                <span className="tnum font-medium text-ink/80">{brl(f.wealth)}</span>
                <span className="text-faint">·</span>
                <span>{f.n_positions} {f.n_positions === 1 ? "posição" : "posições"}</span>
                {f.holders && (
                  <>
                    <span className="text-faint">·</span>
                    <span className="truncate">{f.holders}</span>
                  </>
                )}
                {f.benchmark && (
                  <>
                    <span className="text-faint">·</span>
                    <span>benchmark {f.benchmark}</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              {f.next_meeting_id ? (
                <>
                  <div className="text-right">
                    <StatusChip status={(f.next_meeting_status ?? "scheduled") as MeetingStatus} />
                    <div className="mt-1 text-[11px] text-faint">
                      reunião {dateBR(f.next_meeting_at!)}
                    </div>
                  </div>
                  <Link
                    href={`/app/reunioes/${f.next_meeting_id}`}
                    className="rounded-full bg-navy px-4 py-2 text-[12.5px] font-medium text-white transition-colors hover:bg-navy-deep"
                  >
                    Abrir
                  </Link>
                </>
              ) : f.pending_docs > 0 ? (
                <Link
                  href="/app/caixa-de-confirmacao"
                  className="rounded-full border border-hairline bg-surface px-4 py-2 text-[12.5px] font-medium text-navy transition-colors hover:bg-navy-soft"
                >
                  Conferir extração
                </Link>
              ) : (
                <span className="text-[12px] text-faint">sem reunião agendada</span>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
