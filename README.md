# AI Portfolio Platform *(nome provisório — pressuposto P5)*

> **Missão:** colocar inteligência de nível institucional em cada decisão de investimento profissional — com a precisão, a auditabilidade e a neutralidade que o dever fiduciário exige.

Plataforma SaaS de análise inteligente de carteiras para o mid-market fiduciário brasileiro (consultorias CVM, wealth managers independentes, multi family offices). Este repositório é, por enquanto, **o cérebro documentado da empresa** — o código nasce na Fase 1.

## Estado atual (2026-07-03)

| Fase | Período | Status |
|---|---|---|
| Documentação fundacional | jul/2026 | ✅ **Completa** (este repositório) |
| **Fase 0 — Validação** | jul–set/2026 | ⏳ **Próxima** — 15–20 entrevistas + protótipo + 5 design partners |
| Fase 1 — MVP | out/2026–mar/2027 | Aguardando Gate 0→1 |
| Fase 2 — Repetibilidade | abr–dez/2027 | Aguardando Gate 1→2 |

## Mapa dos documentos (ordem de leitura)

### 00_FOUNDATION — por que e como vencemos
1. [MISSION.md](00_FOUNDATION/MISSION.md) — missão, crenças falsificáveis, princípios inegociáveis, anti-objetivos. **Prevalece sobre tudo.** *(Aprovado)*
2. [MARKET_ANALYSIS.md](00_FOUNDATION/MARKET_ANALYSIS.md) — mercado, concorrência (Gorila, Smartbrain, globais), lacunas, riscos.
3. [STRATEGY.md](00_FOUNDATION/STRATEGY.md) — beachhead, fases com gates, kill criteria, GTM, modelo empresa-IA. *(Aprovado)*
4. [BUSINESS_MODEL.md](00_FOUNDATION/BUSINESS_MODEL.md) — planos e preços (H1), unit economics, ponto de equilíbrio, projeções.

### 01_PRODUCT — o que construímos
5. [PRODUCT_VISION.md](01_PRODUCT/PRODUCT_VISION.md) — a Reunião como objeto central; cinco pilares; princípios de experiência.
6. [PERSONAS.md](01_PRODUCT/PERSONAS.md) — Ricardo (consultoria CVM), Marina (wealth independente), Eduardo (MFO) + anti-persona.
7. [MVP_SCOPE.md](01_PRODUCT/MVP_SCOPE.md) — o corte: caminho dourado, classes de ativo v1, critérios de aceite, lista "fora".

### 02_ARCHITECTURE — como funciona
8. [ARCHITECTURE.md](02_ARCHITECTURE/ARCHITECTURE.md) — dois deployables, cinco invariantes (I1–I5), módulos, fluxos, escala.
9. [DATA_STRATEGY.md](02_ARCHITECTURE/DATA_STRATEGY.md) — Open Finance + parsing + dados públicos; selo de confiança; golden dataset.
10. [AI_ARCHITECTURE.md](02_ARCHITECTURE/AI_ARCHITECTURE.md) — três camadas; Verificador de Proveniência Numérica; evals; segurança de IA.
11. [SECURITY_COMPLIANCE.md](02_ARCHITECTURE/SECURITY_COMPLIANCE.md) — segurança essencial, LGPD operacional, fronteira CVM.

### 03_ENGINEERING — com o quê e com que padrão
12. [TECH_STACK.md](03_ENGINEERING/TECH_STACK.md) — Next.js/TS + Python/FastAPI + Postgres(RLS) + Claude API; racional e rejeições.
13. [ENGINEERING_PRINCIPLES.md](03_ENGINEERING/ENGINEERING_PRINCIPLES.md) — testes dourados como constituição; fluxo humano+agentes; DoD.

### 04_EXECUTION — o que fazemos agora
14. [ROADMAP.md](04_EXECUTION/ROADMAP.md) — Fase 0 semana a semana; Fase 1 mês a mês; dependências do fundador.
15. [DISCOVERY_PLAYBOOK.md](04_EXECUTION/DISCOVERY_PLAYBOOK.md) — roteiro de entrevista, tracker, critérios do gate, oferta de design partner.

## As cinco frases que resumem tudo

1. O motor calcula, a IA traduz, **o humano recomenda**.
2. Somos donos de um **workflow** (a reunião), não de um dado.
3. **Precisão é binária** — um número errado destrói a confiança.
4. Auditável por padrão: a regulação é nosso fosso, não nosso custo.
5. Validar antes de construir: **nenhuma fase começa sem o gate da anterior**.

## Governança do repositório

Documentos de fundação mudam por acordo dos fundadores, com changelog. Hierarquia em conflito: MISSION > STRATEGY > demais. Pressupostos abertos (P1–P5) vivem em MISSION.md §9 — nenhum documento pode tratá-los como decididos. Time: João Pedro (fundador) · Claude (CTO fundador) · agentes de IA (execução).
