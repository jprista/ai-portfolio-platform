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
           ps.value::text as value, ps.confidence
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

export type ManagerCard = {
  name: string;
  period_end: string;
  source_url: string | null;
  holdings: { rank: number; issuer_name: string; pct_of_total: string; change_kind: string | null }[];
};

export async function getRadar(): Promise<ManagerCard[]> {
  const rows = await sql`
    select mg.name, mf.period_end::text as period_end, mf.source_url,
           mh.rank, mh.issuer_name, mh.pct_of_total::text as pct_of_total, mh.change_kind
    from market.managers mg
    join lateral (
      select * from market.manager_filings f where f.manager_id = mg.id
      order by f.period_end desc limit 1
    ) mf on true
    join market.manager_holdings mh on mh.filing_id = mf.id
    where mh.rank <= 6
    order by mg.name, mh.rank
  `;
  const byManager = new Map<string, ManagerCard>();
  for (const r of rows) {
    const card: ManagerCard = byManager.get(r.name) ?? {
      name: r.name,
      period_end: r.period_end,
      source_url: r.source_url,
      holdings: [],
    };
    card.holdings.push({
      rank: r.rank,
      issuer_name: r.issuer_name,
      pct_of_total: r.pct_of_total,
      change_kind: r.change_kind,
    });
    byManager.set(r.name, card);
  }
  return [...byManager.values()];
}
