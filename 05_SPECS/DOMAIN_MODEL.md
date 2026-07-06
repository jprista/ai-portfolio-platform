# DOMAIN_MODEL.md — Modelo de Domínio e Schema (v1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | **Aprovado pelo fundador em 2026-07-03** (v1.1, com as 4 decisões do §9 e a diretriz de extensibilidade incorporadas) — implementação autorizada |
| **Subordinado a** | [ARCHITECTURE.md](../02_ARCHITECTURE/ARCHITECTURE.md) (I1–I5) · [ENGINE_METHODOLOGY.md](ENGINE_METHODOLOGY.md) v1.1 · [MVP_SCOPE.md](../01_PRODUCT/MVP_SCOPE.md) |
| **Implementa-se em** | Migrações Postgres + tipos do contrato (`packages/contracts`) |

---

## 1. Princípios do modelo

1. **A Reunião é o objeto central** (PRODUCT_VISION §2) — tudo converge para ela.
2. **Transações e runs são imutáveis** (I2); correção é estorno, nunca UPDATE.
3. **Todo dado de tenant carrega `org_id` com RLS** (I3); dados de mercado são globais, sem tenant.
4. **Minimização LGPD**: nenhuma coluna que a análise não use (DATA_STRATEGY §7).
5. **Decisões do fundador de 2026-07-03 já modeladas:** `valuation_mode` por posição; `OrganizationPolicy` **versionada** — cada análise referencia a versão de política vigente (auditoria exige saber *com quais limiares* um alerta foi ou não gerado).
6. **Diretriz de extensibilidade (fundador, 2026-07-03 — princípio permanente de modelagem):** entre simplicidade da v1 e flexibilidade futura, prefere-se arquitetura extensível. A v1 implementa apenas o comportamento padrão, mas o modelo acomoda novas regras **sem refatoração estrutural** (ex.: `Benchmark` como entidade desde o dia 1, ainda que a v1 só use CDI).

## 2. Visão geral (relações principais)

```
Organization ─┬─ User (profissional)
              ├─ OrganizationPolicy (versionada)
              └─ Family ─┬─ Account (por custodiante) ─┬─ Transaction (imutável)
                         │                             └─ PositionSnapshot (informada)
                         ├─ Meeting ──→ AnalysisRun ──→ Generation (IA, auditada)
                         │        └──→ GeneratedDocument (briefing, relatório)
                         ├─ Connection (Open Finance)
                         └─ SourceDocument ──→ ExtractionBatch (fila de confirmação)

Globais (sem tenant): Issuer · Instrument · PricePoint · IndexSeries · FundInfo
Append-only:          AuditEvent (INSERT-only por permissão de banco)
```

## 3. Identidade e tenancy

| Entidade | Campos essenciais | Notas |
|---|---|---|
| **Organization** | id, name, slug, brand (jsonb: logo, cores), created_at | O tenant. Brand alimenta a Fábrica de Material |
| **User** | id, org_id, auth_external_id (Clerk), name, email, role (`admin`\|`professional`), status | Papéis mínimos v1 |
| **OrganizationPolicy** | id, org_id, **version**, effective_from, issuer_concentration_limit_pct (15), fgc_limit (250000), maturity_window_days (90), min_vol_observations (12), fee_median_overrides (jsonb), created_by | **Versionada e imutável**: mudança = nova versão. Defaults = ENGINE_METHODOLOGY §6. UI de edição na v1.1; v1 cria a versão default no onboarding |

## 4. Clientes e contas

| Entidade | Campos essenciais | Notas |
|---|---|---|
| **Family** | id, org_id, display_name, primary_professional_id, benchmark_id (FK → Benchmark; default: preset global CDI), status, created_at | O cliente final como unidade de relacionamento. **Sem CPF, endereço ou dados civis na v1** (minimização) |
| **Benchmark** | id, org_id (nullable — `NULL` = preset global), name, kind (`cdi`\|`ipca_plus`\|`index`\|`custom_portfolio`\|`composite`), params (jsonb: real_rate_aa, index_code, composição) | **Decisão do fundador (§9.4):** entidade desde a v1. Presets globais: CDI, Ibovespa, IMA-B, IPCA+X%; organizações e famílias podem definir os seus. A v1 só *usa* CDI; a estrutura já acomoda os demais sem refatoração |
| **Holder** | id, org_id, family_id, display_name, document_masked (`***.456.789-**`) | Titular de conta dentro da família — necessário porque **FGC é por CPF por emissor** (ver §9.1) |
| **Custodian** | id (global), name, type (`corretora`\|`banco`\|`seguradora`\|`plataforma`) | Tabela de referência |
| **Account** | id, org_id, family_id, holder_id, custodian_id, external_ref_masked, source (`open_finance`\|`document`\|`manual`), status | N contas por família por custodiante (conta regular + previdência etc.) |

## 5. Portfólio (o coração)

| Entidade | Campos essenciais | Notas |
|---|---|---|
| **Issuer** (global) | id, name, type (`bank`\|`asset_manager`\|`sovereign`\|`company`\|`insurer`), document (CNPJ raiz) | Base da regra de concentração |
| **Instrument** (global) | id, type (enum §7), name, issuer_id, index_type (`pre`\|`cdi_pct`\|`ipca_plus`\|`selic`\|`none`), identifiers (jsonb: cnpj_fundo, ticker, codigo_tesouro, isin), maturity | Deduplicado globalmente por identifiers |
| **Transaction** | id, org_id, account_id, instrument_id, type (§7), trade_date, settlement_date, quantity, price, gross_amount, **reversal_of** (FK autorreferente), source, created_by, created_at | **Imutável** (sem UPDATE/DELETE por permissão de banco). Correção = estorno + nova |
| **PositionSnapshot** | id, org_id, account_id, instrument_id, as_of, quantity, value, source, source_document_id, **confidence** (`A`–`D`), **valuation_mode** (`curve`\|`market`), contract_terms (jsonb: principal, start_date, rate_aa, index_pct, anniversary_day), **missing_contract_fields** (text[]), **contract_terms_source** (`statement`\|`user_provided`\|`mixed`) | Posição **informada** (foto do extrato). Posições derivadas de transações não são persistidas — nascem no run (I2). **Decisão do fundador (§9.3):** o motor usa automaticamente todo dado disponível; campos essenciais ausentes são identificados em `missing_contract_fields` e a plataforma solicita complementação ao usuário; dado completado manualmente fica registrado em `contract_terms_source` e declarado na análise |

## 6. Ingestão, análise, reunião e IA

| Entidade | Campos essenciais | Notas |
|---|---|---|
| **Connection** | id, org_id, family_id, provider (`pluggy`\|...), provider_item_ref, status, last_sync_at | Abstração `PortfolioSource` (DATA_STRATEGY §2) |
| **SourceDocument** | id, org_id, family_id, storage_path, kind, sha256, uploaded_by, status (`pending`→`awaiting_confirmation`→`confirmed`\|`rejected`) | O PDF original fica no storage — trilha até a fonte |
| **ExtractionBatch** | id, source_document_id, model_id, raw_output (jsonb), status, confirmed_by, confirmed_at, diffs (jsonb) | A fila de confirmação humana (MVP_SCOPE 3.1) |
| **AnalysisRun** | id, org_id, family_id, run_hash, engine_version, **policy_id** (versão usada), input_snapshot_ref (storage), outputs (jsonb), created_by, created_at | **Imutável.** Reproduzível: snapshot + versão ⇒ mesmos bytes |
| **Meeting** | id, org_id, family_id, professional_id, scheduled_for, status (**decisão do fundador §9.2:** `scheduled` → `preparing` → `material_generated` → `material_sent` → `held`, ou `cancelled`), previous_meeting_id, analysis_run_id, material_sent_at, held_at | **O objeto central.** `previous_meeting_id` encadeia a linha do tempo que alimenta "o que mudou". Os estados acompanham a preparação e o envio prévio do material ao cliente |
| **GeneratedDocument** | id, org_id, family_id, meeting_id, kind (`briefing`\|`client_report`), storage_path, analysis_run_id, generation_id, created_at | Todo material rastreável ao run e à geração |
| **Generation** | id, org_id, model_id+version, prompt_sha256, analysis_run_id, output_text, validator_result (`approved`\|`regenerated`\|`degraded`), requested_by, created_at | Auditoria de IA (AI_ARCHITECTURE §6) |
| **GenerationEdit** | id, generation_id, diff, edited_by, created_at | Supervisão humana documentada (Crença C4) |

## 7. Dados globais de mercado e enums

**Mercado (esquema `market`, sem tenant):** `PricePoint` (instrument_id, date, price, source, captured_at) · `IndexSeries` (index_code, date, value, source, captured_at) · `FundInfo` (cnpj, name, anbima_class, adm_fee_pct, perf_fee_pct, as_of — universo CVM, base das medianas de custo).

**Enums centrais:** `instrument_type`: cash, cdb, lci, lca, lc, tesouro, debenture*, fund, pension_fund, equity, etf, fii, bdr, coe*, other (*aceito no cadastro, marcado não-suportado — limitação declarada) · `transaction_type`: buy, sell, deposit, withdrawal, income, fee, transfer_in, transfer_out, reversal · `audit.event_type`: data_viewed, data_edited, run_created, document_generated, document_exported, extraction_confirmed, policy_changed, login, export_lgpd, purge_lgpd.

## 8. Convenções físicas

IDs UUIDv7 (ordenáveis) · dinheiro `NUMERIC(18,2)`, taxas/fatores `NUMERIC(20,10)`, quantidades `NUMERIC(24,8)` · timestamps `timestamptz` UTC · nomes em inglês, snake_case · RLS: política `org_id = (jwt→org_id)` em toda tabela de tenant; esquemas `market` e `audit` com permissões próprias (audit: INSERT-only) · **purga LGPD:** rotina que apaga família (cascade em contas/posições/documentos/runs) e **anonimiza** (não apaga) os AuditEvents correlatos — a trilha sobrevive sem o dado pessoal · sem hard-delete fora da purga.

## 9. Decisões do fundador (revisão de especialista, 2026-07-03)

1. **FGC por titular — determinado.** Cálculo sempre por CPF/CNPJ por emissor (realidade regulatória); a visão consolidada da família ganha adicionalmente um **alerta agregado** de concentração relevante. Implementação: regra `FGC_TITULAR` (por holder) + regra `CONCENTRACAO_EMISSOR` (agregada por família).
2. **Estados da Reunião — definidos pelo fundador:** `Agendada → Em preparação → Material gerado → Material enviado → Realizada` (+ `Cancelada`), permitindo acompanhar preparação e envio prévio do relatório.
3. **Dados de contrato — fluxo determinado:** motor usa automaticamente tudo que houver; ausências essenciais são identificadas (`missing_contract_fields`), a plataforma solicita complementação, e o uso de dado informado manualmente fica **registrado e declarado na análise** (`contract_terms_source`).
4. **Benchmark — extensível desde o dia 1:** entidade `Benchmark` com presets globais (CDI, IPCA+X%, IMA-B, Ibovespa), carteira personalizada e definição por organização ou família. V1 usa CDI como padrão.

**Diretriz adicional registrada (permanente):** entre simplicidade da v1 e flexibilidade futura, preferir arquitetura extensível — v1 implementa o comportamento padrão, o modelo acomoda novas regras sem refatoração estrutural (§1.6).

**Changelog:** v1.0 (2026-07-03) — versão inicial para aprovação. · v1.1 (2026-07-03) — aprovada com as 4 decisões e a diretriz de extensibilidade incorporadas (§1, §4, §5, §6).
