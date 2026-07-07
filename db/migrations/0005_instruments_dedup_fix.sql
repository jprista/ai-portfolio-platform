-- ============================================================================
-- 0005_instruments_dedup_fix.sql — corrects instrument dedup key.
--
-- Root cause (found 2026-07-07, first real multi-portfolio confirmation):
-- instruments_identifiers_uq deduped on (kind, identifiers::text), but
-- `identifiers` now also carries the display-bucketing hint `category`
-- (introduced for the confirmation queue) — NOT a genuine external id.
-- Multiple distinct funds sharing the same category (e.g. several "Fundos de
-- Renda Fixa Pós-Fixado") produced the SAME identifiers value and collided.
--
-- Fix: dedup on (kind, name) — the actual natural key until real external
-- identifiers (CNPJ/ticker/ISIN) are captured per instrument. `identifiers`
-- remains free for metadata (category) and future real external ids.
-- ============================================================================

begin;

drop index if exists core.instruments_identifiers_uq;

create unique index instruments_kind_name_uq on core.instruments (kind, name);

commit;
