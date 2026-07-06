-- ============================================================================
-- 0002_api_spec_decisions.sql — implements API_SPEC.md v1.1 founder decisions
-- (2026-07-03): explicit sharing with extensible scopes, AI-records retention
-- policy, material versioning/freezing, new audit event kinds.
-- ============================================================================

begin;

-- decision 9.4 — explicit sharing; scope enum born extensible (v1 uses 'full')
create type core.share_scope as enum ('full','read_only','edit','approval','audit');

create table core.family_shares (
    id          uuid primary key default gen_random_uuid(),
    org_id      uuid not null references core.organizations(id),
    family_id   uuid not null references core.families(id),
    user_id     uuid not null references core.app_users(id),
    scope       core.share_scope not null default 'full',
    granted_by  uuid references core.app_users(id),
    created_at  timestamptz not null default now(),
    unique (family_id, user_id)
);

alter table core.family_shares enable row level security;
create policy family_shares_tenant_isolation on core.family_shares
    using (org_id = core.current_org_id());

-- decision 9.3 — org-defined retention for AI interaction records
-- (null = retain indefinitely; purge is itself audited)
alter table core.organization_policies
    add column ai_interaction_retention_days integer;

-- decision 9.2 — material versioning: frozen after sending, new versions
-- preserve prior ones with full generation parameters
alter table core.generated_documents
    add column version integer not null default 1,
    add column supersedes_id uuid references core.generated_documents(id),
    add column frozen_at timestamptz;

create unique index generated_documents_version_uq
    on core.generated_documents (meeting_id, kind, version)
    where meeting_id is not null;

-- decision 9.1 + 9.2 + 9.3 — audit event kinds for the new exceptions
alter type audit.event_kind add value if not exists 'meeting_state_skipped';
alter type audit.event_kind add value if not exists 'material_frozen';
alter type audit.event_kind add value if not exists 'ai_records_purged';
alter type audit.event_kind add value if not exists 'family_share_granted';
alter type audit.event_kind add value if not exists 'family_share_revoked';

commit;
