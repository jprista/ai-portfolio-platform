import Link from "next/link";
import { Card, SectionTitle } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getPendingExtractions } from "@/lib/data";
import { brl } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function CaixaDeConfirmacao() {
  const { orgId } = await requireOrg();
  const docs = await getPendingExtractions(orgId);

  return (
    <div className="mx-auto max-w-[1000px] px-10 py-9">
      <header className="mb-2">
        <h1 className="font-display text-[28px] tracking-tight text-navy">Caixa de confirmação</h1>
        <p className="mt-1 max-w-[640px] text-[13px] leading-relaxed text-muted">
          Extrações de documentos aguardando conferência humana. Nenhum dado entra no motor de análise
          sem passar por aqui — é a trava contra alucinação de parsing.
        </p>
      </header>

      {docs.length === 0 ? (
        <Card className="mt-8 p-8 text-center">
          <p className="text-[14px] text-muted">Nenhuma extração pendente no momento.</p>
        </Card>
      ) : (
        <>
          <SectionTitle>{docs.length} documento{docs.length > 1 ? "s" : ""} pendente{docs.length > 1 ? "s" : ""}</SectionTitle>
          <div className="flex flex-col gap-3">
            {docs.map((d) => (
              <Card key={d.id} hover className="flex items-center gap-5 p-5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-info-soft text-info">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
                    <path d="M14 3v5h5" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-display text-[16px] text-navy">{d.family}</div>
                  <div className="mt-1 flex items-center gap-2 text-[12.5px] text-muted">
                    <span>{d.n_positions} posições extraídas</span>
                    <span className="text-faint">·</span>
                    <span className="tnum">{brl(d.total_value)}</span>
                    <span className="text-faint">·</span>
                    <span className={d.reconciled ? "text-ok" : "text-warn"}>
                      {d.reconciled ? "Reconciliado com o total declarado" : "Divergência a revisar"}
                    </span>
                  </div>
                </div>
                <Link
                  href={`/app/caixa-de-confirmacao/${d.id}`}
                  className="shrink-0 rounded-full bg-navy px-5 py-2.5 text-[13px] font-medium text-white transition-colors hover:bg-navy-deep"
                >
                  Conferir
                </Link>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
