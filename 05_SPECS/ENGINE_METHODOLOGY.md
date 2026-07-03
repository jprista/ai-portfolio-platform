# ENGINE_METHODOLOGY.md — Metodologia de Cálculo do Motor (v1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | **Aprovado pelo fundador em 2026-07-03** (v1.1, com as 4 decisões do §8 incorporadas) — implementação autorizada |
| **Subordinado a** | [MVP_SCOPE.md](../01_PRODUCT/MVP_SCOPE.md) §3.2 · [ARCHITECTURE.md](../02_ARCHITECTURE/ARCHITECTURE.md) (I1, I2) · [ENGINEERING_PRINCIPLES.md](../03_ENGINEERING/ENGINEERING_PRINCIPLES.md) |
| **Implementa-se em** | `services/engine` (Fase de implementação) — cada seção numerada vira módulo + casos dourados |

---

## 1. Papel deste documento

Especifica **como cada número da plataforma é calculado**: convenções, fórmulas, fontes e arredondamentos. É a referência contra a qual os casos dourados são conferidos e a nota metodológica dos relatórios é escrita. Nenhuma métrica aparece na plataforma sem estar especificada aqui (ou declarada como não suportada). Alterações exigem nova versão + re-execução da suíte dourada.

## 2. Convenções gerais

| Convenção | Regra |
|---|---|
| Aritmética | `Decimal`, precisão de contexto 28 dígitos; **float proibido** em qualquer caminho de dinheiro |
| Contagem de dias | **DU/252** (dias úteis) para tudo que é indexado a CDI/SELIC e taxas prefixadas locais; calendário de feriados **ANBIMA** |
| Fatores diários de CDI | v1 usa a **taxa diária publicada no BCB/SGS série 12** (% a.d., que já incorpora a convenção CETIP/B3 de truncamento); fator diário = `1 + taxa/100`; percentual de CDI aplica-se sobre o excesso: `1 + (fator_diário − 1) × p` |
| Arredondamento de exibição | Valores monetários: 2 casas (half-even). Percentuais: cálculo em 4+ casas, exibição em 2 |
| Datas de preço | Todo preço/cota carrega a data efetiva; posição valorizada com dado defasado ≥ 3 dias úteis rebaixa o selo de confiança (DATA_STRATEGY §5) |
| Reprodutibilidade | Todo cálculo referencia o snapshot de inputs do `AnalysisRun` (I2); rodar duas vezes com o mesmo snapshot produz bytes idênticos |

## 3. Valorização por classe de ativo (v1)

### 3.1 Caixa e CDB de liquidez diária (% CDI)
`V_t = V_0 × ∏ᵢ [1 + (fator_CDIᵢ − 1) × p]` para cada dia útil `i` desde a última posição confirmada, com `p` = percentual contratado. Fonte do CDI: BCB/SGS série 12.

### 3.2 RF bancária prefixada (CDB/LCI/LCA pré)
Marcação **na curva** (accrual da taxa contratada): `V_t = P × (1 + taxa)^(du(aplicação, t)/252)`. Não marcamos a mercado papel bancário na v1 — **limitação declarada** no material (mercado secundário ilíquido; é a prática padrão de extratos de custódia). **Requisito futuro registrado (decisão do fundador, 2026-07-03):** a plataforma deverá suportar também marcação a mercado, com alternância entre os dois critérios quando aplicável — o modelo de dados já deve prever `valuation_mode` por posição (entra no DOMAIN_MODEL).

### 3.3 RF bancária IPCA+ — **VNA exato** (decisão do fundador, 2026-07-03)
`V_t = P × F_IPCA × F_stub × (1 + taxa_real)^(du(aplicação, t)/252)`, onde:

- **Aniversários:** dia contratual (padrão: dia da aplicação), ajustados para o **dia útil seguinte** quando caírem em dia não útil.
- **F_IPCA:** produto de `(1 + IPCA_m/100)` aplicado a cada aniversário transcorrido, onde `IPCA_m` é o último índice publicado na data do aniversário (mês anterior ao do aniversário; fonte BCB/SGS 433).
- **F_stub (período em aberto):** do último aniversário até a data-base, pro-rata por DU: `(1 + proj/100)^(du_decorrido / du_total_do_período)`. Projeção: **ANBIMA quando integrada**; até lá, *fallback* = último IPCA publicado, **sinalizado na proveniência e na nota metodológica** — é a única imprecisão da convenção, inevitável até a divulgação do índice do mês.
- Alternativa temporária descartada: a convenção simplificada (defasagem fixa + pro-rata sem aniversário) foi avaliada e rejeitada — a meta da plataforma é o cálculo mais preciso possível (decisão registrada).

### 3.4 Títulos públicos (Tesouro Direto)
**Preço de mercado público** (Tesouro Transparente, preço de venda do dia) × quantidade. Sem modelo próprio de curva na v1.

### 3.5 Fundos e FIEs de previdência
`cota_CVM(data) × quantidade de cotas`. Fonte: Informe Diário CVM. Fundos sem informe (exclusivos/restritos): posição informada pelo extrato, selo de confiança ≤ B.

### 3.6 Renda variável (ações, ETFs, FIIs, BDRs)
`fechamento_B3(data) × quantidade`, ajustado por eventos societários **somente quando refletidos na fonte de preços**; proventos entram como transações (fluxo), não como ajuste de preço, na v1.

### 3.7 Não suportados na v1 (sempre com limitação declarada, nunca silêncio)
Debêntures/crédito privado negociado, COE, offshore, cripto, derivativos, ilíquidos — posição informativa manual quando existir, **excluída das métricas de risco** e sinalizada no material.

## 4. Retornos

- **Metodologia oficial: TWR aproximado por Modified Dietz encadeado.** Sub-período = intervalo entre valorações disponíveis (diário quando houver série diária; mensal como granularidade mínima). Por sub-período: `r = (V₁ − V₀ − F) / (V₀ + Σ Fᵢ·wᵢ)`, com `wᵢ = (T − tᵢ)/T` em dias corridos do sub-período. Encadeamento: `R = ∏(1+rᵢ) − 1`.
- Janelas expostas: mês, YTD, 12m, desde o início, entre reuniões — todas derivadas do mesmo encadeamento (nunca recalculadas por caminho diferente).
- **Decomposição patrimonial:** `ΔPatrimônio = fluxos líquidos + rendimento`, onde rendimento = `V₁ − V₀ − F` somado nos sub-períodos (consistência garantida por teste de propriedade).
- Retorno ponderado por dinheiro (XIRR): **v1.1** — registrado como não suportado.

## 5. Benchmarks e comparação

- **CDI acumulado:** `∏(1 + fator_diárioᵢ − 1... )` — produto dos fatores diários da janela (convenção §2), fechado na mesma data-base da carteira.
- **IPCA acumulado:** produto dos mensais; mês corrente pro-rata (mesma convenção do §3.3).
- **Ibovespa:** variação de fechamentos entre as datas-base.
- **% do benchmark:** `R_carteira / R_benchmark × 100`, calculado apenas quando `R_carteira ≥ 0` e `R_benchmark > 0` na mesma janela; caso contrário exibe-se **diferença em pontos percentuais**, com explicação do motivo no próprio relatório (decisão do fundador, 2026-07-03 — prática confirmada com clientes).

## 6. Risco e estrutura (v1)

| Métrica | Definição |
|---|---|
| Volatilidade | Desvio-padrão amostral dos retornos dos sub-períodos, anualizado por `√(nº de sub-períodos/ano)`; exposta somente com ≥ 12 observações (senão: "histórico insuficiente") |
| Drawdown máximo | Maior queda pico-a-vale da série de índice encadeado |
| Concentração de emissor (crédito) | Soma por emissor sobre classes de risco de crédito ÷ patrimônio total; referência 15% e teto FGC R$ 250 mil |

**Parametrização (decisão do fundador, 2026-07-03):** todos os limiares desta seção (concentração, FGC, janela de vencimentos, observações mínimas de volatilidade, medianas de custo) são **parâmetros do motor com defaults de v1** — nunca constantes fixas no código. A configuração por organização/perfil (política de investimentos própria) entra no DOMAIN_MODEL como `OrganizationPolicy` e ganha interface na v1.1.
| Concentração por classe/indexador | Participações diretas sobre o total |
| Escada de liquidez | Buckets D0 / ≤30 / 31–360 / >360 dias, por regra de resgate ou vencimento (o menor dos dois) |
| Vencimentos | Janela de 90 dias a partir da data-base |
| Custos | Taxa de administração ponderada; comparação vs. mediana da classe no universo CVM (v1 calcula a mediana do universo de fundos com informe; até lá, referência declarada) |

## 7. Proveniência e política de precisão

Todo output carrega: `run_id`, versão do motor, fonte e data de cada preço/indexador usado. **Tolerância dourada:** divergência ≤ 0,01% contra cálculo manual conferido pelo fundador; acima disso o caso não entra em produção. Divergência entre posição derivada e informada acima de 0,10% do valor da posição gera flag de reconciliação (nunca ajuste silencioso).

## 8. Decisões do fundador (revisão de especialista, 2026-07-03)

1. **§3.2 — Curva na v1: aprovado.** Comportamento consistente com o extrato do custodiante; marcação a mercado com alternância de critério registrada como requisito futuro.
2. **§3.3 — VNA exato: determinado.** Máxima precisão e aderência às metodologias oficiais; convenção simplificada rejeitada; fallback de projeção documentado como imprecisão temporária sinalizada.
3. **§5 — Regra do %CDI negativo: aprovada.** Diferença em p.p. + explicação do motivo no relatório.
4. **§6 — Limiares: aprovados como defaults, com exigência de parametrização** por escritório/perfil (nunca constantes fixas).

**Changelog:** v1.0 (2026-07-03) — versão inicial para aprovação. · v1.1 (2026-07-03) — aprovada com as 4 decisões do fundador incorporadas (§2, §3.2, §3.3, §5, §6).
