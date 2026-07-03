# ROADMAP.md — Plano de Execução (Fases 0 e 1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [STRATEGY.md](../00_FOUNDATION/STRATEGY.md) (fases e gates) · [MVP_SCOPE.md](../01_PRODUCT/MVP_SCOPE.md) |

---

## 1. Como ler

Datas são alvos; **gates são obrigatórios** (STRATEGY.md §6). Cada fase separa o trabalho em duas trilhas: **Fundador** (o que só o João Pedro pode fazer — validação, venda, verdade dos números) e **CTO-IA** (o que eu executo com agentes). A trilha do fundador é o caminho crítico da Fase 0; a minha, o da Fase 1.

## 2. Fase 0 — Validação (jul–set/2026, ~10 semanas)

| Semanas | Trilha Fundador | Trilha CTO-IA |
|---|---|---|
| 1–2 | Lista de 30+ alvos no ICP (rede própria); primeiros agendamentos; ler e internalizar o [DISCOVERY_PLAYBOOK.md](DISCOVERY_PLAYBOOK.md) | Setup do monorepo, contas e plataformas; spike técnico: agregador Open Finance (sandbox Pluggy e alternativas) + parsing de 5 extratos reais — **teste da premissa P3 antes de tudo** |
| 3–6 | **12–16 entrevistas** (meta: 2–3/semana), registradas no tracker; ajuste do roteiro após as 5 primeiras | **Protótipo demonstrável**: 2 carteiras reais (anonimizadas, do próprio fundador) → consolidação → análise institucional → briefing + relatório PDF exemplares. Não é o MVP: é a demo que converte entrevista em pré-venda |
| 7–8 | Últimas entrevistas (total 15–20); demos do protótipo para os melhores fits | Primeiros casos dourados (as 2 carteiras do protótipo, calculadas à mão comigo e conferidas pelo fundador); rascunho de contrato de design partner + DPA (com jurídico) |
| 9–10 | **Conversão: 5 design partners assinados com compromisso financeiro** | Consolidação dos aprendizados → revisão de BUSINESS_MODEL (preços reais ouvidos) e PERSONAS (correções) |

**Gate 0→1 (revisão formal):** ≥ 5 design partners pagantes + dor confirmada top-2 em ≥ 60% + cobertura de dados viável no spike. Falhou → R1 do STRATEGY.md (não construir; re-testar dor).

## 3. Fase 1 — MVP (out/2026 – mar/2027, 6 meses)

| Mês | Entrega principal | Critério de "feito" |
|---|---|---|
| **M1 (out)** | Fundação: monorepo, CI com todos os gates, auth+organizações, tenancy com RLS + testes de isolamento, esquemas core/audit, framework de golden tests | Deploy contínuo em staging; primeiro golden test rodando no CI |
| **M2 (nov)** | Ingestão: Open Finance (agregador) + upload/parsing com fila de confirmação + manual. **Design partners conectam dados reais ao fim de M2** | ≥ 70% do patrimônio dos DPs dentro (medição real do gate técnico) |
| **M3 (dez)** | Motor v1: classes do MVP_SCOPE 3.2 + métricas + runs imutáveis | 100% das métricas com goldens assinados pelo fundador |
| **M4 (jan)** | Camada de IA: AnalysisContext, verificador de proveniência, resumo/o-que-mudou/pontos de atenção/briefing; **primeiras reuniões reais preparadas na plataforma** | Métrica-estrela > 0; evals de IA no CI |
| **M5 (fev)** | Fábrica de material (relatório com marca, PDF) + Q&A + trilha de auditoria completa na UI (proveniência clicável) | Design partner entrega material a cliente real sem retrabalho |
| **M6 (mar)** | Hardening: LGPD operacional (exportação/exclusão), backups testados, performance, onboarding self-service < 30 min; buffer para o que a realidade trouxer | Os 5 DPs ativos semanalmente; zero número errado em produção |

**Regras da fase:** design partners usam desde M2 (nunca beta silencioso — feedback quinzenal já previsto no contrato deles) · toda sexta: revisão de progresso contra este plano e replanejamento honesto (atraso se declara na semana em que nasce, não em M6) · escopo negocia, precisão e auditoria nunca (R6).

**Gate 1→2:** ≥ 3 DPs preparando reuniões reais toda semana + dispostos a pagar preço de tabela + "não voltaria ao processo antigo". Falhou → R3 (congela GTM, imersão de produto).

## 4. Fase 2 — Repetibilidade (abr–dez/2027) — esboço

Playbook de venda documentado a partir do que funcionou com os 5 primeiros · onboarding sem toque < 2 semanas · billing automatizado · v1.1 (registro pós-reunião + suitability; alertas) puxada por uso real, não por opinião · meta dez/2027: 25–40 organizações, MRR ≥ R$ 60 mil, churn < 2%/mês. Detalhamento ao cruzar o Gate 1→2.

## 5. Dependências do fundador (o roadmap quebra sem isso)

1. **~20h/semana na Fase 0** (entrevistas são o caminho crítico); disponibilidade menor = gate desliza — avisar cedo.
2. **Conferência de números dourados** (M3 sobretudo): é a função insubstituível — o padrão de verdade da empresa.
3. **Relação com design partners:** quinzenais dele, não meus.
4. Contratação de jurídico pontual (parecer CVM + contratos) na Fase 0/1 — orçado no BUSINESS_MODEL.

> **Realinhamento (2026-07-03, decisão do fundador):** a fase de validação de mercado está **encerrada**. Gates comerciais e tarefas de descoberta deste documento deixam de ser processo ativo e permanecem apenas como registro histórico. Fluxo vigente: escrever documento → revisar → aprovar → implementar. O plano de construção técnica (§3) segue como referência de sequência de engenharia.

## 6. Status vivo (atualizado a cada avanço)

| Data | Trilha | Item | Status |
|---|---|---|---|
| 2026-07-03 | CTO-IA | Spike de dados: BCB/SGS e Tesouro testados ao vivo ✅; descoberta de piso de custo de agregadores (→ [SPIKE_001](../02_ARCHITECTURE/spikes/SPIKE_001_DATA_SOURCES.md)) | **Feito** (pendências: CVM, cotações B3, parsing de extratos reais, sandbox Pluggy) |
| 2026-07-03 | CTO-IA | Protótipo v0.1: motor Decimal (Dietz encadeado, alocação, concentração, liquidez, vencimentos), 4 regras de insight, briefing + relatório institucional HTML, runs imutáveis, **17/17 testes dourados** | **Feito** — Python 3.12 instalado na máquina do fundador; demo roda local |
| 2026-07-03 | Fundador | **10 entrevistas realizadas** — sinal forte (4 pedidos de piloto, trilha de auditoria citada espontaneamente 2x). Registro e leitura de gate em [INTERVIEWS_TRACKER](tracking/INTERVIEWS_TRACKER.md) | **Parcial** — faltam: dados de preço (Van Westendorp), classificação ICP de 4 entrevistados, 5–10 entrevistas, e conversão dos 4 pilotos em design partners **pagantes** (0/5 do gate) |
| 2026-07-03 | Fundador | 3 extratos reais XP ("Posição Detalhada") entregues | **Feito** — protegidos fora do versionamento (LGPD) |
| 2026-07-03 | CTO-IA | Parsing por visão dos 3 extratos → fila de confirmação (totais por seção, controle anti-alucinação em 2 etapas) | **Aguardando confirmação do fundador** para virar casos dourados reais |

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total. · v1.1 (2026-07-03) — status vivo inaugurado com entregas do primeiro dia da Fase 0.
