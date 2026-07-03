# TECH_STACK.md — Stack Tecnológica

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [ARCHITECTURE.md](../02_ARCHITECTURE/ARCHITECTURE.md) |

---

## 1. Critérios de escolha (na ordem)

(1) **Operável por um fundador + agentes** — managed > auto-hospedado, sempre; (2) **maturidade** — nada que vire arqueologia em 2 anos; (3) **os agentes de IA são fluentes** — stacks populares rendem melhor código gerado e revisado; (4) custo compatível com bootstrap; (5) caminho de escala sem reescrita (ARCHITECTURE §7). Velocidade de moda não é critério.

## 2. Decisões

| Camada | Escolha | Racional | Alternativa rejeitada (por quê) |
|---|---|---|---|
| Web app | **Next.js (App Router) + TypeScript** | Full-stack maduro, SSR, ecossistema; fluência máxima de agentes | Remix/SvelteKit (menor ecossistema B2B); SPA pura (SEO/perf de dashboards server-side) |
| UI | **Tailwind + shadcn/ui** | Densidade profissional customizável; componentes possuídos, não dependência | Lib pesada (MUI/Ant): estética difícil de descolar |
| Motor de cálculo | **Python 3.12 + FastAPI**, `Decimal` em caminho de dinheiro, pandas/numpy no analítico | Ecossistema quant; separação natural da invariante I1; tipagem com mypy strict | Motor em TS (ecossistema quant fraco); Rust (velocidade de dev de um time solo vale mais que performance que não precisamos ainda) |
| Banco | **PostgreSQL gerenciado (Supabase), região sa-east-1** | RLS nativo (I3), storage incluso, latência BR, preço bootstrap | RDS direto (mais operação); NoSQL (domínio é relacional e transacional) |
| Autenticação | **Clerk** (organizações, convites, MFA, papéis) | B2B multi-tenant pronto em dias, não semanas; MFA e SSO no roadmap deles | Auth própria (risco e tempo); Supabase Auth (camada de organizações imatura para B2B) |
| Jobs/filas | **Inngest** (sync diário, parsing, PDFs) | Serverless-friendly, retries/observabilidade prontas, tier gratuito generoso | Celery+Redis (mais infra para operar); cron simples (sem retries/visibilidade) |
| IA | **Claude API (Anthropic)** — Sonnet padrão, topo de linha sob flag, versões pinadas | Melhor instrução-seguimento para o contrato de grounding; visão para parsing | Multi-provedor desde o dia 1 (complexidade prematura — abstração fina `LLMGateway` deixa a porta aberta) |
| Hospedagem web | **Vercel** (funções em GRU) | Zero operação, preview deployments (úteis com agentes) | — |
| Hospedagem engine | **Fly.io ou Railway, região São Paulo** — decidir no spike da semana 1 da Fase 1 | Containers gerenciados, perto do banco | K8s/AWS direto (operação que não temos braço para pagar agora; é o destino de escala, não o começo) |
| PDF | **Playwright (HTML → PDF)** em job | Fidelidade total com o design system dos relatórios | react-pdf (limitado para material institucional) |
| Observabilidade | **Sentry** (erros) + logs estruturados da plataforma; Axiom se precisar | Suficiente para dois deployables | Stack Grafana (operação demais) |
| CI/CD | **GitHub + GitHub Actions** | Padrão; agentes integram bem (PRs, reviews) | — |
| Monorepo | **pnpm + Turborepo**; `apps/web`, `services/engine`, `packages/contracts` (tipos gerados do OpenAPI) | Contrato único de tipos entre TS e Python (I5) | Repos separados (sincronização de contrato manual = drift) |
| E-mail transacional | **Resend** | Simples, barato | — |
| Billing | **Manual (Pix/transferência + NF) na Fase 1**; Stripe/Asaas no Gate 1→2 | 5 design partners não justificam integração; caixa primeiro | Automatizar cedo (custo de oportunidade) |

## 3. Regras transversais

- **Tudo em inglês no código** (nomes, comentários, commits); pt-BR é língua de produto e documentação de negócio. Facilita agentes, contratações futuras e o Princípio 7 (arquitetura global).
- **`packages/contracts` é a fronteira sagrada:** o OpenAPI do engine gera os tipos TS; mudança de contrato é PR explícito, nunca drift silencioso.
- **Nada de serviço novo sem ADR** — cada dependência é um custo de operação vitalício para um time de um.
- **Custo total da stack na Fase 1: ~R$ 1,5–3 mil/mês** (dentro do burn do BUSINESS_MODEL §5); revisão trimestral de custos.

## 4. O que este documento não decide

Detalhes de bibliotecas (validação, ORM, charts) ficam para ADRs curtas durante a Fase 1 — decisões reversíveis não merecem cerimônia; as daqui (linguagens, banco, plataformas, fronteiras) são as caras de trocar.

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
