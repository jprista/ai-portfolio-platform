-- ============================================================================
-- 0004_instruments_index_fix.sql — dedup index must only apply when the
-- instrument HAS external identifiers; empty {} must not collide (found by
-- the first real seed on 2026-07-06).
-- ============================================================================

begin;

drop index if exists core.instruments_identifiers_uq;

create unique index instruments_identifiers_uq
    on core.instruments (kind, (identifiers::text))
    where identifiers::text <> '{}';

commit;
