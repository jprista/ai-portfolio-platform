# BUSINESS_MODEL.md — Modelo de Negócio e Unit Economics

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Donos** | João Pedro (fundador) · Claude (CTO fundador) |
| **Status** | Final (produzido sob delegação total; ciclo interno de rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [MISSION.md](MISSION.md) · [STRATEGY.md](STRATEGY.md) |

---

## 1. Por que este documento existe

Transforma as decisões de estratégia (assinatura SaaS, nunca AUM, premium justificado) em números operáveis: planos, preços, custos unitários, margens, ponto de equilíbrio e projeções com premissas explícitas. Toda premissa aqui é **hipótese numerada (H1–H8)** até ser calibrada pelas entrevistas da Fase 0 e pelos primeiros contratos — este documento obrigatoriamente é revisado ao final da Fase 0.

## 2. Princípios de monetização (herdados e derivados)

1. **Receita exclusivamente de software** (Princípio 4 da missão — sem rebates, distribuição ou dados).
2. **Nunca % de AUM** (decisão do fundador). Além da preferência, há lógica: cobrar por AUM nos colocaria na cadeia de valor financeira e enfraqueceria a neutralidade percebida.
3. **Preço ancorado em valor, não em custo:** substituímos 6–10h/semana de trabalho analítico por profissional — o equivalente a uma fração de um analista júnior (R$ 8–15 mil/mês + encargos). Nosso teto de preço é uma fração disso; nosso piso é o que sustenta margem ≥ 75%.
4. **Premium justificado:** nunca seremos a opção mais barata. Contra Excel (gratuito) vendemos tempo e padrão; contra consolidadores vendemos a análise que eles não fazem.
5. **Simplicidade radical de planos:** um eixo só (assentos), sem matriz de features confusa. Features de compliance/auditoria estão em TODOS os planos — auditabilidade não é upsell, é identidade (seria incoerente cobrar extra pelo que a missão diz ser inegociável).

## 3. Estrutura de planos (H1)

| Plano | Alvo | Preço (H1) | Inclui |
|---|---|---|---|
| **Profissional** | Consultor/gestor solo ou dupla (1–4 assentos) | **R$ 590/assento/mês** | Tudo: ingestão, motor completo, análises, preparação de reunião, relatórios com sua marca, trilha de auditoria |
| **Escritório** | Organizações de 5–14 assentos | **R$ 490/assento/mês** (mín. R$ 2.450/mês) | Tudo do Profissional + papéis e permissões, templates da casa, visão consolidada da carteira de clientes da firma |
| **Instituição** | 15+ assentos | **R$ 420/assento/mês** (piso R$ 6.300/mês) | Tudo + SSO, SLA formal, exportações em massa, onboarding assistido |
| Anual antecipado | Todos | **–15%** | Fluxo de caixa antecipado — vital em bootstrap |
| Design partner | 5 vagas (Fase 0/1) | **–50% por 12 meses** | Conforme STRATEGY.md §7; preço de tabela no 13º mês |

Notas de desenho: (a) o valor mínimo por organização evita contas de 5 assentos pagando por 1; (b) não há plano gratuito — trial de 14 dias com dados reais, guiado; freemium em B2B fiduciário atrai curiosos e gera custo de dado/LLM sem receita; (c) preços B2B dos concorrentes são opacos (pesquisa 2026-07) — coletar nos roteiros da Fase 0 (DISCOVERY_PLAYBOOK) e recalibrar.

## 4. Custos unitários (H2–H4)

Estimativas por **assento ativo/mês**, em uso intenso (4–8 reuniões preparadas/mês, ~30 carteiras acompanhadas):

| Componente | Estimativa | Premissa |
|---|---|---|
| LLM (análises, narrativas, relatórios, parsing) | R$ 45–90 | H2: ~2–4M tokens/assento/mês em Claude (mix Sonnet/modelo maior), com cache de contexto |
| Agregador Open Finance (por conta conectada) | R$ 20–45 | H3: R$ 1–3/conexão/mês × 15–30 clientes finais por assento — **maior incerteza de custo; negociar contrato com trava de volume**. ⚠️ Spike 2026-07-03 ([SPIKE_001](../02_ARCHITECTURE/spikes/SPIKE_001_DATA_SOURCES.md)): há piso de plataforma (~R$ 2,5–6 mil/mês) além do custo por conexão — entra nos fixos até diluir; contratação adiada para M2 da Fase 1 com negociação startup |
| Dados de mercado e referência | R$ 5–15 | H4: fontes públicas (CVM, Tesouro, BCB/SGS) + cotações via provedor de baixo custo, amortizado |
| Infraestrutura (compute, DB, storage, observabilidade) | R$ 8–15 | Serverless/managed, região BR |
| **COGS total/assento/mês** | **R$ 78–165** | |

**Margem bruta resultante:** 72–87% no plano Profissional (alvo ≥ 75%; se H2/H3 estourarem, ajustar preço ou arquitetura de tokens antes de aceitar margem < 70%).

## 5. Custos fixos e ponto de equilíbrio (H5)

| Item | Mensal |
|---|---|
| Retirada do fundador (H5 — **a confirmar com João Pedro**) | R$ 25.000 |
| Ferramentas da empresa-IA (Claude Max/API de desenvolvimento, SaaS diversos) | R$ 3.000–5.000 |
| Contabilidade, jurídico recorrente, seguros | R$ 2.500 |
| Marketing/eventos de nicho (Fase 2) | R$ 2.000 |
| **Total** | **~R$ 33.000–35.000** |

**Ponto de equilíbrio: MRR ≈ R$ 42.000** (fixos ÷ margem bruta 80%) — consistente com o marco de sustentabilidade do STRATEGY.md (~mês 12 da Fase 2). Regra de caixa: reserva mínima de 6 meses de fixos; qualquer decisão que a fure exige revisão da estratégia.

## 6. Projeções — dez/2027 (fim da Fase 2)

Premissas: ticket médio por organização R$ 2.200/mês (mix de planos, H6); churn lógico 2%/mês (H7); venda 100% founder-led com 15% de taxa de conversão demo→contrato (H8).

| Cenário | Organizações | MRR | Situação |
|---|---|---|---|
| Conservador | 18 | ~R$ 40 mil | Equilíbrio apertado; Fase 3 adiada |
| **Base** | **30** | **~R$ 66 mil** | Meta do STRATEGY.md; equilíbrio + margem para reserva |
| Otimista | 45 | ~R$ 100 mil | Antecipar Gate 2→3 e discussão de capital |

Sanidade do funil (cenário base): 30 contratos ÷ 15% conversão = 200 demos em ~18 meses ≈ 3 demos/semana — factível para founder-led com rede própria, mas é **o gargalo da empresa**: o tempo de venda do fundador, não a tecnologia.

## 7. LTV, CAC e saúde do modelo

- **Vida média do cliente** @ churn 2%/mês ≈ 50 meses. LTV bruto (ticket R$ 2.200 × 50 × margem 80%) ≈ **R$ 88 mil por organização**.
- **CAC founder-led** (tempo do fundador + deslocamentos + material) ≈ R$ 2–4 mil → LTV/CAC > 20; payback < 2 meses. Números excelentes *se* o churn de 2% se confirmar — em SaaS B2B de nicho o churn real só aparece no mês 13 (primeira renovação anual). Tratar H7 como a premissa mais frágil do modelo.
- **Expansão (NRR):** crescimento de assentos dentro das organizações (contratam profissionais novos) + upgrade de plano. Alvo NRR ≥ 110% na Fase 2 — em beachhead pequeno, crescer *dentro* dos clientes vale mais que caçar logos.

## 8. Riscos do modelo e gatilhos de revisão

| Gatilho | Ação |
|---|---|
| Entrevistas da Fase 0 indicarem disposição a pagar < R$ 350/assento | Repensar empacotamento (cobrar por organização, não assento) antes de baixar preço |
| COGS de LLM ou agregador > 35% do preço | Rearquitetura de tokens/cache e renegociação de contrato de dados |
| Churn > 3,5%/mês por 2 meses seguidos na Fase 2 | Congelar aquisição; diagnóstico de valor (R3 do STRATEGY.md) |
| 2 design partners pedirem white-label pagando 3x | Não aceitar (anti-objetivo); registrar como sinal para a Fase 3 |

## 9. Governança

Revisão obrigatória: ao final da Fase 0 (calibragem por entrevistas), a cada gate, ou quando qualquer gatilho do §8 disparar. **Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
