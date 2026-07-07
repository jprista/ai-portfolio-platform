"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { sql } from "@/lib/db";
import { requireOrg } from "@/lib/auth";

const REQUIRED_FIELDS: Record<string, string[]> = {
  cdb: ["aplicacao", "vencimento"],
  lca: ["aplicacao", "vencimento", "index_pct"],
  lci: ["aplicacao", "vencimento", "index_pct"],
  debenture: ["aplicacao", "vencimento", "taxa_contratada"],
};

type ExtractionPosition = {
  name: string; kind: string; issuer: string; value: string; confidence: string;
  index_kind?: string; valuation_mode?: string; category?: string;
  contract_terms?: Record<string, string>;
};

/** Nada entra no motor sem confirmação humana (MVP_SCOPE §3.1). Escreve
 * position_snapshots reais, aciona o motor (services/engine) e cria/atualiza
 * o AnalysisRun da família — fechando o ciclo extração -> análise. */
export async function confirmExtraction(documentId: string, formData: FormData) {
  const { orgId, userId } = await requireOrg();

  const doc = await sql`
    select d.id, d.family_id, d.status, eb.id as batch_id, eb.raw_output
    from core.source_documents d
    join core.extraction_batches eb on eb.source_document_id = d.id
    where d.org_id = ${orgId} and d.id = ${documentId} and d.status = 'awaiting_confirmation'
  `;
  if (!doc.length) throw new Error("EXTRACTION_UNCONFIRMED: documento não encontrado ou já processado");

  const raw = doc[0].raw_output as {
    account_id: string; reference_date: string; positions: ExtractionPosition[];
  };
  const familyId = doc[0].family_id as string;
  const accountId = raw.account_id;
  const asOf = raw.reference_date;

  // formData carrega os valores (possivelmente corrigidos) por índice de posição
  const positions = raw.positions.map((p, i) => ({
    ...p,
    value: (formData.get(`value_${i}`) as string) || p.value,
  }));

  const professionalUser = await sql`select id from core.app_users where auth_external_id = ${userId}`;
  const professionalId: string | null = professionalUser[0]?.id ?? null;

  await sql.begin(async (tx) => {
    // remove qualquer posição agregada informada anteriormente (placeholder pré-confirmação)
    await tx`
      delete from core.position_snapshots ps
      using core.accounts a
      where ps.account_id = a.id and a.family_id = ${familyId}
    `;

    for (const p of positions) {
      const issuer = await tx`
        insert into core.issuers (name, kind)
        values (${p.issuer}, ${p.kind === "tesouro" ? "sovereign" : p.kind === "cdb" || p.kind === "lca" || p.kind === "lci" ? "bank" : "asset_manager"})
        on conflict do nothing
        returning id
      `;
      let issuerId: string;
      if (issuer.length) {
        issuerId = issuer[0].id;
      } else {
        issuerId = (await tx`select id from core.issuers where name = ${p.issuer} limit 1`)[0].id;
      }

      const identifiers = p.category ? { category: p.category } : {};
      const existingInst = await tx`
        select id from core.instruments
        where kind = ${p.kind} and name = ${p.name}
      `;
      let instrumentId: string;
      if (existingInst.length) {
        instrumentId = existingInst[0].id;
      } else {
        const maturity = p.contract_terms?.vencimento ?? null;
        const inst = await tx`
          insert into core.instruments (kind, name, issuer_id, index_kind, identifiers, maturity)
          values (${p.kind}, ${p.name}, ${issuerId}, ${p.index_kind ?? "none"}, ${tx.json(identifiers)}, ${maturity})
          returning id
        `;
        instrumentId = inst[0].id;
      }

      const missing = (REQUIRED_FIELDS[p.kind] ?? []).filter((f) => !p.contract_terms?.[f]);

      await tx`
        insert into core.position_snapshots
          (org_id, account_id, instrument_id, as_of, value, source, confidence,
           valuation_mode, contract_terms, missing_contract_fields, contract_terms_origin)
        values (${orgId}, ${accountId}, ${instrumentId}, ${asOf}, ${p.value}, 'document', ${p.confidence},
                ${p.valuation_mode ?? "curve"}, ${tx.json(p.contract_terms ?? {})},
                ${missing}, 'statement')
        on conflict (org_id, account_id, instrument_id, as_of)
        do update set value = excluded.value
      `;
    }

    await tx`
      update core.extraction_batches
      set status = 'confirmed', confirmed_by = ${professionalId}, confirmed_at = now()
      where id = ${doc[0].batch_id}
    `;
    await tx`update core.source_documents set status = 'confirmed' where id = ${documentId}`;
    await tx`
      insert into audit.events (org_id, actor_id, kind, entity_type, entity_id, payload)
      values (${orgId}, ${professionalId}, 'extraction_confirmed', 'source_document', ${documentId},
              ${tx.json({ n_positions: positions.length, family_id: familyId })})
    `;
  });

  // dispara o motor real (services/engine) sobre as posições recem-confirmadas
  const enginePositions = positions.map((p) => ({
    name: p.name, asset_class: p.category ?? guessClass(p),
    issuer: p.issuer, value: p.value, liquidity: "D+2", confidence: p.confidence,
    fund_fee_pct: null,
  }));

  let policyId: string;
  const policy = await sql`select id from core.organization_policies where org_id = ${orgId} and version = 1`;
  policyId = policy[0].id;

  let outputs: Record<string, unknown> = { total_value: "0", allocation: {}, insights: [], declared_limitations: [] };
  try {
    const res = await fetch(`${process.env.ENGINE_URL}/engine/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reference_date: asOf,
        positions: enginePositions,
        history: { valuations: [], flows: [] },
      }),
      cache: "no-store",
    });
    if (res.ok) {
      const run = await res.json();
      outputs = run.outputs;
    }
  } catch {
    // motor indisponível — a confirmação dos dados já foi persistida; a análise pode ser gerada depois
  }

  const runHash = `confirm-${documentId}-${Date.now()}`;
  const runId = (
    await sql`
      insert into core.analysis_runs (org_id, family_id, run_hash, engine_version, policy_id, input_snapshot_ref, outputs)
      values (${orgId}, ${familyId}, ${runHash}, '0.2.0-prototype', ${policyId}, ${`document:${documentId}`}, ${sql.json(outputs as never)})
      returning id
    `
  )[0].id;

  // vincula à próxima reunião da família (cria uma se não houver nenhuma agendada)
  const meeting = await sql`
    select id from core.meetings where org_id = ${orgId} and family_id = ${familyId}
    and status not in ('held','cancelled') order by scheduled_for asc limit 1
  `;
  if (meeting.length) {
    await sql`
      update core.meetings set analysis_run_id = ${runId}, status = 'preparing'
      where id = ${meeting[0].id}
    `;
  } else {
    const inAWeek = new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString();
    await sql`
      insert into core.meetings (org_id, family_id, professional_id, scheduled_for, status, analysis_run_id)
      values (${orgId}, ${familyId}, ${professionalId}, ${inAWeek}, 'preparing', ${runId})
    `;
  }

  revalidatePath("/app");
  revalidatePath("/app/caixa-de-confirmacao");
  redirect("/app/caixa-de-confirmacao");
}

export async function rejectExtraction(documentId: string) {
  const { orgId, userId } = await requireOrg();
  const professionalUser = await sql`select id from core.app_users where auth_external_id = ${userId}`;
  const professionalId: string | null = professionalUser[0]?.id ?? null;

  const doc = await sql`
    select eb.id as batch_id from core.source_documents d
    join core.extraction_batches eb on eb.source_document_id = d.id
    where d.org_id = ${orgId} and d.id = ${documentId}
  `;
  if (!doc.length) throw new Error("documento não encontrado");

  await sql.begin(async (tx) => {
    await tx`update core.extraction_batches set status = 'rejected' where id = ${doc[0].batch_id}`;
    await tx`update core.source_documents set status = 'rejected' where id = ${documentId}`;
    await tx`
      insert into audit.events (org_id, actor_id, kind, entity_type, entity_id, payload)
      values (${orgId}, ${professionalId}, 'extraction_confirmed', 'source_document', ${documentId}, '{"decision":"rejected"}'::jsonb)
    `;
  });

  revalidatePath("/app/caixa-de-confirmacao");
  redirect("/app/caixa-de-confirmacao");
}

function guessClass(p: ExtractionPosition): string {
  if (p.kind === "pension_fund") return "previdencia";
  if (["equity", "etf", "fii", "bdr"].includes(p.kind)) return "renda_variavel";
  if (p.index_kind === "ipca_plus") return "renda_fixa_inflacao";
  if (p.kind === "cash") return "caixa";
  return "renda_fixa_pos";
}
