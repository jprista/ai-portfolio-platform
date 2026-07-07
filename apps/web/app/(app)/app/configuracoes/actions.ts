"use server";

import { revalidatePath } from "next/cache";
import { sql } from "@/lib/db";
import { requireOrg } from "@/lib/auth";

/** Políticas são IMUTÁVEIS (I2): salvar cria uma nova versão — cada análise
 * futura referencia a versão vigente no momento em que rodou. */
export async function savePolicyVersion(formData: FormData) {
  const { orgId, userId } = await requireOrg();
  const professional = await sql`select id from core.app_users where auth_external_id = ${userId}`;
  const professionalId: string | null = professional[0]?.id ?? null;

  const issuerLimit = String(formData.get("issuer_limit") ?? "15").replace(",", ".");
  const fgcLimit = String(formData.get("fgc_limit") ?? "250000").replace(/\./g, "").replace(",", ".");
  const maturityDays = parseInt(String(formData.get("maturity_days") ?? "90"), 10);
  const minVolObs = parseInt(String(formData.get("min_vol_obs") ?? "12"), 10);
  const retentionRaw = String(formData.get("ai_retention_days") ?? "").trim();
  const retention = retentionRaw ? parseInt(retentionRaw, 10) : null;

  if (Number.isNaN(maturityDays) || Number.isNaN(minVolObs) || Number(issuerLimit) <= 0 || Number(fgcLimit) <= 0) {
    throw new Error("VALIDATION_FAILED: valores inválidos na política");
  }

  const newVersion = await sql`
    insert into core.organization_policies
      (org_id, version, issuer_concentration_limit_pct, fgc_limit, maturity_window_days,
       min_vol_observations, ai_interaction_retention_days, created_by)
    select ${orgId}, coalesce(max(version), 0) + 1, ${issuerLimit}, ${fgcLimit}, ${maturityDays},
           ${minVolObs}, ${retention}, ${professionalId}
    from core.organization_policies where org_id = ${orgId}
    returning version
  `;

  await sql`
    insert into audit.events (org_id, actor_id, kind, entity_type, entity_id, payload)
    values (${orgId}, ${professionalId}, 'policy_changed', 'organization_policy', null,
            ${sql.json({
              new_version: newVersion[0].version,
              issuer_concentration_limit_pct: issuerLimit,
              fgc_limit: fgcLimit,
              maturity_window_days: maturityDays,
              min_vol_observations: minVolObs,
              ai_interaction_retention_days: retention,
            })})
  `;

  revalidatePath("/app/configuracoes");
}
