import { Card, SectionTitle } from "@/components/ui";
import { requireOrg } from "@/lib/auth";
import { getOrgSettings } from "@/lib/data";
import { dateBR } from "@/lib/format";
import { savePolicyVersion } from "./actions";

export const dynamic = "force-dynamic";

function Field({
  label, name, defaultValue, suffix, hint,
}: { label: string; name: string; defaultValue: string; suffix?: string; hint?: string }) {
  return (
    <label className="block">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-faint">{label}</span>
      <span className="mt-1 flex items-center gap-2">
        <input
          type="text"
          name={name}
          defaultValue={defaultValue}
          className="tnum w-32 rounded-lg border border-hairline bg-paper px-3 py-2 text-[13px] outline-none focus:ring-2 focus:ring-gold/40"
        />
        {suffix && <span className="text-[12px] text-muted">{suffix}</span>}
      </span>
      {hint && <span className="mt-1 block text-[11px] leading-relaxed text-faint">{hint}</span>}
    </label>
  );
}

export default async function ConfiguracoesPage() {
  const { orgId } = await requireOrg();
  const s = await getOrgSettings(orgId);

  return (
    <div className="mx-auto max-w-[900px] px-10 py-9">
      <header className="mb-8">
        <h1 className="font-display text-[28px] tracking-tight text-navy">Configurações</h1>
        <p className="mt-1 text-[13px] text-muted">
          {s.org.name} · criada em {dateBR(s.org.created_at)}
        </p>
      </header>

      <SectionTitle>Política de análise — versão {s.policy.version} vigente</SectionTitle>
      <Card className="p-6">
        <p className="mb-5 max-w-[620px] text-[12.5px] leading-relaxed text-muted">
          Estes limiares parametrizam os pontos de atenção do motor. Políticas são{" "}
          <b>imutáveis</b>: salvar cria uma nova versão, e cada análise registra com qual versão foi
          gerada — um auditor sempre saberá quais regras valiam em cada data.
        </p>
        <form action={savePolicyVersion} className="space-y-5">
          <div className="grid grid-cols-2 gap-x-8 gap-y-5">
            <Field
              label="Concentração máx. por emissor"
              name="issuer_limit"
              defaultValue={Number(s.policy.issuer_concentration_limit_pct).toFixed(2).replace(".", ",")}
              suffix="% da carteira"
              hint="Acima disso, o motor gera alerta de concentração da família."
            />
            <Field
              label="Teto FGC por titular"
              name="fgc_limit"
              defaultValue={Number(s.policy.fgc_limit).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              suffix="R$ por CPF/emissor"
              hint="Cobertura regulatória do FGC — cálculo sempre por titular."
            />
            <Field
              label="Janela de vencimentos"
              name="maturity_days"
              defaultValue={String(s.policy.maturity_window_days)}
              suffix="dias"
              hint="Vencimentos dentro da janela entram na pauta da reunião."
            />
            <Field
              label="Observações mínimas p/ volatilidade"
              name="min_vol_obs"
              defaultValue={String(s.policy.min_vol_observations)}
              suffix="períodos"
              hint="Abaixo disso, o motor declara histórico insuficiente."
            />
            <Field
              label="Retenção de registros de IA"
              name="ai_retention_days"
              defaultValue={s.policy.ai_interaction_retention_days?.toString() ?? ""}
              suffix="dias (vazio = indefinida)"
              hint="Perguntas e gerações de IA são expurgadas após o prazo; o expurgo é auditado."
            />
          </div>
          <div className="flex items-center justify-end gap-4 border-t border-hairline pt-4">
            <span className="text-[11.5px] text-faint">A alteração fica registrada na trilha de auditoria.</span>
            <button
              type="submit"
              className="rounded-full bg-navy px-5 py-2.5 text-[13px] font-medium text-white shadow-card transition-colors hover:bg-navy-deep"
            >
              Salvar como versão {s.policy.version + 1}
            </button>
          </div>
        </form>
      </Card>

      <div className="mt-4">
        <Card className="p-4">
          <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
            Histórico de versões
          </div>
          <div className="divide-y divide-hairline">
            {s.policyHistory.map((p) => (
              <div key={p.version} className="flex items-center justify-between py-2 text-[12.5px]">
                <span className="font-medium text-ink">Versão {p.version}</span>
                <span className="text-muted">
                  vigente desde {dateBR(p.effective_from)}
                  {p.created_by_name ? ` · por ${p.created_by_name}` : " · criada no onboarding"}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-9 grid grid-cols-2 gap-5">
        <div>
          <SectionTitle>Equipe</SectionTitle>
          <Card className="p-4">
            <div className="divide-y divide-hairline">
              {s.team.map((u) => (
                <div key={u.email} className="flex items-center justify-between py-2.5">
                  <div>
                    <div className="text-[13px] font-medium text-ink">{u.name}</div>
                    <div className="text-[11.5px] text-faint">{u.email}</div>
                  </div>
                  <span className={`rounded-full px-2.5 py-0.5 text-[10.5px] font-semibold ${
                    u.role === "admin" ? "bg-gold-soft text-gold" : "bg-navy-soft text-navy"
                  }`}>
                    {u.role === "admin" ? "Administrador" : "Profissional"}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
        <div>
          <SectionTitle>Benchmarks disponíveis</SectionTitle>
          <Card className="p-4">
            <div className="divide-y divide-hairline">
              {s.benchmarks.map((b) => (
                <div key={b.name} className="flex items-center justify-between py-2.5">
                  <span className="text-[13px] font-medium text-ink">{b.name}</span>
                  <span className="text-[11px] text-faint">{b.global ? "preset global" : "da organização"}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 border-t border-hairline pt-2.5 text-[11px] leading-relaxed text-faint">
              Benchmarks personalizados (IPCA+X%, carteira própria) entram na próxima versão — a
              estrutura já está pronta no modelo de dados.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
