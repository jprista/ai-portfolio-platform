# API_SPEC.md — Contrato da API da Plataforma (v1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | **Aprovado pelo fundador em 2026-07-03** (v1.1, com as 4 decisões do §9 incorporadas) — implementação autorizada |
| **Subordinado a** | [ARCHITECTURE.md](../02_ARCHITECTURE/ARCHITECTURE.md) (I1, I2, I5) · [DOMAIN_MODEL.md](DOMAIN_MODEL.md) v1.1 · [AI_ARCHITECTURE.md](../02_ARCHITECTURE/AI_ARCHITECTURE.md) |
| **Implementa-se em** | `packages/contracts/openapi.yaml` (fonte única de tipos TS + Python) |

---

## 1. Papel deste documento

Define o contrato lógico da API da plataforma — a **única porta** para toda capacidade (I5): a interface web é o primeiro consumidor; agentes de IA e integrações serão os próximos, **do mesmo contrato**. Especifica convenções, recursos, máquina de estados, erros e as garantias de proveniência que tornam a API consumível por máquinas com a mesma auditabilidade que por humanos.

## 2. Convenções

| Tema | Regra |
|---|---|
| Estilo | REST orientado a recursos, OpenAPI 3.1, JSON. Prefixo `/api/v1` |
| Autenticação | Bearer JWT (Clerk); claims carregam `org_id` e `role`. Toda requisição é executada no contexto do tenant do token — nunca há parâmetro `org_id` na URL (o isolamento não é opt-in) |
| Dinheiro e taxas | **Strings decimais** (`"412350.75"`), nunca float JSON (regra float-proibido atravessa o contrato). Campos monetários acompanham `currency` (v1: `"BRL"`) |
| Datas | ISO 8601; timestamps UTC (`Z`); datas de negócio como `YYYY-MM-DD` |
| Erros | RFC 9457 (Problem Details): `type`, `title`, `status`, `detail`, `instance` + extensão `code` (catálogo §6) |
| Paginação | Cursor-based (`?cursor=&limit=`, máx. 200); resposta com `next_cursor` |
| Idempotência | Todo POST de criação aceita `Idempotency-Key` (obrigatório para agentes; recomendado para a UI) |
| Imutabilidade no contrato | Recursos imutáveis (transações, runs, gerações, políticas) **não expõem** `PUT/PATCH/DELETE` — a operação de correção é explícita (`POST .../reversals`, nova versão de política). A API torna a invariante I2 impossível de violar por cliente |
| Proveniência | Toda resposta com números de análise carrega `run_id`, `engine_version`, `policy_version` e `data_as_of` — sem exceção (é o que torna a API "agent-ready": máquina cita fonte como humano) |
| Limitações declaradas | Respostas de análise incluem array `declared_limitations[]` (classes não suportadas, dados defasados, fallback de projeção do VNA) — Princípio 2 no nível do contrato |

## 3. Recursos e endpoints (v1)

### Núcleo de clientes
```
GET/POST        /families                       · lista/cria famílias
GET/PATCH       /families/{id}                  · detalhe/edita (nome, benchmark, profissional)
GET/POST        /families/{id}/holders          · titulares (FGC por CPF)
GET/POST        /families/{id}/accounts         · contas por custodiante
```

### Portfólio (imutável por contrato)
```
GET/POST        /accounts/{id}/transactions     · POST cria; sem PUT/DELETE
POST            /transactions/{id}/reversals    · estorno explícito (auditável)
GET/POST        /accounts/{id}/positions        · snapshots informados
POST            /positions/{id}/contract-terms  · complementação de contrato pelo usuário
                                                  (grava contract_terms_origin=user_provided — decisão 9.3 do DOMAIN_MODEL)
```

### Ingestão
```
POST            /documents                      · upload de extrato (multipart, máx. 25 MB)
GET             /documents/{id}                 · status do pipeline
GET             /documents/{id}/extraction      · resultado extraído para conferência
POST            /documents/{id}/extraction/confirm  · confirmação humana (nada entra sem isso)
GET/POST/DELETE /families/{id}/connections      · Open Finance (DELETE = revogação de consentimento)
```

### Análise (o motor via API)
```
POST            /families/{id}/analysis-runs    · dispara análise; retorna run imutável
GET             /analysis-runs/{id}             · outputs completos + proveniência
GET             /analysis-runs/{id}/insights    · pontos de atenção (com a política/versão usada)
POST            /analysis-runs/{id}/generations · narrativa IA {kind: summary|what_changed|briefing}
                                                  resposta inclui validator_result (aprovado/degradado)
POST            /analysis-runs/{id}/qa          · pergunta fundamentada no run (grounded)
```

### Reuniões (o objeto central)
```
GET/POST        /families/{id}/meetings         · agenda/lista
GET             /meetings/{id}                  · detalhe com linha do tempo
POST            /meetings/{id}/transition       · {to: preparing|material_generated|material_sent|held|cancelled}
                                                  máquina de estados validada no servidor (§4)
POST            /meetings/{id}/materials        · gera briefing/relatório {kind}; associa run + geração
GET             /materials/{id}                 · metadados + URL assinada de download
```
**Versionamento de material (decisão do fundador, §9.2):** após `material_sent`, o material é **congelado** (`frozen_at`); regenerar cria **nova versão** (`version` incremental, `supersedes_id` apontando a anterior), preservando integralmente todas as versões com data, autor e parâmetros (run + geração). Tentativa de mutação de material congelado → erro `MATERIAL_FROZEN`.

### Compartilhamento explícito (decisão do fundador, §9.4)
```
GET/POST        /families/{id}/shares           · concede acesso de outro profissional à família
DELETE          /shares/{id}                    · revoga
```
`scope` v1: apenas `full`; o enum já nasce extensível (`read_only`, `edit`, `approval`, `audit`) para permissões granulares futuras — estrutura pronta, comportamento v1 mínimo (diretriz de extensibilidade).

### Configuração e auditoria
```
GET             /benchmarks                     · presets globais + os da organização
POST            /benchmarks                     · benchmark custom da organização (kind + params)
GET             /policies/active                · política de limiares vigente
POST            /policies                       · nova versão (imutável; audit registra policy_changed)
GET             /audit-events                   · trilha filtrável (o endpoint do auditor externo)
GET             /organizations/me · /users      · contexto e equipe
```

## 4. Máquina de estados da Reunião (imposta no servidor)

Transições válidas (decisão do fundador, DOMAIN_MODEL §9.2): `scheduled → preparing → material_generated → material_sent → held`; `cancelled` alcançável de qualquer estado não-final; **pulos para frente são permitidos** (confirmado pelo fundador em 2026-07-03) e **toda exceção é registrada na auditoria** — evento `meeting_state_skipped` com quem fez, quando e a lista de estados pulados. Retrocesso não existe; correção de estado errado = cancelar e recriar (imutabilidade da linha do tempo).

## 5. API interna do motor (web → engine)

Contrato separado e mínimo, sem estado e sem conhecimento de tenant (ARCHITECTURE §4): `POST /engine/analyze` (snapshot de posições + séries + política → outputs de run), `POST /engine/valuate` (accrual de uma posição), `GET /engine/health`. O serviço web é o único chamador; tenancy, autenticação e persistência ficam fora do motor.

## 6. Catálogo de erros de domínio (extensão `code`)

`VALIDATION_FAILED` · `IDEMPOTENCY_CONFLICT` · `STATE_TRANSITION_INVALID` (§4) · `INSTRUMENT_UNSUPPORTED` (classe fora da v1 — devolve a limitação declarada, nunca 500) · `CONTRACT_TERMS_MISSING` (accrual impossível; lista `missing_fields[]` — dispara o fluxo de complementação) · `DATA_INSUFFICIENT` (ex.: volatilidade com < mínimo de observações da política) · `EXTRACTION_UNCONFIRMED` (tentativa de usar dado não confirmado) · `BENCHMARK_UNSUPPORTED` · `RUN_IMMUTABLE` (tentativa de mutação) · `MATERIAL_FROZEN` (mutação de material após envio — §3) · `TENANT_MISMATCH` (sempre 404, nunca 403 — não revelamos existência de recurso alheio).

## 7. Versionamento e compatibilidade

`v1` no path; mudanças **aditivas** (campos novos, endpoints novos, valores novos em enums *de saída*) não quebram versão; mudanças de quebra exigem `v2` com convivência mínima de 6 meses. O OpenAPI é versionado no repositório; **o CI quebra se o contrato mudar sem bump** (gate de contrato do ENGINEERING_PRINCIPLES §3). Enums de *entrada* nunca ganham valores obrigatórios novos dentro da mesma versão.

## 8. Prontidão para agentes (Crença C5, desenhada desde já)

O que a v1 já garante para o consumo por agentes de IA, sem custo extra: contrato OpenAPI completo e publicado · respostas autossuficientes (proveniência + limitações declaradas em todo payload de análise) · idempotência · zero estado ambiente (nenhum endpoint depende de "tela anterior") · erros estruturados com código de domínio acionável. O que fica para a fase de API pública (v3 do produto): chaves de API por integração, escopos, rate limits por consumidor, webhooks.

## 9. Decisões do fundador (revisão de prática de mercado, 2026-07-03)

1. **Pulos de estado — aprovado.** Qualquer transição válida para frente é permitida; toda exceção registrada na auditoria (quem, quando, estados pulados — evento `meeting_state_skipped`).
2. **Material enviado — congelado.** Alteração posterior = nova versão; versões anteriores preservadas integralmente com data, horário, autor e parâmetros (run + geração). Rastreabilidade completa (`version`, `supersedes_id`, `frozen_at`).
3. **Q&A auditado — aprovado com ressalva incorporada:** todas as interações relevantes com IA são auditadas (perguntas, respostas, análises, relatórios), **e a organização define política de retenção** desses registros (`ai_interaction_retention_days` na OrganizationPolicy; `null` = retenção indefinida; expurgo auditado via evento `ai_records_purged`) — por privacidade, armazenamento e conformidade.
4. **Visibilidade — aprovado:** admin vê tudo; profissional vê apenas famílias sob sua responsabilidade; compartilhamento explícito via `/families/{id}/shares`. **Permissões granulares futuras já modeladas** no enum `share_scope` (`full` na v1; `read_only`, `edit`, `approval`, `audit` reservados) — sem refatoração estrutural quando escritórios maiores chegarem.

**Changelog:** v1.0 (2026-07-03) — versão inicial para aprovação. · v1.1 (2026-07-03) — aprovada com as 4 decisões incorporadas (§3, §4, §6, §9).
