import { sql } from "./db";

export type MeetingRow = {
  id: string;
  scheduled_for: string;
  status: string;
  family: string;
  family_id: string;
  wealth: string;
  material_sent_at: string | null;
  insights: { severity: string }[] | null;
};

export async function getMeetings(orgId: string): Promise<MeetingRow[]> {
  return (await sql`
    select m.id, m.scheduled_for, m.status, f.display_name as family, f.id as family_id,
           m.material_sent_at,
           coalesce((select sum(ps.value) from core.position_snapshots ps
                     join core.accounts a on a.id = ps.account_id
                     where a.family_id = f.id), 0)::text as wealth,
           r.outputs->'outputs'->'insights' as insights
    from core.meetings m
    join core.families f on f.id = m.family_id
    left join core.analysis_runs r on r.id = m.analysis_run_id
    where m.org_id = ${orgId} and m.status <> 'cancelled'
    order by m.scheduled_for asc
  `) as unknown as MeetingRow[];
}

export type PositionRow = {
  name: string;
  kind: string;
  index_kind: string;
  maturity: string | null;
  issuer: string;
  holder: string | null;
  value: string;
  confidence: string;
  category: string | null;
};

export type MeetingDetail = {
  id: string;
  scheduled_for: string;
  status: string;
  family: string;
  run: {
    short: string;
    engine_version: string;
    policy_version: number;
    created_at: string;
    outputs: Record<string, unknown>;
  } | null;
  positions: PositionRow[];
};

export async function getMeetingDetail(orgId: string, meetingId: string): Promise<MeetingDetail | null> {
  const rows = await sql`
    select m.id, m.scheduled_for, m.status, f.display_name as family, f.id as family_id,
           r.outputs, r.engine_version, r.created_at as run_created_at,
           substring(r.run_hash, 1, 16) as run_short,
           p.version as policy_version
    from core.meetings m
    join core.families f on f.id = m.family_id
    left join core.analysis_runs r on r.id = m.analysis_run_id
    left join core.organization_policies p on p.id = r.policy_id
    where m.org_id = ${orgId} and m.id = ${meetingId}
  `;
  if (!rows.length) return null;
  const m = rows[0];

  const positions = (await sql`
    select i.name, i.kind, i.index_kind, i.maturity::text as maturity,
           coalesce(iss.name, '—') as issuer, h.display_name as holder,
           ps.value::text as value, ps.confidence,
           i.identifiers->>'category' as category
    from core.position_snapshots ps
    join core.accounts a on a.id = ps.account_id
    join core.instruments i on i.id = ps.instrument_id
    left join core.issuers iss on iss.id = i.issuer_id
    left join core.holders h on h.id = a.holder_id
    where a.family_id = ${m.family_id}
    order by ps.value desc
  `) as unknown as PositionRow[];

  return {
    id: m.id,
    scheduled_for: m.scheduled_for,
    status: m.status,
    family: m.family,
    run: m.outputs
      ? {
          short: m.run_short,
          engine_version: m.engine_version,
          policy_version: m.policy_version ?? 1,
          created_at: m.run_created_at,
          outputs: (m.outputs as { outputs?: Record<string, unknown> }).outputs ?? (m.outputs as Record<string, unknown>),
        }
      : null,
    positions,
  };
}

export type PendingDocument = {
  id: string;
  family: string;
  family_id: string;
  kind: string;
  status: string;
  created_at: string;
  n_positions: number;
  total_value: string;
  reconciled: boolean;
};

export async function getPendingExtractionCount(orgId: string): Promise<number> {
  const rows = await sql`
    select count(*)::int as n from core.source_documents
    where org_id = ${orgId} and status = 'awaiting_confirmation'
  `;
  return rows[0]?.n ?? 0;
}

export async function getPendingExtractions(orgId: string): Promise<PendingDocument[]> {
  const rows = await sql`
    select d.id, d.kind, d.status, d.created_at, f.display_name as family, f.id as family_id,
           eb.raw_output, eb.diffs
    from core.source_documents d
    join core.families f on f.id = d.family_id
    join core.extraction_batches eb on eb.source_document_id = d.id
    where d.org_id = ${orgId} and d.status = 'awaiting_confirmation'
    order by d.created_at asc
  `;
  return rows.map((r) => {
    const positions = (r.raw_output as { positions: { value: string }[] }).positions;
    return {
      id: r.id,
      family: r.family,
      family_id: r.family_id,
      kind: r.kind,
      status: r.status,
      created_at: r.created_at,
      n_positions: positions.length,
      total_value: positions.reduce((acc, p) => acc + Number(p.value), 0).toFixed(2),
      reconciled: (r.diffs as { reconciled: boolean }).reconciled,
    };
  });
}

export type ExtractionPosition = {
  name: string; kind: string; issuer: string; value: string; confidence: string;
  index_kind?: string; valuation_mode?: string; category?: string; note?: string;
  contract_terms?: Record<string, string>;
};

export type ExtractionDetail = {
  id: string;
  family: string;
  familyId: string;
  storagePath: string;
  status: string;
  conta: string;
  perfil: string;
  custodiante: string;
  referenceDate: string;
  declaredTotal: string;
  sumOfPositions: string;
  reconciled: boolean;
  accountId: string;
  holderId: string;
  positions: ExtractionPosition[];
};

export async function getExtractionDetail(orgId: string, documentId: string): Promise<ExtractionDetail | null> {
  const rows = await sql`
    select d.id, d.storage_path, d.status, f.display_name as family, f.id as family_id,
           eb.raw_output, eb.diffs
    from core.source_documents d
    join core.families f on f.id = d.family_id
    join core.extraction_batches eb on eb.source_document_id = d.id
    where d.org_id = ${orgId} and d.id = ${documentId}
  `;
  if (!rows.length) return null;
  const r = rows[0];
  const raw = r.raw_output as {
    conta: string; perfil: string; custodiante: string; reference_date: string;
    patrimonio_total_declarado: string; account_id: string; holder_id: string;
    positions: ExtractionPosition[];
  };
  const diffs = r.diffs as { sum_of_positions: string; reconciled: boolean };
  return {
    id: r.id,
    family: r.family,
    familyId: r.family_id,
    storagePath: r.storage_path,
    status: r.status,
    conta: raw.conta,
    perfil: raw.perfil,
    custodiante: raw.custodiante,
    referenceDate: raw.reference_date,
    declaredTotal: raw.patrimonio_total_declarado,
    sumOfPositions: diffs.sum_of_positions,
    reconciled: diffs.reconciled,
    accountId: raw.account_id,
    holderId: raw.holder_id,
    positions: raw.positions,
  };
}

export type ManagerCard = {
  name: string;
  jurisdiction: string;
  period_end: string;
  source_url: string | null;
  holdings: { rank: number; issuer_name: string; instrument: string | null; pct_of_total: string; change_kind: string | null }[];
};

export async function getRadar(): Promise<ManagerCard[]> {
  const rows = await sql`
    select mg.name, mg.jurisdiction, mf.period_end::text as period_end, mf.source_url,
           mh.rank, mh.issuer_name, mh.instrument, mh.pct_of_total::text as pct_of_total, mh.change_kind
    from market.managers mg
    join lateral (
      select * from market.manager_filings f where f.manager_id = mg.id
      order by f.period_end desc limit 1
    ) mf on true
    join market.manager_holdings mh on mh.filing_id = mf.id
    where mh.rank <= 6
    order by mg.jurisdiction, mg.name, mh.rank
  `;
  const byManager = new Map<string, ManagerCard>();
  for (const r of rows) {
    const card: ManagerCard = byManager.get(r.name) ?? {
      name: r.name,
      jurisdiction: r.jurisdiction,
      period_end: r.period_end,
      source_url: r.source_url,
      holdings: [],
    };
    card.holdings.push({
      rank: r.rank,
      issuer_name: r.issuer_name,
      instrument: r.instrument,
      pct_of_total: r.pct_of_total,
      change_kind: r.change_kind,
    });
    byManager.set(r.name, card);
  }
  return [...byManager.values()];
}

export type FamilyRow = {
  id: string;
  display_name: string;
  wealth: string;
  n_positions: number;
  holders: string | null;
  benchmark: string | null;
  next_meeting_id: string | null;
  next_meeting_at: string | null;
  next_meeting_status: string | null;
  pending_docs: number;
  worst_confidence: string | null;
};

export async function getFamilies(orgId: string): Promise<FamilyRow[]> {
  return (await sql`
    select f.id, f.display_name,
           coalesce((select sum(ps.value) from core.position_snapshots ps
                     join core.accounts a on a.id = ps.account_id where a.family_id = f.id), 0)::text as wealth,
           coalesce((select count(*) from core.position_snapshots ps
                     join core.accounts a on a.id = ps.account_id where a.family_id = f.id), 0)::int as n_positions,
           (select string_agg(h.display_name, ' · ' order by h.display_name)
              from core.holders h where h.family_id = f.id) as holders,
           b.name as benchmark,
           m.id as next_meeting_id, m.scheduled_for::text as next_meeting_at, m.status as next_meeting_status,
           (select count(*) from core.source_documents d
             where d.family_id = f.id and d.status = 'awaiting_confirmation')::int as pending_docs,
           (select max(ps.confidence) from core.position_snapshots ps
              join core.accounts a on a.id = ps.account_id where a.family_id = f.id) as worst_confidence
    from core.families f
    left join core.benchmarks b on b.id = f.benchmark_id
    left join lateral (
      select id, scheduled_for, status from core.meetings mm
      where mm.family_id = f.id and mm.status not in ('held','cancelled')
      order by mm.scheduled_for asc limit 1
    ) m on true
    where f.org_id = ${orgId} and f.is_active
    order by 3 desc
  `) as unknown as FamilyRow[];
}

export type OrgSettings = {
  org: { name: string; slug: string; created_at: string };
  policy: {
    version: number;
    effective_from: string;
    issuer_concentration_limit_pct: string;
    fgc_limit: string;
    maturity_window_days: number;
    min_vol_observations: number;
    ai_interaction_retention_days: number | null;
  };
  policyHistory: { version: number; effective_from: string; created_by_name: string | null }[];
  team: { name: string; email: string; role: string }[];
  benchmarks: { name: string; kind: string; global: boolean }[];
};

export async function getOrgSettings(orgId: string): Promise<OrgSettings> {
  const org = (await sql`
    select name, slug, created_at::text as created_at from core.organizations where id = ${orgId}
  `)[0] as OrgSettings["org"];
  const policy = (await sql`
    select version, effective_from::text as effective_from,
           issuer_concentration_limit_pct::text as issuer_concentration_limit_pct,
           fgc_limit::text as fgc_limit, maturity_window_days, min_vol_observations,
           ai_interaction_retention_days
    from core.organization_policies where org_id = ${orgId}
    order by version desc limit 1
  `)[0] as OrgSettings["policy"];
  const policyHistory = (await sql`
    select p.version, p.effective_from::text as effective_from, u.name as created_by_name
    from core.organization_policies p
    left join core.app_users u on u.id = p.created_by
    where p.org_id = ${orgId} order by p.version desc
  `) as unknown as OrgSettings["policyHistory"];
  const team = (await sql`
    select name, email, role from core.app_users where org_id = ${orgId} and is_active order by role, name
  `) as unknown as OrgSettings["team"];
  const benchmarks = (await sql`
    select name, kind, (org_id is null) as global from core.benchmarks
    where org_id is null or org_id = ${orgId} order by org_id nulls first, name
  `) as unknown as OrgSettings["benchmarks"];
  return { org, policy, policyHistory, team, benchmarks };
}

export type AuditRow = {
  id: string;
  kind: string;
  actor_name: string | null;
  entity_type: string | null;
  entity_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export async function getAuditEvents(orgId: string, kind?: string): Promise<AuditRow[]> {
  if (kind) {
    return (await sql`
      select e.id, e.kind::text as kind, u.name as actor_name, e.entity_type, e.entity_id::text as entity_id,
             e.payload, e.created_at::text as created_at
      from audit.events e
      left join core.app_users u on u.id = e.actor_id
      where e.org_id = ${orgId} and e.kind::text = ${kind}
      order by e.created_at desc limit 100
    `) as unknown as AuditRow[];
  }
  return (await sql`
    select e.id, e.kind::text as kind, u.name as actor_name, e.entity_type, e.entity_id::text as entity_id,
           e.payload, e.created_at::text as created_at
    from audit.events e
    left join core.app_users u on u.id = e.actor_id
    where e.org_id = ${orgId}
    order by e.created_at desc limit 100
  `) as unknown as AuditRow[];
}
