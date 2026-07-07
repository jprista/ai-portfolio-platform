import { notFound } from "next/navigation";
import Link from "next/link";
import { Card, Seal } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getExtractionDetail, type ExtractionPosition } from "@/lib/data";
import { getSignedDocumentUrl } from "@/lib/storage";
import { brl } from "@/lib/format";
import { confirmExtraction, rejectExtraction } from "../actions";

export const dynamic = "force-dynamic";

const CLASS_LABEL: Record<string, string> = {
  renda_fixa_pos: "Renda fixa pós-fixada",
  renda_variavel: "Renda variável",
  renda_fixa_inflacao: "Renda fixa inflação",
  multimercado: "Multimercado",
  caixa: "Caixa e liquidez",
  previdencia: "Previdência",
};

function classify(p: ExtractionPosition): string {
  if (p.category) return p.category;
  if (p.kind === "pension_fund") return "previdencia";
  if (["equity", "etf", "fii", "bdr"].includes(p.kind)) return "renda_variavel";
  if (p.index_kind === "ipca_plus") return "renda_fixa_inflacao";
  if (p.kind === "cash") return "caixa";
  return "renda_fixa_pos";
}

export default async function ExtractionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { orgId } = await requireOrg();
  const detail = await getExtractionDetail(orgId, id);
  if (!detail) notFound();

  const pdfUrl = await getSignedDocumentUrl(detail.storagePath).catch((e) => {
    console.error("getSignedDocumentUrl failed:", e);
    return null;
  });

  const groups = new Map<string, { positions: (ExtractionPosition & { idx: number })[]; subtotal: number }>();
  detail.positions.forEach((p, idx) => {
    const cls = classify(p);
    const g = groups.get(cls) ?? { positions: [], subtotal: 0 };
    g.positions.push({ ...p, idx });
    g.subtotal += Number(p.value);
    groups.set(cls, g);
  });

  const missingCount = detail.positions.filter(
    (p) => p.contract_terms && Object.values(p.contract_terms).some((v) => !v)
  ).length;

  return (
    <div className="mx-auto max-w-[1100px] px-10 py-9">
      <nav className="mb-2 text-[12px] text-muted">
        <Link href="/app/caixa-de-confirmacao" className="hover:underline">Caixa de confirmação</Link>
        <span className="mx-1.5 text-faint">/</span>
        {detail.family}
      </nav>

      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-[26px] tracking-tight text-navy">{detail.family}</h1>
          <p className="mt-1 text-[13px] text-muted">
            {detail.custodiante} · conta ***{detail.conta.slice(-4)} · perfil {detail.perfil} · dados de{" "}
            {detail.referenceDate.split("-").reverse().join("/")}
          </p>
        </div>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 rounded-full border border-hairline bg-surface px-4 py-2 text-[12.5px] font-medium text-navy transition-colors hover:bg-navy-soft"
          >
            Abrir documento original ↗
          </a>
        )}
      </header>

      <Card className={`mb-6 flex items-center justify-between p-4 ${detail.reconciled ? "bg-ok-soft/40" : "bg-warn-soft/40"}`}>
        <div className="text-[13px]">
          <span className="font-semibold text-navy">Reconciliação: </span>
          Total declarado no documento <b className="tnum">{brl(detail.declaredTotal)}</b> · soma das posições extraídas{" "}
          <b className="tnum">{brl(detail.sumOfPositions)}</b>
          {missingCount > 0 && (
            <span className="ml-2 text-warn">· {missingCount} posição(ões) com dado de contrato incompleto</span>
          )}
        </div>
        <span className={`rounded-full px-3 py-1 text-[11.5px] font-semibold ${detail.reconciled ? "bg-ok text-white" : "bg-warn text-white"}`}>
          {detail.reconciled ? "Reconciliado" : "Revisar"}
        </span>
      </Card>

      <form id="confirm-form" action={confirmExtraction.bind(null, detail.id)}>
        <div className="flex flex-col gap-4">
          {[...groups.entries()].map(([cls, g]) => (
            <Card key={cls} className="overflow-hidden">
              <div className="flex items-baseline justify-between border-b border-hairline bg-paper/60 px-5 py-3">
                <span className="font-display text-[15px] text-navy">{CLASS_LABEL[cls] ?? cls}</span>
                <span className="tnum text-[13.5px] font-semibold text-navy">{brl(g.subtotal)}</span>
              </div>
              <table className="w-full text-[12.5px]">
                <thead>
                  <tr className="text-left text-[10.5px] font-semibold uppercase tracking-wider text-faint">
                    <th className="px-5 py-2.5 font-semibold">Ativo extraído</th>
                    <th className="py-2.5 font-semibold">Emissor</th>
                    <th className="py-2.5 text-center font-semibold">Selo</th>
                    <th className="py-2.5 font-semibold">Contrato</th>
                    <th className="py-2.5 pr-5 text-right font-semibold">Valor (editável)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline">
                  {g.positions.map((p) => {
                    const ct = p.contract_terms;
                    const missing = ct ? Object.entries(ct).filter(([, v]) => !v).map(([k]) => k) : [];
                    return (
                      <tr key={p.idx} className="align-top">
                        <td className="px-5 py-2.5 font-medium text-ink">
                          {p.name}
                          {p.note && <div className="mt-0.5 text-[11px] font-normal text-faint">{p.note}</div>}
                        </td>
                        <td className="py-2.5 text-muted">{p.issuer}</td>
                        <td className="py-2.5 text-center"><Seal grade={p.confidence} /></td>
                        <td className="py-2.5 text-[11.5px] text-muted">
                          {ct ? (
                            <>
                              {ct.aplicacao && <div>aplicação {ct.aplicacao.split("-").reverse().join("/")}</div>}
                              {ct.vencimento && <div>venc. {ct.vencimento.split("-").reverse().join("/")}</div>}
                              {ct.taxa_contratada && <div>taxa contratada {ct.taxa_contratada}%</div>}
                              {ct.taxa_mercado && <div>taxa a mercado {ct.taxa_mercado}%</div>}
                              {ct.index_pct && <div>{ct.index_pct}% CDI</div>}
                              {missing.length > 0 && (
                                <div className="mt-1 font-medium text-warn">
                                  falta: {missing.join(", ")} — complementação necessária
                                </div>
                              )}
                            </>
                          ) : (
                            <span className="text-faint">—</span>
                          )}
                        </td>
                        <td className="py-2.5 pr-5 text-right">
                          <input
                            type="text"
                            name={`value_${p.idx}`}
                            defaultValue={p.value}
                            className="tnum w-28 rounded-lg border border-hairline bg-paper px-2 py-1 text-right text-[12.5px] outline-none focus:ring-2 focus:ring-gold/40"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          ))}
        </div>
      </form>

      <div className="mt-6 flex items-center justify-between">
        <p className="max-w-[480px] text-[11.5px] leading-relaxed text-faint">
          Confirmar cria as posições reais na plataforma, dispara uma nova análise no motor e vincula o
          resultado à próxima reunião do cliente. A ação fica registrada na trilha de auditoria.
        </p>
        <div className="flex gap-3">
          <form action={rejectExtraction.bind(null, detail.id)}>
            <button
              type="submit"
              className="rounded-full border border-hairline bg-surface px-5 py-2.5 text-[13px] font-medium text-bad transition-colors hover:bg-bad-soft"
            >
              Rejeitar
            </button>
          </form>
          <button
            type="submit"
            form="confirm-form"
            className="rounded-full bg-navy px-6 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep"
          >
            Confirmar tudo
          </button>
        </div>
      </div>
    </div>
  );
}
