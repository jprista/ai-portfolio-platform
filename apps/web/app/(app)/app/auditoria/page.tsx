import Link from "next/link";
import { Card, SectionTitle } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getAuditEvents } from "@/lib/data";

export const dynamic = "force-dynamic";

const KIND_LABEL: Record<string, string> = {
  extraction_confirmed: "Extração confirmada",
  policy_changed: "Política alterada",
  run_created: "Análise gerada",
  document_generated: "Material gerado",
  document_exported: "Material exportado",
  meeting_state_skipped: "Estado de reunião pulado",
  material_frozen: "Material congelado",
  ai_records_purged: "Registros de IA expurgados",
  family_share_granted: "Compartilhamento concedido",
  family_share_revoked: "Compartilhamento revogado",
  data_viewed: "Dados visualizados",
  data_edited: "Dados editados",
  login: "Login",
  export_lgpd: "Exportação LGPD",
  purge_lgpd: "Purga LGPD",
};

const KIND_TONE: Record<string, string> = {
  extraction_confirmed: "bg-ok-soft text-ok",
  policy_changed: "bg-gold-soft text-gold",
  meeting_state_skipped: "bg-warn-soft text-warn",
  ai_records_purged: "bg-warn-soft text-warn",
  purge_lgpd: "bg-bad-soft text-bad",
};

function summarize(kind: string, payload: Record<string, unknown>): string {
  if (kind === "extraction_confirmed") {
    if (payload.decision === "rejected") return "Documento rejeitado pelo profissional";
    return `${payload.n_positions ?? "?"} posições confirmadas e enviadas ao motor`;
  }
  if (kind === "policy_changed") {
    return `Nova versão ${payload.new_version ?? "?"}: emissor ${payload.issuer_concentration_limit_pct}% · FGC R$ ${payload.fgc_limit} · vencimentos ${payload.maturity_window_days}d`;
  }
  const compact = JSON.stringify(payload);
  return compact.length > 120 ? compact.slice(0, 117) + "…" : compact;
}

export default async function AuditoriaPage({
  searchParams,
}: {
  searchParams: Promise<{ kind?: string }>;
}) {
  const { kind } = await searchParams;
  const { orgId } = await requireOrg();
  const events = await getAuditEvents(orgId, kind);
  const kindsInUse = [...new Set(events.map((e) => e.kind))];

  return (
    <div className="mx-auto max-w-[1000px] px-10 py-9">
      <header className="mb-6">
        <h1 className="font-display text-[28px] tracking-tight text-navy">Auditoria</h1>
        <p className="mt-1 max-w-[640px] text-[13px] leading-relaxed text-muted">
          Trilha imutável de tudo que aconteceu na plataforma — quem fez, o quê e quando. É esta tela
          que se apresenta a um auditor externo ou à supervisão regulatória.
        </p>
      </header>

      <div className="mb-5 flex items-center gap-2">
        <Link
          href="/app/auditoria"
          className={`rounded-full px-3 py-1.5 text-[11.5px] font-medium transition-colors ${
            !kind ? "bg-navy text-white" : "bg-surface text-muted ring-1 ring-hairline hover:text-navy"
          }`}
        >
          Todos
        </Link>
        {Object.entries(KIND_LABEL)
          .filter(([k]) => kindsInUse.includes(k) || k === kind)
          .map(([k, label]) => (
            <Link
              key={k}
              href={`/app/auditoria?kind=${k}`}
              className={`rounded-full px-3 py-1.5 text-[11.5px] font-medium transition-colors ${
                kind === k ? "bg-navy text-white" : "bg-surface text-muted ring-1 ring-hairline hover:text-navy"
              }`}
            >
              {label}
            </Link>
          ))}
      </div>

      <SectionTitle>{events.length} evento{events.length !== 1 ? "s" : ""}</SectionTitle>
      {events.length === 0 ? (
        <Card className="p-8 text-center text-[13px] text-muted">Nenhum evento registrado ainda.</Card>
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="border-b border-hairline text-left text-[10.5px] font-semibold uppercase tracking-wider text-faint">
                <th className="px-5 py-3 font-semibold">Quando</th>
                <th className="py-3 font-semibold">Evento</th>
                <th className="py-3 font-semibold">Autor</th>
                <th className="py-3 pr-5 font-semibold">Detalhe</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {events.map((e) => (
                <tr key={e.id} className="align-top transition-colors hover:bg-paper/50">
                  <td className="tnum whitespace-nowrap px-5 py-3 text-muted">
                    {new Date(e.created_at).toLocaleString("pt-BR", {
                      day: "2-digit", month: "2-digit", year: "2-digit",
                      hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo",
                    })}
                  </td>
                  <td className="py-3">
                    <span className={`rounded-full px-2.5 py-1 text-[10.5px] font-semibold ${KIND_TONE[e.kind] ?? "bg-navy-soft text-navy"}`}>
                      {KIND_LABEL[e.kind] ?? e.kind}
                    </span>
                  </td>
                  <td className="py-3 text-ink/80">{e.actor_name ?? "Sistema"}</td>
                  <td className="max-w-[380px] py-3 pr-5 leading-relaxed text-muted">
                    {summarize(e.kind, e.payload)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <p className="mt-4 text-[11.5px] leading-relaxed text-faint">
        Eventos de auditoria são imutáveis por permissão de banco (INSERT-only) — nem administradores
        conseguem editá-los ou apagá-los.
      </p>
    </div>
  );
}
