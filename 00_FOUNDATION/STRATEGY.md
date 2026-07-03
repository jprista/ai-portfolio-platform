# STRATEGY.md — Estratégia de Entrada e Crescimento

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Donos** | João Pedro (fundador) · Claude (CTO fundador) |
| **Status** | **Aprovado** pelo fundador em 2026-07-03, sem ressalvas (premissas do §8 sobre horas do fundador e termos de design partners valem como escritas) |
| **Subordinado a** | [MISSION.md](MISSION.md) — em conflito, a missão prevalece |
| **Informado por** | [MARKET_ANALYSIS.md](MARKET_ANALYSIS.md) |

---

## 1. Por que este documento existe

Define onde jogamos, como vencemos, em que ordem e com quais metas — sob a restrição que domina tudo: **fundador solo, bootstrap, MVP robusto em ~6 meses**. Seu teste de qualidade: dizer **não** a quase tudo, e dizer **quando mudaríamos de ideia** (kill criteria, §9). Nenhum documento de produto ou arquitetura pode contradizê-lo sem revisão formal.

## 2. Diagnóstico — o problema estratégico em um parágrafo

O wealth independente brasileiro cresce e se profissionaliza (consultorias CVM dobraram desde 2020; fee-based avançando), mas a tecnologia disponível parou na camada de *consolidação* (Gorila, Smartbrain: mostram a foto da carteira) ou na camada de *dados brutos* (Comdinheiro, Quantum: exigem analista treinado). O trabalho que consome o profissional — analisar a carteira, preparar a reunião, produzir material com padrão institucional, documentar o processo — permanece manual, em Excel e PowerPoint. Os incumbentes têm dados, mas conflitos e dívida técnica; os globais não tratam ativos brasileiros; os bancos constroem só para si. Existe uma janela — estimo 12–24 meses antes que a Gorila suba a pilha com competência — para ocupar a camada de **análise institucional pronta para a reunião**.

## 3. Política orientadora

**Onde jogamos:** mid-market fiduciário brasileiro — consultorias CVM, wealth managers independentes e family offices — no momento de maior valor do trabalho deles: **a preparação e condução da reunião com o cliente final**.

**Como vencemos:** entregando em minutos, com auditabilidade total, o que hoje exige horas de um analista — e fazendo isso com uma estrutura de custo que só uma empresa operada por IA consegue ter.

**A aposta central desta estratégia:** venceremos não por termos mais features que a Gorila, mas por sermos donos de um *workflow* (a reunião) enquanto eles são donos de um *dado* (a posição consolidada). Dado sem workflow é substituível; workflow vira hábito, e hábito vira contrato renovado.

## 4. Cliente ideal (ICP v1) — e quem recusamos

### ICP

| Dimensão | Perfil |
|---|---|
| Organização | Consultoria CVM, wealth manager independente ou MFO com **2–20 profissionais** e **50–500 famílias/clientes ativos** |
| Operação | Multi-custódia (2+ custodiantes), remuneração fee-based ou fiduciária |
| Usuário primário | Sócio-consultor / gestor de relacionamento que conduz reuniões com clientes finais |
| Sintoma qualificador | Produz material de reunião manualmente (Excel/PowerPoint); ciclo de revisões trimestrais; reclama de tempo gasto em análise repetitiva |
| Momento de compra | Crescendo em clientes sem poder contratar analistas na mesma proporção |

### Anti-ICP (recusamos educadamente, e por quê)

1. **Escritórios cativos de hub de plataforma** (assessoria 100% XP/BTG) — a ferramenta da casa é subsidiada e o dado é cativo; venda ruim, churn certo.
2. **Single family office querendo sistema sob medida** — é projeto de consultoria, viola o anti-objetivo 5 da missão.
3. **Quem quer que "a IA recomende sozinha"** — viola o Princípio 1 da missão e a Resolução CVM 19/21.
4. **Bancos e grandes instituições** — ciclo de 18 meses que um bootstrap não sobrevive; voltamos a eles na Fase 3.
5. **Investidor final** — não somos B2C (anti-objetivo 3), sem exceções "só dessa vez".

## 5. Posicionamento

> Para **consultorias, wealth managers e family offices independentes** que precisam demonstrar valor analítico e cumprir dever fiduciário, somos **a plataforma de inteligência de carteiras que entrega análise de nível institucional pronta para a reunião com o cliente** — diferente dos consolidadores, que mostram a foto da carteira mas não a explicam, nós analisamos, fundamentamos, produzimos o material e documentamos o processo. Todo número auditável; nenhuma recomendação de caixa-preta.

**Mensagem-síntese:** *"Chegue em toda reunião com o trabalho de uma equipe de análise — sem ter uma."*

Contra cada alternativa: vs. **Excel/PowerPoint** (o concorrente real nº 1): horas → minutos, com padrão e trilha de auditoria. vs. **Gorila**: eles consolidam, nós analisamos e preparamos; e não somos sócios de ninguém do seu mercado. vs. **Comdinheiro/Quantum**: eles vendem dados para quem sabe a pergunta; nós entregamos a resposta pronta. vs. **contratar um analista** (R$ 8–15 mil/mês + encargos): fração do custo, disponível 24/7, sem turnover.

## 6. Sequenciamento — fases com gates

A regra: **nenhuma fase começa sem o gate da anterior**. Datas são alvos; gates são obrigatórios.

### Fase 0 — Validação (jul–set/2026)
- 15–20 entrevistas estruturadas no ICP (roteiro incluirá: ranking das dores, processo atual da reunião, ferramentas e preços pagos hoje — para suprir a opacidade de preços B2B do mercado — e teste de disposição a pagar).
- Protótipo demonstrável (carteira real → análise + material de reunião) construído em paralelo, para transformar entrevista em pré-venda.
- **Gate 0→1:** ≥ 5 organizações comprometidas como design partners **com compromisso financeiro** (ver §7) e dor da reunião confirmada como top-2 em ≥ 60% das entrevistas.

### Fase 1 — MVP com design partners (out/2026–mar/2027)
- Construção do MVP robusto (escopo em `01_PRODUCT/MVP_SCOPE.md`) com uso semanal real dos design partners desde o primeiro mês (não beta silencioso).
- Prova técnica de cobertura de dados: Open Finance + parsing precisa cobrir ≥ 70% do patrimônio típico dos design partners.
- **Gate 1→2:** ≥ 3 design partners usando a plataforma **toda semana** para reuniões reais (métrica-estrela) + pagando preço de tabela ao fim do período de design partner + NPS qualitativo "não voltaria ao processo antigo".

### Fase 2 — Repetibilidade comercial (abr–dez/2027)
- Escalar de 5 para 25–40 organizações pagantes; playbook de venda documentado; onboarding sem toque do fundador em < 2 semanas.
- **Metas ao fim da fase (dez/2027):** MRR ≥ R$ 60 mil · métrica-estrela ≥ 150 reuniões/semana · churn lógico < 2%/mês · receita cobrindo custo integral da operação e do fundador (ponto de equilíbrio ≈ MRR R$ 42 mil, calculado em BUSINESS_MODEL.md §5 — alvo para o mês 12 da fase).
- **Gate 2→3:** metas acima + demanda comprovada de um segundo segmento chegando *inbound*.

### Fase 3 — Expansão (2028+)
- Ordem de expansão: (1º) assessores independentes/fee-based fora de hubs; (2º) gestoras de patrimônio maiores; (3º) API para agentes como produto; (4º) geografia (LatAm/mercados de complexidade local alta). Bancos por último, como clientes enterprise ou adquirentes.

## 7. Go-to-market

**Motion:** founder-led sales — o João Pedro é assessor, fala a língua do cliente e tem a rede. Nenhum vendedor contratado antes do Gate 2.

**Programa de design partners (estrutura):** 5 vagas. Recebem: 50% de desconto por 12 meses, influência direta no roadmap, acesso quinzenal ao fundador. Devem: compromisso financeiro desde o dia 1 (mesmo simbólico — R$ 500–1.000/mês — pele em jogo é o que separa feedback de cortesia), uso em reuniões reais, feedback estruturado quinzenal e direito nosso a case público ao final. Sem desconto vitalício: gratidão eterna cria clientes que valem menos do que custam.

**Preço (hipótese a calibrar nas entrevistas; detalhe em BUSINESS_MODEL.md):** assinatura por profissional (faixa-hipótese R$ 400–900/mês) + planos organizacionais por tamanho (faixa-hipótese R$ 2–8 mil/mês). Âncora de valor: substituímos 6–10h/semana de trabalho analítico (fração do custo de um analista júnior). Nunca % de AUM (decisão do fundador, 2026-07-03). Posição: **premium justificado** — competir por preço contra quem tem R$ 100 mi em caixa é suicídio; competimos por resultado.

**Autoridade:** conteúdo técnico de nicho (análise de carteira bem feita, regulação CVM + IA, renda fixa calculada corretamente) assinado pelo fundador, produzido com apoio de agentes — o objetivo é ser *a* referência técnica do segmento antes de ter budget de marketing.

**O duplo papel do fundador — tratamento explícito:** ser assessor ativo é a origem da credibilidade ("construído por quem vive a dor") e um risco de percepção (concorrência com potenciais clientes; neutralidade da plataforma). Mitigação: transparência total no pitch; a neutralidade estrutural da empresa (Princípio 4 — sem rebates, sem distribuição, sem participação em clientes) vale independentemente da pessoa; e fica registrado o **compromisso de revisão**: se o duplo papel custar ≥ 2 negócios documentados ou ao atingirmos o Gate 1→2, a dedicação exclusiva entra em pauta formalmente.

## 8. Modelo operacional — a empresa-IA

A restrição "fundador solo + bootstrap" só fecha com um modelo operacional novo: **um fundador de domínio + um CTO-IA + agentes especializados**, no lugar dos ~10 funcionários que este plano exigiria em 2022.

| Função | Quem executa | Papel do humano |
|---|---|---|
| Estratégia, produto, prioridade | João Pedro + Claude | Decisão final sempre do fundador |
| Arquitetura e desenvolvimento | Claude + agentes de código (implementação, testes, revisão em paralelo) | Aprovação de decisões estruturais |
| Motor quantitativo | Claude + agentes, **com validação por suíte de testes dourados** (casos calculados e conferidos manualmente) | O fundador confere números como um auditor — Crença C6: precisão é binária |
| Pesquisa contínua (mercado, regulação, concorrência) | Agentes de pesquisa recorrentes | Leitura dos sumários |
| Conteúdo GTM | Agentes rascunham | Fundador dá voz, valida e assina |
| Vendas e relação com design partners | **João Pedro, exclusivamente** | IA prepara material; não vende, não se relaciona |
| Suporte (Fase 2+) | Agente de primeira linha | Escalação ao fundador |

**Implicação de custo:** burn mensal de infraestrutura + IA + dados estimado em R$ 3–8 mil/mês na Fase 1 — é isso que torna o bootstrap viável e é, em si, uma vantagem competitiva: nosso ponto de equilíbrio é ~50x menor que o de um concorrente com folha de pagamento tradicional.

**Orçamento de horas do fundador (a validar com ele):** Fase 0 ≈ 60% descoberta/vendas, 30% co-construção e validação de números, 10% administração. Se a disponibilidade real (dado o trabalho como assessor) for inferior a ~20h/semana, os prazos das fases devem ser recalculados *antes* de assumidos — prazo herói é dívida com juros.

## 9. Riscos estratégicos e kill criteria

| # | Risco | Resposta pré-combinada |
|---|---|---|
| R1 | **Validação falha:** < 30% das entrevistas confirmam a dor da reunião como top-2, ou não fechamos 5 design partners até out/2026 | Não construir o MVP. Voltar a MARKET_ANALYSIS.md e testar dor alternativa (compliance/suitability) no mesmo segmento antes de considerar outro segmento |
| R2 | **Cobertura de dados insuficiente:** Open Finance + parsing < 70% do patrimônio dos design partners | Ativar plano B do P3: negociar API de consolidador (inclusive Gorila — cliente deles antes que concorrente) e reavaliar custo/dependência |
| R3 | **Uso não vira hábito:** MVP entregue e < 3 design partners com uso semanal após 3 meses | Congelar GTM e novas features; imersão de produto até achar o gatilho do ritual semanal — problema de produto não se resolve vendendo mais |
| R4 | **Gorila lança workflow de reunião completo antes do nosso MVP** | Duplo down no que ela não pode copiar: profundidade quant + compliance nativo para consultorias CVM + neutralidade (o modelo societário deles é o nosso flanco) |
| R5 | **Solo founder é ponto único de falha** (saúde, tempo, capital pessoal) | Documentação contínua (este repositório é o backup do cérebro da empresa); marcos de caixa revisados a cada gate; sem contratação, mas rede de parceiros identificada na Fase 2 |
| R6 | **Prazo de 6 meses estoura por escopo** | O corte é sagrado no MVP_SCOPE.md: adiar features, nunca comprometer precisão (C6) nem auditabilidade (Princípio 3). Se precisão vs. prazo colidirem, o prazo perde |

## 10. O que explicitamente NÃO fazemos nas Fases 0–2

Consolidação como produto próprio · integrações proprietárias com custodiantes · app B2C · white-label · venda a bancos · internacionalização · contratação de funcionários · levantar capital (reavaliável no Gate 2→3, por decisão do fundador) · qualquer feature que não sirva à reunião com o cliente final.

## 11. Governança

- Revisão obrigatória: ao cruzar cada gate, ao disparar qualquer kill criterion, ou a cada 6 meses.
- Alterações exigem acordo dos dois fundadores, registradas em changelog.
- **Changelog:** v1.0 (2026-07-03) — versão inicial, aprovada pelo fundador. · v1.0.1 (2026-07-03) — correção de consistência: marco de sustentabilidade bootstrap ajustado de "R$ 35–40 mil" para "≈ R$ 42 mil", alinhado ao cálculo de ponto de equilíbrio do BUSINESS_MODEL.md §5 (sob delegação total).
