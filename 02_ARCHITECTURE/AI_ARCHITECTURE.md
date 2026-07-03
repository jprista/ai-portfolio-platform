# AI_ARCHITECTURE.md — Arquitetura de IA

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [MISSION.md](../00_FOUNDATION/MISSION.md) (Princípio 1, Crença C6) · [ARCHITECTURE.md](ARCHITECTURE.md) (I1) |

---

## 1. O contrato fundamental

> **O motor calcula. A IA traduz. O humano recomenda.**

Em termos de engenharia: o LLM **nunca** produz um número novo, **nunca** faz aritmética, **nunca** recomenda. Ele recebe resultados tipados do motor e produz linguagem. Este documento existe para tornar essa separação *estruturalmente impossível de violar* — não uma convenção que um prompt mal escrito quebra.

## 2. As três camadas

```
┌────────────────────────────────────────────────────────────┐
│ CAMADA 3 — ORQUESTRAÇÃO (workflows agênticos)              │
│ parser de documentos · compositor de briefing · compositor │
│ de relatório · Q&A — cada um com escopo e guardrails próprios│
├────────────────────────────────────────────────────────────┤
│ CAMADA 2 — INTERPRETAÇÃO (LLM: Claude API)                 │
│ entrada: AnalysisContext (JSON tipado, só outputs do motor)│
│ saída: narrativa validada pelo Verificador de Proveniência │
├────────────────────────────────────────────────────────────┤
│ CAMADA 1 — VERDADE (motor determinístico, Python)          │
│ runs imutáveis · testes dourados · zero LLM                │
└────────────────────────────────────────────────────────────┘
```

## 3. O contrato de grounding (Camada 1 → 2)

Toda geração recebe um **AnalysisContext**: JSON tipado contendo exclusivamente outputs de um `AnalysisRun` (valores já formatados + metadados: período, benchmark, selo de confiança) e fatos registrados (última reunião, política do cliente). O prompt de sistema estabelece: números só do contexto, reproduzidos literalmente; o que não está no contexto não existe; sem conselho, sem imperativo, sem futuro previsto.

### O Verificador de Proveniência Numérica (componente central)

Pós-processador determinístico de toda saída do LLM:

1. Extrai todos os tokens numéricos da narrativa (percentuais, valores monetários, datas, quantidades).
2. Confronta cada um contra o conjunto de valores do AnalysisContext (com tolerância zero de valor; flexibilidade apenas de formatação declarada).
3. Número órfão (sem correspondência) → **a saída inteira é descartada**, uma regeneração é tentada; falhando de novo, o texto degrada para template determinístico (feio e correto > bonito e errado).
4. Resultado da verificação (aprovado/regenerado/degradado) registrado na trilha de auditoria.

O mesmo verificador roda uma **lista de bloqueio de linguagem prescritiva** ("recomendo", "você deve", "venda", "compre", "melhor opção"...) — mantida como configuração versionada, revisada com olhar CVM 19/21. Detecção → mesma política de descarte.

## 4. Política de modelos

| Uso | Modelo | Racional |
|---|---|---|
| Narrativas, briefings, relatórios | Claude Sonnet (versão pinada) | Qualidade/custo; tom controlável |
| Q&A interativo | Claude Sonnet + contexto do run | Latência |
| Parsing de documentos | Claude (visão) com prompts dedicados | Melhor extração estruturada de extratos |
| Casos complexos (carteiras grandes, comitês) | Claude Opus/topo de linha, sob flag | Custo justificado pelo ticket |

Regras: versões **pinadas** (upgrade de modelo = PR com re-execução da suíte de avaliação, nunca upgrade automático) · temperatura baixa · API da Anthropic sem retenção para treino (confirmar contratualmente; avaliar zero-data-retention) · custo por feature monitorado com orçamento de tokens (H2 do BUSINESS_MODEL) e cache de contexto agressivo.

**Suíte de avaliação (evals):** conjunto versionado de AnalysisContexts reais → narrativas avaliadas em (a) proveniência 100%, (b) zero linguagem prescritiva, (c) qualidade editorial (rubrica revisada pelo fundador — ele é o padrão de tom do mercado). Roda em todo PR que toque prompts e em toda troca de modelo.

## 5. Segurança específica de IA

- **Documento é dado, nunca instrução.** Conteúdo de PDFs/planilhas entra em canal separado do prompt, com delimitação explícita e instrução de não-execução; texto extraído é sanitizado. Extrato malicioso com "ignore suas instruções e..." é o vetor óbvio — tratado como input hostil por padrão (prompt injection).
- **Parsing nunca escreve direto.** A saída do parser vai para a fila de confirmação humana (MVP_SCOPE 3.1) — humano aprova antes de virar dado.
- **Q&A não tem ferramentas de escrita.** A camada de interpretação lê contexto; jamais executa ações.
- **Isolamento por tenant também na IA:** o contexto de uma geração só contém dados do tenant da requisição (mesma regra I3).

## 6. Auditoria de IA

Toda geração registra (esquema `audit`): id e versão do modelo · hash do prompt de sistema · referência ao AnalysisRun/contexto · saída completa · resultado do verificador · quem solicitou e quando · edições manuais do usuário sobre o texto (diff). Responde à exigência regulatória esperada (documentação, supervisão humana, explicabilidade — Crença C4) e é argumento de venda para P3.

## 7. Agentes internos (a empresa-IA, lado de operação)

Distinto do produto: agentes que operam a *empresa* (Claude Code no desenvolvimento, agente de pesquisa regulatória/concorrência recorrente, rascunhos de conteúdo GTM). Regra da STRATEGY.md §8 mantida: decisões, números do motor (validação final) e toda relação humana são do fundador. Agentes de desenvolvimento seguem ENGINEERING_PRINCIPLES.md (revisão cruzada por segundo agente + gates de teste).

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
