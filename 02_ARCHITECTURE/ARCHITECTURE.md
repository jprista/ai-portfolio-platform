# ARCHITECTURE.md — Arquitetura do Sistema

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [MISSION.md](../00_FOUNDATION/MISSION.md) (Princípios 3, 6, 7) · [MVP_SCOPE.md](../01_PRODUCT/MVP_SCOPE.md) |
| **Irmãos** | [DATA_STRATEGY.md](DATA_STRATEGY.md) · [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md) · [SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md) · [TECH_STACK.md](../03_ENGINEERING/TECH_STACK.md) |

---

## 1. Filosofia arquitetural

Arquitetura para **um fundador + agentes de IA**, não para um time de 40: o inimigo é a complexidade operacional, não a escala (que virá depois e tem caminho traçado). Três compromissos:

1. **Monolito modular, não microsserviços.** Dois deployables apenas (web + motor), fronteiras internas rígidas por módulos. Microsserviços resolvem problema de coordenação de times — não temos times.
2. **Aborrecido por fora, rigoroso por dentro.** Tecnologias maduras e gerenciadas (Postgres, filas simples, plataformas managed); o rigor vai para onde nos diferencia: motor, auditoria, isolamento de tenant.
3. **As invariantes valem mais que os componentes.** Componentes serão trocados; as cinco invariantes do §3 não.

## 2. Visão de contêineres

```
                    ┌─────────────────────────────────────────────┐
                    │                  USUÁRIO                     │
                    └──────────────────────┬──────────────────────┘
                                           │ HTTPS
                    ┌──────────────────────▼──────────────────────┐
                    │  WEB APP (Next.js/TS — Vercel, região GRU)  │
                    │  UI · BFF/rotas de API · autenticação (Clerk)│
                    └───────┬──────────────────────────┬──────────┘
                            │ REST/OpenAPI (JWT)       │
        ┌───────────────────▼────────────┐   ┌─────────▼─────────────────┐
        │  ENGINE (Python/FastAPI — GRU) │   │  JOBS (fila gerenciada)    │
        │  Motor de cálculo determinístico│  │  ingestão · sync diário ·  │
        │  runs imutáveis e versionados  │   │  parsing · geração de PDF  │
        └───────┬────────────────────────┘   └─────────┬─────────────────┘
                │                                      │
   ┌────────────▼──────────────────────────────────────▼───────────────┐
   │  POSTGRES (região sa-east-1) — RLS por tenant                     │
   │  esquemas: core (domínio) · market (dados de mercado, sem tenant) │
   │  · audit (append-only) — + OBJECT STORAGE (docs, PDFs)            │
   └───────────────────────────────────────────────────────────────────┘
        Integrações: Agregador Open Finance · Fontes de mercado (CVM,
        Tesouro, BCB/SGS, cotações B3) · Claude API (camada de IA)
```

## 3. As cinco invariantes (o que nunca muda)

| # | Invariante | Consequência prática |
|---|---|---|
| I1 | **Nenhum número apresentado nasce fora do motor** | LLM não faz aritmética; UI não calcula (nem soma coluna) — exibe outputs do motor. Um único ponto de verdade numérica |
| I2 | **Execuções do motor são imutáveis** | `AnalysisRun` = (snapshot de inputs + versão do motor + outputs + hash). Reproduzível para sempre; correção = novo run, nunca edição |
| I3 | **Todo dado de tenant passa por RLS** | Row-Level Security no Postgres como última linha de defesa, além do filtro na aplicação; testes automatizados de isolamento a cada release |
| I4 | **Auditoria é append-only** | Esquema `audit` sem UPDATE/DELETE (revogados por permissão de banco); tudo que P3 (Eduardo) mostraria a um auditor externo vive aqui |
| I5 | **API primeiro** | Toda capacidade nasce como endpoint OpenAPI; a UI é o primeiro consumidor, agentes serão o segundo (Crença C5). O contrato OpenAPI é fonte de tipos para o front |

## 4. Módulos do domínio (fronteiras internas)

`identity` (organizações, usuários, papéis — espelho do Clerk) · `clients` (famílias, mandatos) · `portfolio` (instrumentos, transações, posições — transações imutáveis, correção por estorno) · `ingestion` (conectores, parsing, fila de confirmação humana) · `market-data` (preços, índices, curvas — global, sem tenant) · `engine` (cálculo — Python, sem estado próprio além de runs) · `insights` (regras determinísticas de pontos de atenção) · `narrative` (camada de IA — ver AI_ARCHITECTURE.md) · `meetings` (o objeto central do produto) · `materials` (relatórios/PDF) · `audit` (trilha).

Regra de dependência: módulos só conversam por interfaces explícitas; `engine` e `market-data` não conhecem tenants (recebem dados, devolvem resultados — o que facilita extração futura e testes dourados).

## 5. Fluxos principais

**Ingestão (Open Finance):** conexão → job de sync diário → normalização para o modelo canônico → reconciliação (posição derivada de transações vs. posição informada; divergência = flag de confiança, nunca ajuste silencioso) → gatilho de re-análise.

**Ingestão (documento):** upload → parsing (IA, com defesas de AI_ARCHITECTURE.md §5) → **fila de confirmação humana** → aprovação → entra como transações/posições com origem `document` + referência ao arquivo original no storage (auditável até o PDF).

**Análise:** requisição → engine monta snapshot (posições + preços com data de corte) → calcula → persiste `AnalysisRun` imutável → `insights` roda regras sobre o run → `narrative` gera textos citando exclusivamente o run → UI exibe com proveniência clicável.

**Material:** template da organização + run + narrativa → render HTML → PDF (job) → storage + registro em `audit` (quem gerou, para qual cliente, com qual run).

## 6. Multi-tenancy

Banco único, `tenant_id` em toda tabela de domínio, RLS ativo (política por tenant via claim do JWT), storage particionado por tenant. Suficiente e correto para os próximos anos; isolamento físico (banco dedicado) só se um cliente Instituição pagar por isso — decisão adiada de propósito.

## 7. Caminho de escala (para não sobre-engenheirar hoje)

| Gargalo futuro | Resposta já desenhada |
|---|---|
| Volume de análises | Engine é stateless → réplicas horizontais atrás da API |
| Dados de mercado crescem | Esquema `market` extraível para banco próprio/TimescaleDB sem tocar o domínio |
| Clientes enterprise exigem infra dedicada | Migração para AWS sa-east-1 (containers ECS + RDS) documentada como ADR; nada na stack atual impede |
| API pública (v3) | Mesmo contrato OpenAPI da UI, com gestão de chaves e rate limiting na frente |

## 8. Decisões registradas (ADRs)

Decisões arquiteturais relevantes viverão em `02_ARCHITECTURE/decisions/` (uma página por decisão: contexto, opções, escolha, consequências). ADR-001 (dois deployables), ADR-002 (RLS como defesa final) e ADR-003 (runs imutáveis) estão implícitas neste documento e serão formalizadas na primeira semana da Fase 1.

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
