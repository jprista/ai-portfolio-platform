# CONSENSUS_RADAR.md — Radar de Consenso e Proposta Assistida

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-06 |
| **Status** | Direcionamento **aprovado pelo fundador** (2026-07-06: listas da casa + lacunas + proposta assistida + inteligência das grandes casas); especificação registrada para implementação na trilha v1.1, após a fiação do app aos dados reais |
| **Subordinado a** | [MISSION.md](../00_FOUNDATION/MISSION.md) (Princípio 1, anti-objetivo 2) · [API_SPEC.md](API_SPEC.md) |

---

## 1. O que o fundador pediu, traduzido para o produto legal

> "Quero que sugiram para mim ativos que as maiores casas de analistas, gestoras e bancos do mundo estão recomendando e negociando. Com isso e com os ativos aprovados do meu escritório, teremos a melhor oportunidade de acerto."

Dois caminhos para essa inteligência — um proibido, um poderoso:

- **Proibido:** redistribuir *relatórios e recomendações proprietárias* (research de bancos/corretoras é licenciado; revender = violação de PI e contrato) ou a plataforma "recomendar sozinha" (fronteira CVM 19/21 e anti-objetivo 2 da missão).
- **Poderoso e legal:** observar **o que as grandes casas FAZEM e DETÊM** — informação pública por obrigação regulatória — e entregá-la como **evidência organizada** para a decisão do profissional. O que os melhores fazem vale mais do que o que os relatórios dizem.

## 2. Fontes (validadas ao vivo em 2026-07-06)

| Fonte | O que revela | Base legal | Defasagem |
|---|---|---|---|
| **CVM — CDA** (dados.cvm.gov.br) ✅ testado | Carteira mensal de **todos os fundos brasileiros**: o que as maiores gestoras do país detêm, compraram e venderam | Dado público oficial | ~1–3 meses (janela de sigilo) |
| **SEC — 13F** (EDGAR) ✅ testado | Posições trimestrais das maiores gestoras do mundo (Berkshire, Bridgewater, BlackRock…) em ações listadas nos EUA | Dado público oficial | ~45 dias |
| **Cartas de gestão públicas** | Teses e movimentos declarados pelas próprias gestoras | Documento público de divulgação; **resumo com atribuição e link**, nunca reprodução | Mensal/trimestral |
| **Consenso de analistas** (compra/venda/preço-alvo) | Visão agregada do sell-side sobre ações listadas | **Somente via licenciamento** (LSEG/Bloomberg ou provedor local) — avaliar custo na Fase 2; sem licença, não exibimos | Diária |
| Tesouro/B3/BCB (já integrados) | Contexto de taxas e mercado local | Público | Diária |

## 3. O produto: Radar de Consenso → Proposta Assistida

1. **Radar de Consenso** (nova área da plataforma): por ativo/classe, painéis de evidência — *"presente na carteira de N das 20 maiores gestoras BR"*, *"posição aumentada por X e Y no último tri (13F)"*, *"citado em cartas de Z gestoras"* — sempre com fonte, data e defasagem declaradas.
2. **Cruzamento com as listas da casa:** os ativos aprovados do escritório ganham o selo de evidência do radar ("dos 14 ativos da sua lista de RF inflação, estes 5 aparecem no radar"). A curadoria continua sendo do escritório.
3. **Proposta assistida:** o motor detecta lacunas vs. política do cliente → o rascunho da proposta puxa candidatos **das listas da casa**, cada um acompanhado do painel de evidências do radar → o profissional escolhe, ajusta e assina → trilha documenta autoria, evidências consideradas e versões.

**Invariante preservada:** a plataforma organiza evidência e monta rascunho; **a recomendação é do profissional** — com prova melhor do que ele teria sozinho.

## 4. O que NUNCA fazemos aqui

Reproduzir/redistribuir research proprietário sem licença · exibir "compre X" em nome da plataforma · ocultar defasagem dos dados (13F/CDA são fotos atrasadas — sempre declarado) · usar dados de carteiras dos NOSSOS clientes como "consenso" (anti-objetivo 4).

## 5. Sequenciamento

(1º) fiação do app aos dados reais + auth (bloco atual) → (2º) pipeline CDA/13F + Radar v1 (gestoras BR + globais) → (3º) listas da casa + proposta assistida → (4º) consenso de analistas licenciado (avaliar custo/benefício na Fase 2).

**Changelog:** v1.0 (2026-07-06) — registro da decisão e do desenho.
