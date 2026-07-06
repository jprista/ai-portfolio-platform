-- ============================================================================
-- 0003_consensus_radar.sql — implements CONSENSUS_RADAR.md v1.0 (radar tables)
-- Global market intelligence from PUBLIC regulatory sources (SEC 13F, CVM CDA).
-- Market schema: no tenant, read-only for the app.
-- ============================================================================

begin;

create table market.managers (
    id           uuid primary key default gen_random_uuid(),
    name         text not null,
    jurisdiction text not null,             -- 'US' | 'BR'
    source       text not null,             -- 'sec_13f' | 'cvm_cda'
    external_ref text not null,             -- CIK (SEC) ou CNPJ (CVM)
    created_at   timestamptz not null default now(),
    unique (source, external_ref)
);

create table market.manager_filings (
    id           uuid primary key default gen_random_uuid(),
    manager_id   uuid not null references market.managers(id),
    period_end   date not null,
    filed_at     date,
    source_url   text,
    total_value  numeric(20,2),
    captured_at  timestamptz not null default now(),
    unique (manager_id, period_end)
);

create table market.manager_holdings (
    filing_id    uuid not null references market.manager_filings(id),
    rank         integer not null,
    issuer_name  text not null,
    instrument   text,                      -- ticker/classe quando identificável
    value        numeric(20,2) not null,
    pct_of_total numeric(8,4),
    change_kind  text,                      -- 'new' | 'increased' | 'reduced' | 'unchanged' | null
    primary key (filing_id, rank)
);

commit;
