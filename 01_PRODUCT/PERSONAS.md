# PERSONAS.md — Personas do Beachhead

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final — **personas provisórias**: construídas a partir da experiência do fundador (assessor) e da análise de mercado; serão corrigidas com as entrevistas da Fase 0 |
| **Subordinado a** | [STRATEGY.md §4 (ICP)](../00_FOUNDATION/STRATEGY.md) |

---

## Como usar este documento

Toda decisão de produto e de cópia deve citar qual persona atende. Feature que não serve a nenhuma das três não entra. As personas são arquétipos do ICP — não médias estatísticas — e cada uma carrega a pergunta que ela fará na demo e a objeção que fará no fechamento.

---

## P1 — Ricardo, o sócio de consultoria CVM *(persona primária)*

**Contexto.** 52 anos, sócio-fundador de consultoria de valores mobiliários registrada na CVM com 9 profissionais e ~160 famílias atendidas (patrimônio médio R$ 4 mi). Ex-private banker. Remuneração 100% fee. Multi-custódia: clientes têm conta em 3–5 instituições.

**Semana típica.** 8–12 reuniões de revisão com clientes. Cada uma consome 2–4 horas de preparação de alguém da equipe: baixar posições de vários portais, consolidar em Excel, montar PowerPoint no padrão da casa, conferir números (já erraram na frente de cliente — o trauma é vivo).

**Dores (na ordem dele).** (1) O gargalo de preparação limita quantas famílias cada profissional atende — contratar analista custa R$ 10 mil+/mês e treinar leva 6 meses; (2) padrão inconsistente entre profissionais da casa; (3) a CVM exige processo documentado e a documentação real está espalhada em e-mails e planilhas; (4) medo de errar número.

**O que o faz comprar.** Alavancagem: mesmas 9 pessoas atendendo 240 famílias com padrão melhor. Compra pelo escritório inteiro (plano Escritório) se confiar nos números.
**A pergunta na demo:** *"Esse retorno aí bate com o que a XP mostra? Como você calculou?"* — a trilha de auditoria responde.
**A objeção no fechamento:** *"Meus dados de clientes vão para onde? Quem mais vê?"* — LGPD, isolamento por tenant e o compromisso de nunca monetizar dados respondem.
**Mede sucesso por:** horas de preparação por reunião (de 3h para 20min) e zero erros de número no semestre.

## P2 — Marina, a wealth manager independente *(persona de adoção rápida)*

**Contexto.** 38 anos, saiu de um multi family office para abrir a própria gestão de patrimônio com uma sócia e um estagiário. 45 famílias, crescendo por indicação. Faz *tudo*: prospecção, análise, reunião, admin.

**Dores.** (1) É ela quem prepara cada reunião — noites e fins de semana; (2) precisa parecer instituição grande ("por que sair do banco para ficar com você?" — a resposta é a qualidade do material e da análise); (3) não pode contratar analista ainda; (4) perde negócios por capacidade, não por demanda.

**O que a faz comprar.** É a compradora ideal do plano Profissional: decide sozinha, dor aguda, ciclo de venda curto. Nossa "equipe de análise invisível".
**A pergunta na demo:** *"Consigo colocar minha marca no relatório?"* — sim, o material é dela (princípio "o profissional é o herói").
**A objeção:** preço — R$ 1.180/mês (2 assentos) pesa no começo. Resposta: uma noite de domingo livre por semana e material que fecha clientes novos; trial com as carteiras reais dela.
**Mede sucesso por:** conseguir aceitar as próximas 10 famílias sem contratar.

## P3 — Eduardo, o gestor de multi family office *(persona de exigência máxima)*

**Contexto.** 45 anos, CFA, um dos 6 profissionais de um MFO com 28 famílias de patrimônio alto (R$ 20–300 mi cada). Carteiras complexas: fundos exclusivos, previdência, imóveis, offshore, ativos ilíquidos. Comitê de investimentos trimestral com ata formal.

**Dores.** (1) Consolidação multi-custodiante + classes complexas: nenhuma ferramenta cobre tudo; (2) o comitê exige análise com rigor de banco e a produção é artesanal; (3) auditoria externa e compliance interno pedem rastreabilidade que a planilha não dá.

**O que o faz comprar.** Profundidade e auditabilidade. É o cliente que menos tolera limitação — e o que mais paga e mais retém. **Papel estratégico:** puxa a régua de qualidade do produto; **risco:** puxar o roadmap para classes de ativo de nicho cedo demais (offshore/ilíquidos são v2 — dizer não com clareza, conforme Princípio 2 da missão: declaramos a limitação).
**A pergunta na demo:** *"Como vocês marcam uma debênture incentivada sem liquidez? E se eu discordar do preço?"* — resposta: metodologia aberta + possibilidade de override manual **com registro de quem e por quê** (auditável).
**A objeção:** *"Meu processo é diferente do de vocês"* — templates e política por organização respondem em parte; o resto é disciplina de não customizar (anti-ICP 2 vigia a fronteira).
**Mede sucesso por:** passar auditoria externa apontando a plataforma como fonte, sem planilha paralela.

## Anti-persona — Fábio, o assessor cativo de plataforma

35 anos, assessor em escritório 100% XP. A dor parece igual (preparar reuniões), mas: os dados dele vivem no hub da XP (que já lhe dá ferramenta subsidiada com IA), a remuneração é comissional (menor pressão por demonstrar valor analítico) e o escritório decide software por ele. **Vender para Fábio é churn anunciado e desvio de roadmap** — educadamente, não. Reavaliar apenas na Fase 3, no recorte de assessores independentes/fee-based (STRATEGY.md §6).

---

## Síntese para decisões de produto

| Tema | Ricardo (P1) | Marina (P2) | Eduardo (P3) |
|---|---|---|---|
| Plano | Escritório | Profissional | Escritório/Instituição |
| Gatilho de compra | Alavancar equipe | Parecer grande | Rigor + auditoria |
| Feature decisiva | Padrão da casa + permissões | Material com a marca dela | Trilha de auditoria + metodologia aberta |
| Risco de produto | Exigir CRM | Sensível a preço | Puxar nicho cedo demais |
| Prioridade no MVP | **1º** | **1º** (mesmo core) | 2º (servir bem no comum, declarar limites no complexo) |

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total; revisão obrigatória pós-Fase 0.
