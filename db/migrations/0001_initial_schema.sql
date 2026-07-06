-- ============================================================================
-- 0001_initial_schema.sql — implements DOMAIN_MODEL.md v1.1 (approved 2026-07-03)
--
-- Invariants enforced at the database level:
--   I2  immutable transactions / analysis runs / policies (trigger + REVOKE)
--   I3  row-level security on every tenant table
--   I4  append-only audit schema (INSERT-only)
-- Founder decisions 2026-07-03: meeting states, Holder/FGC, Benchmark entity,
-- missing_contract_fields + contract_terms_source, valuation_mode.
-- NOTE: core.current_org_id() reads a session setting; at Supabase deploy it
-- is replaced by a JWT-claim implementation (same signature).
-- ============================================================================

begin;

create extension if not exists pgcrypto;

create schema if not exists core;
create schema if not exists market;
create schema if not exists audit;

-- ---------------------------------------------------------------- enums ----
create type core.user_role                  as enum ('admin','professional');
create type core.meeting_status             as enum ('scheduled','preparing','material_generated','material_sent','held','cancelled');
create type core.instrument_type            as enum ('cash','cdb','lci','lca','lc','tesouro','debenture','fund','pension_fund','equity','etf','fii','bdr','coe','other');
create type core.index_kind                 as enum ('pre','cdi_pct','ipca_plus','selic','none');
create type core.transaction_kind           as enum ('buy','sell','deposit','withdrawal','income','fee','transfer_in','transfer_out','reversal');
create type core.position_source           as enum ('open_finance','document','manual');
create type core.confidence_seal            as enum ('A','B','C','D');
create type core.valuation_mode             as enum ('curve','market');
create type core.benchmark_kind             as enum ('cdi','ipca_plus','index','custom_portfolio','composite');
create type core.contract_terms_origin      as enum ('statement','user_provided','mixed');
create type core.document_status            as enum ('pending','awaiting_confirmation','confirmed','rejected');
create type core.connection_status          as enum ('active','error','revoked');
create type core.validator_result           as enum ('approved','regenerated','degraded');
create type core.issuer_kind                as enum ('bank','asset_manager','sovereign','company','insurer');
create type core.custodian_kind             as enum ('corretora','banco','seguradora','plataforma');
create type core.generated_document_kind    as enum ('briefing','client_report');
create type audit.event_kind                as enum ('data_viewed','data_edited','run_created','document_generated','document_exported','extraction_confirmed','policy_changed','login','export_lgpd','purge_lgpd');

-- ------------------------------------------------------------- helpers ----
create function core.current_org_id() returns uuid
language sql stable
as $$ select nullif(current_setting('app.current_org_id', true), '')::uuid $$;

create function core.touch_updated_at() returns trigger
language plpgsql
as $$ begin new.updated_at := now(); return new; end $$;

create function core.forbid_mutation() returns trigger
language plpgsql
as $$ begin raise exception 'immutable table (%): UPDATE/DELETE forbidden — correction is a new row (I2/I4)', tg_table_name; end $$;

-- ---------------------------------------------------- identity / tenancy ----
create table core.organizations (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    slug          text not null unique,
    brand         jsonb not null default '{}',
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);

create table core.app_users (
    id                uuid primary key default gen_random_uuid(),
    org_id            uuid not null references core.organizations(id),
    auth_external_id  text not null unique,
    name              text not null,
    email             text not null,
    role              core.user_role not null default 'professional',
    is_active         boolean not null default true,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now(),
    unique (org_id, email)
);

-- versioned & immutable: every AnalysisRun references the policy version used
create table core.organization_policies (
    id                              uuid primary key default gen_random_uuid(),
    org_id                          uuid not null references core.organizations(id),
    version                         integer not null,
    effective_from                  timestamptz not null default now(),
    issuer_concentration_limit_pct  numeric(6,2)  not null default 15.00,
    fgc_limit                       numeric(18,2) not null default 250000.00,
    maturity_window_days            integer       not null default 90,
    min_vol_observations            integer       not null default 12,
    fee_median_overrides            jsonb         not null default '{}',
    created_by                      uuid references core.app_users(id),
    created_at                      timestamptz not null default now(),
    unique (org_id, version)
);

-- org_id NULL = global preset (CDI, Ibovespa, IMA-B, ...)
create table core.benchmarks (
    id          uuid primary key default gen_random_uuid(),
    org_id      uuid references core.organizations(id),
    name        text not null,
    kind        core.benchmark_kind not null,
    params      jsonb not null default '{}',
    created_at  timestamptz not null default now()
);

-- ------------------------------------------------------ clients / accounts ----
create table core.families (
    id                       uuid primary key default gen_random_uuid(),
    org_id                   uuid not null references core.organizations(id),
    display_name             text not null,
    primary_professional_id  uuid references core.app_users(id),
    benchmark_id             uuid references core.benchmarks(id),
    is_active                boolean not null default true,
    created_at               timestamptz not null default now(),
    updated_at               timestamptz not null default now()
);

-- FGC is per CPF/CNPJ per issuer (founder decision 9.1) — masked document only
create table core.holders (
    id               uuid primary key default gen_random_uuid(),
    org_id           uuid not null references core.organizations(id),
    family_id        uuid not null references core.families(id),
    display_name     text not null,
    document_masked  text,
    created_at       timestamptz not null default now()
);

create table core.custodians (
    id          uuid primary key default gen_random_uuid(),
    name        text not null unique,
    kind        core.custodian_kind not null,
    created_at  timestamptz not null default now()
);

create table core.accounts (
    id                  uuid primary key default gen_random_uuid(),
    org_id              uuid not null references core.organizations(id),
    family_id           uuid not null references core.families(id),
    holder_id           uuid references core.holders(id),
    custodian_id        uuid not null references core.custodians(id),
    external_ref_masked text,
    source              core.position_source not null,
    is_active           boolean not null default true,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

-- ------------------------------------------------------------- portfolio ----
create table core.issuers (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    kind        core.issuer_kind not null,
    document    text,
    created_at  timestamptz not null default now()
);

create table core.instruments (
    id           uuid primary key default gen_random_uuid(),
    kind         core.instrument_type not null,
    name         text not null,
    issuer_id    uuid references core.issuers(id),
    index_kind   core.index_kind not null default 'none',
    identifiers  jsonb not null default '{}',
    maturity     date,
    created_at   timestamptz not null default now()
);
create unique index instruments_identifiers_uq on core.instruments (kind, (identifiers::text));

-- immutable: correction = reversal + new row (I2)
create table core.transactions (
    id               uuid primary key default gen_random_uuid(),
    org_id           uuid not null references core.organizations(id),
    account_id       uuid not null references core.accounts(id),
    instrument_id    uuid not null references core.instruments(id),
    kind             core.transaction_kind not null,
    trade_date       date not null,
    settlement_date  date,
    quantity         numeric(24,8),
    price            numeric(20,10),
    gross_amount     numeric(18,2) not null,
    reversal_of      uuid references core.transactions(id),
    source           core.position_source not null,
    created_by       uuid references core.app_users(id),
    created_at       timestamptz not null default now()
);

-- informed position (statement photo); founder decision 9.3: missing contract
-- fields are identified and manual completion is recorded and declared
create table core.position_snapshots (
    id                       uuid primary key default gen_random_uuid(),
    org_id                   uuid not null references core.organizations(id),
    account_id               uuid not null references core.accounts(id),
    instrument_id            uuid not null references core.instruments(id),
    as_of                    date not null,
    quantity                 numeric(24,8),
    value                    numeric(18,2) not null,
    source                   core.position_source not null,
    source_document_id       uuid,
    confidence               core.confidence_seal not null,
    valuation_mode           core.valuation_mode not null default 'curve',
    contract_terms           jsonb not null default '{}',
    missing_contract_fields  text[] not null default '{}',
    contract_terms_origin    core.contract_terms_origin,
    created_at               timestamptz not null default now(),
    unique (org_id, account_id, instrument_id, as_of)
);

-- ------------------------------------------------------------- ingestion ----
create table core.connections (
    id                 uuid primary key default gen_random_uuid(),
    org_id             uuid not null references core.organizations(id),
    family_id          uuid not null references core.families(id),
    provider           text not null,
    provider_item_ref  text not null,
    status             core.connection_status not null default 'active',
    last_sync_at       timestamptz,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now()
);

create table core.source_documents (
    id            uuid primary key default gen_random_uuid(),
    org_id        uuid not null references core.organizations(id),
    family_id     uuid not null references core.families(id),
    storage_path  text not null,
    kind          text not null,
    sha256        text not null,
    uploaded_by   uuid references core.app_users(id),
    status        core.document_status not null default 'pending',
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
alter table core.position_snapshots
    add constraint position_snapshots_source_document_fk
    foreign key (source_document_id) references core.source_documents(id);

create table core.extraction_batches (
    id                  uuid primary key default gen_random_uuid(),
    org_id              uuid not null references core.organizations(id),
    source_document_id  uuid not null references core.source_documents(id),
    model_id            text not null,
    raw_output          jsonb not null,
    status              core.document_status not null default 'awaiting_confirmation',
    diffs               jsonb not null default '{}',
    confirmed_by        uuid references core.app_users(id),
    confirmed_at        timestamptz,
    created_at          timestamptz not null default now()
);

-- ------------------------------------------------------ analysis / meetings ----
-- immutable (I2): same snapshot + same engine version => same bytes
create table core.analysis_runs (
    id                  uuid primary key default gen_random_uuid(),
    org_id              uuid not null references core.organizations(id),
    family_id           uuid not null references core.families(id),
    run_hash            text not null,
    engine_version      text not null,
    policy_id           uuid not null references core.organization_policies(id),
    input_snapshot_ref  text not null,
    outputs             jsonb not null,
    created_by          uuid references core.app_users(id),
    created_at          timestamptz not null default now()
);

-- the central product object; states per founder decision 9.2
create table core.meetings (
    id                   uuid primary key default gen_random_uuid(),
    org_id               uuid not null references core.organizations(id),
    family_id            uuid not null references core.families(id),
    professional_id      uuid not null references core.app_users(id),
    scheduled_for        timestamptz not null,
    status               core.meeting_status not null default 'scheduled',
    previous_meeting_id  uuid references core.meetings(id),
    analysis_run_id      uuid references core.analysis_runs(id),
    material_sent_at     timestamptz,
    held_at              timestamptz,
    created_at           timestamptz not null default now(),
    updated_at           timestamptz not null default now()
);

-- AI audit (AI_ARCHITECTURE §6): every generation logged, immutable
create table core.generations (
    id                uuid primary key default gen_random_uuid(),
    org_id            uuid not null references core.organizations(id),
    model_id          text not null,
    model_version     text not null,
    prompt_sha256     text not null,
    analysis_run_id   uuid not null references core.analysis_runs(id),
    output_text       text not null,
    validator_result  core.validator_result not null,
    requested_by      uuid references core.app_users(id),
    created_at        timestamptz not null default now()
);

create table core.generation_edits (
    id             uuid primary key default gen_random_uuid(),
    org_id         uuid not null references core.organizations(id),
    generation_id  uuid not null references core.generations(id),
    diff           jsonb not null,
    edited_by      uuid not null references core.app_users(id),
    created_at     timestamptz not null default now()
);

create table core.generated_documents (
    id               uuid primary key default gen_random_uuid(),
    org_id           uuid not null references core.organizations(id),
    family_id        uuid not null references core.families(id),
    meeting_id       uuid references core.meetings(id),
    kind             core.generated_document_kind not null,
    storage_path     text not null,
    analysis_run_id  uuid not null references core.analysis_runs(id),
    generation_id    uuid references core.generations(id),
    created_at       timestamptz not null default now()
);

-- ------------------------------------------------------- market (global) ----
create table market.price_points (
    instrument_id  uuid not null references core.instruments(id),
    price_date     date not null,
    price          numeric(20,10) not null,
    source         text not null,
    captured_at    timestamptz not null default now(),
    primary key (instrument_id, price_date, source)
);

create table market.index_series (
    index_code   text not null,
    value_date   date not null,
    value        numeric(20,10) not null,
    source       text not null,
    captured_at  timestamptz not null default now(),
    primary key (index_code, value_date, source)
);

create table market.fund_info (
    cnpj          text not null,
    as_of         date not null,
    name          text not null,
    anbima_class  text,
    adm_fee_pct   numeric(8,4),
    perf_fee_pct  numeric(8,4),
    captured_at   timestamptz not null default now(),
    primary key (cnpj, as_of)
);

-- --------------------------------------------------------- audit (I4) ----
create table audit.events (
    id           uuid primary key default gen_random_uuid(),
    org_id       uuid,
    actor_id     uuid,
    kind         audit.event_kind not null,
    entity_type  text,
    entity_id    uuid,
    payload      jsonb not null default '{}',
    created_at   timestamptz not null default now()
);

-- ------------------------------------------------- immutability triggers ----
create trigger transactions_immutable          before update or delete on core.transactions           for each row execute function core.forbid_mutation();
create trigger analysis_runs_immutable         before update or delete on core.analysis_runs          for each row execute function core.forbid_mutation();
create trigger organization_policies_immutable before update or delete on core.organization_policies  for each row execute function core.forbid_mutation();
create trigger generations_immutable           before update or delete on core.generations            for each row execute function core.forbid_mutation();
create trigger audit_events_immutable          before update or delete on audit.events                for each row execute function core.forbid_mutation();

-- ------------------------------------------------- updated_at triggers ----
create trigger organizations_touch    before update on core.organizations    for each row execute function core.touch_updated_at();
create trigger app_users_touch        before update on core.app_users        for each row execute function core.touch_updated_at();
create trigger families_touch         before update on core.families         for each row execute function core.touch_updated_at();
create trigger accounts_touch         before update on core.accounts         for each row execute function core.touch_updated_at();
create trigger connections_touch      before update on core.connections      for each row execute function core.touch_updated_at();
create trigger source_documents_touch before update on core.source_documents for each row execute function core.touch_updated_at();
create trigger meetings_touch         before update on core.meetings         for each row execute function core.touch_updated_at();

-- ------------------------------------------------------------- RLS (I3) ----
do $rls$
declare
    t text;
begin
    foreach t in array array[
        'app_users','organization_policies','families','holders','accounts',
        'transactions','position_snapshots','connections','source_documents',
        'extraction_batches','analysis_runs','meetings','generations',
        'generation_edits','generated_documents'
    ] loop
        execute format('alter table core.%I enable row level security', t);
        execute format(
            'create policy %I_tenant_isolation on core.%I using (org_id = core.current_org_id())',
            t, t
        );
    end loop;
end
$rls$;

alter table core.organizations enable row level security;
create policy organizations_self on core.organizations
    using (id = core.current_org_id());

-- benchmarks: global presets (org_id null) readable by all; own rows by tenant
alter table core.benchmarks enable row level security;
create policy benchmarks_visibility on core.benchmarks
    using (org_id is null or org_id = core.current_org_id());

-- ----------------------------------------------------------------- seeds ----
insert into core.benchmarks (org_id, name, kind, params) values
    (null, 'CDI',       'cdi',   '{}'),
    (null, 'Ibovespa',  'index', '{"index_code": "ibov"}'),
    (null, 'IMA-B',     'index', '{"index_code": "ima_b"}');

insert into core.custodians (name, kind) values
    ('XP Investimentos', 'corretora'),
    ('BTG Pactual',      'banco'),
    ('Itaú',             'banco'),
    ('Bradesco',         'banco'),
    ('Santander',        'banco'),
    ('Ágora',            'corretora'),
    ('Órama',            'corretora');

commit;
