-- ============================================================================
-- 0006_macro_snapshot.sql — snapshot macroeconômico para a aba Análise.
-- Fonte: BCB/SGS (público, sem chave). Mesmo padrão de dados reais externos
-- já usado no Radar de Consenso (CVM CDA / SEC 13F): busca em lote via script,
-- app só lê do banco — nunca chama API externa em tempo de requisição.
-- ============================================================================

begin;

create table market.macro_snapshot (
    id              uuid primary key default gen_random_uuid(),
    captured_at     timestamptz not null default now(),
    selic_meta_pct  numeric(6,2) not null,
    selic_as_of     date not null,
    ipca_12m_pct    numeric(6,2) not null,
    ipca_as_of      date not null,
    usd_brl         numeric(10,4) not null,
    usd_as_of       date not null,
    source_url      text not null default 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/1'
);

commit;
