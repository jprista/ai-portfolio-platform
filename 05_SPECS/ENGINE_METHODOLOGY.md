# ENGINE_METHODOLOGY.md — Metodologia de Cálculo do Motor (v1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | **Aguardando aprovação do fundador** — este documento é a verdade financeira do produto; a revisão dele é papel de auditor, não de leitor |
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
| Fatores diários de CDI | Convenção B3/CETIP: fator diário = `(1 + DI/100)^(1/252)`, **truncado em 8 casas decimais**; percentual de CDI aplica-se sobre o excesso: `1 + (fator_diário − 1) × p` |
| Arredondamento de exibição | Valores monetários: 2 casas (half-even). Percentuais: cálculo em 4+ casas, exibição em 2 |
| Datas de preço | Todo preço/cota carrega a data efetiva; posição valorizada com dado defasado ≥ 3 dias úteis rebaixa o selo de confiança (DATA_STRATEGY §5) |
| Reprodutibilidade | Todo cálculo referencia o snapshot de inputs do `AnalysisRun` (I2); rodar duas vezes com o mesmo snapshot produz bytes idênticos |

## 3. Valorização por classe de ativo (v1)

### 3.1 Caixa e CDB de liquidez diária (% CDI)
`V_t = V_0 × ∏ᵢ [1 + (fator_CDIᵢ − 1) × p]` para cada dia útil `i` desde a última posição confirmada, com `p` = percentual contratado. Fonte do CDI: BCB/SGS série 12.

### 3.2 RF bancária prefixada (CDB/LCI/LCA pré)
Marcação **na curva** (accrual da taxa contratada): `V_t = P × (1 + taxa)^(du(aplicação, t)/252)`. Não marcamos a mercado papel bancário na v1 — **limitação declarada** no material (mercado secundário ilíquido; é a prática padrão de extratos de custódia).

### 3.3 RF bancária IPCA+ 
`V_t = P × F_IPCA(aplicação → t) × (1 + taxa_real)^(du/252)`, onde `F_IPCA` acumula IPCA mensal (BCB/SGS 433) com **pro-rata por dias úteis no mês corrente e defasagem de divulgação de 1 mês** (convenção de VNA simplificada). A defasagem exata usada é registrada na nota metodológica do relatório.

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
- **% do benchmark:** `R_carteira / R_benchmark × 100`, calculado apenas quando ambos ≥ 0 e mesma janela; caso contrário exibe-se diferença em pontos percentuais (evita o clássico "%CDI" sem sentido com retorno negativo).

## 6. Risco e estrutura (v1)

| Métrica | Definição |
|---|---|
| Volatilidade | Desvio-padrão amostral dos retornos dos sub-períodos, anualizado por `√(nº de sub-períodos/ano)`; exposta somente com ≥ 12 observações (senão: "histórico insuficiente") |
| Drawdown máximo | Maior queda pico-a-vale da série de índice encadeado |
| Concentração de emissor (crédito) | Soma por emissor sobre classes de risco de crédito ÷ patrimônio total; referência 15% e teto FGC R$ 250 mil (parametrizáveis por organização na v1.1) |
| Concentração por classe/indexador | Participações diretas sobre o total |
| Escada de liquidez | Buckets D0 / ≤30 / 31–360 / >360 dias, por regra de resgate ou vencimento (o menor dos dois) |
| Vencimentos | Janela de 90 dias a partir da data-base |
| Custos | Taxa de administração ponderada; comparação vs. mediana da classe no universo CVM (v1 calcula a mediana do universo de fundos com informe; até lá, referência declarada) |

## 7. Proveniência e política de precisão

Todo output carrega: `run_id`, versão do motor, fonte e data de cada preço/indexador usado. **Tolerância dourada:** divergência ≤ 0,01% contra cálculo manual conferido pelo fundador; acima disso o caso não entra em produção. Divergência entre posição derivada e informada acima de 0,10% do valor da posição gera flag de reconciliação (nunca ajuste silencioso).

## 8. Pontos que exigem a sua revisão de especialista (antes de aprovar)

1. **§3.2** — concorda em marcar papel bancário **na curva** na v1 (padrão de extrato), deixando marcação a mercado para depois?
2. **§3.3** — a convenção de IPCA com defasagem de 1 mês e pro-rata por DU é a que você quer apresentar a cliente, ou prefere a convenção exata de VNA com data de aniversário?
3. **§5** — a regra de não exibir "%CDI" quando o retorno é negativo (trocando por diferença em p.p.) corresponde à sua prática com clientes?
4. **§6** — os limiares de referência (15% emissor, 90 dias de vencimento, 12 observações para vol) fazem sentido para o seu mercado?

**Changelog:** v1.0 (2026-07-03) — versão inicial para aprovação.
