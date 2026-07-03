# ENGINEERING_PRINCIPLES.md — Princípios de Engenharia

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [MISSION.md](../00_FOUNDATION/MISSION.md) (C6, Princípio 3) · [TECH_STACK.md](TECH_STACK.md) |

---

## 1. O contexto único desta engenharia

Este código será escrito majoritariamente por agentes de IA, dirigidos por um CTO-IA, com um único humano validando — e calcula o patrimônio de famílias. As consequências: **os testes são a especificação** (o humano não relê cada linha; ele confia no que os gates provam), e o processo é desenhado para que **a confiança seja verificável, não presumida**.

## 2. Os testes dourados são a constituição

- Suíte de carteiras reais anonimizadas com métricas **calculadas e conferidas à mão** (DATA_STRATEGY §6). É o contrato entre o motor e a realidade.
- **Nenhum merge no motor com golden test falhando. Sem exceções, sem "depois eu arrumo".** Divergência tolerada: ≤ 0,01% vs. cálculo manual.
- Classe de ativo nova = casos dourados novos **assinados pelo fundador** (ele confere como auditor) *antes* do código entrar em produção.
- Golden test que falha e "parece certo" não se ajusta para passar: investiga-se até saber quem está errado — o motor ou o caso.

## 3. Pirâmide de testes (além dos dourados)

| Nível | O quê |
|---|---|
| Unitários | Toda função de cálculo; casos de borda (carteira vazia, um dia, aporte no primeiro dia, resgate total, indexador zerado) |
| Propriedade (hypothesis) | Invariantes que nunca quebram: pesos somam 100%, TWR compõe entre períodos, estorno anula transação, valor da carteira = soma das posições |
| Contrato | OpenAPI do engine × tipos consumidos pelo web (gerados, verificados no CI) |
| Isolamento | Suíte de acesso cruzado entre tenants (SECURITY_COMPLIANCE §2) — roda em todo release |
| Evals de IA | Proveniência numérica, linguagem prescritiva, qualidade editorial (AI_ARCHITECTURE §4) — em todo PR de prompt/modelo |
| Snapshot | Relatórios PDF (regressão visual dos materiais) |

## 4. Regras de código inegociáveis

1. **Float é proibido em dinheiro.** `Decimal` (Python) / strings+decimal.js ou inteiro em centavos (TS). Lint automatizado bloqueia `float` em módulos de cálculo.
2. **Correção é estorno, nunca UPDATE** em transações e trilhas (I2, I4).
3. **Todo output do motor carrega proveniência** (run_id, versão, timestamp de dados) de ponta a ponta até a UI.
4. **Migrações reversíveis;** destrutivas exigem backup verificado no mesmo PR.
5. **Erro nunca é engolido:** ou trata, ou propaga com contexto; log estruturado com tenant/run/request id.
6. **Inglês no código, pt-BR no produto** (TECH_STACK §3).

## 5. Fluxo de desenvolvimento (humano + agentes)

1. **Spec primeiro:** toda unidade de trabalho nasce como especificação curta (o quê, critérios de aceite, casos de teste) — escrita por mim (CTO), aprovada implicitamente pelo roadmap.
2. **Implementação por agente** em branch; PRs pequenos (< ~400 linhas líquidas de preferência).
3. **Revisão cruzada por um segundo agente** com foco em: correção, segurança (tenant, segredos, injeção), aderência a estes princípios — a revisão é registrada no PR.
4. **Gates de CI:** lint + tipos estritos (mypy/tsc) + pirâmide do §3 + verificação de segredos + auditoria de dependências.
5. **Papel do humano (João Pedro):** valida números de casos dourados novos; aprova releases que toquem o motor ou dados; é alertado de qualquer degradação de eval de IA. Ele não revisa código — revisa *verdade*.
6. **Trunk-based** com deploy contínuo para staging; produção por promoção explícita; feature flags para o que os design partners não devem ver ainda.
7. **ADRs** (`02_ARCHITECTURE/decisions/`) para toda decisão difícil de reverter; o agente que propõe escreve a ADR.

## 6. Definição de Pronto (DoD)

Código + testes do §3 pertinentes + proveniência/auditoria implementadas + revisão de agente registrada + sem novo warning de segurança + documentação atualizada (ADR/contratos) + **para features de motor: golden cases assinados**. "Funciona na demo" não é pronto.

## 7. Débito técnico e simplicidade

- Débito é permitido **somente registrado** (issue com etiqueta e plano); débito invisível é proibido.
- Regra de simplicidade: a solução mais simples que respeita as invariantes vence; abstração só na segunda repetição real (não na primeira imaginada).
- Refatoração contínua em PRs pequenos; nunca "a grande reescrita".

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
