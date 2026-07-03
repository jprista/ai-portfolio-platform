# MISSION.md — Missão, Crenças e Princípios

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Donos** | João Pedro (fundador) · Claude (CTO fundador) |
| **Status** | **Aprovado** pelo fundador em 2026-07-03 |
| **Documentos relacionados** | [MARKET_ANALYSIS.md](MARKET_ANALYSIS.md) |

---

## 1. Por que este documento existe

Este é o documento mais permanente da empresa. Estratégia, produto e arquitetura mudarão muitas vezes; este documento só muda quando a realidade provar que uma crença nossa estava errada — e a Seção 6 define exatamente como saberemos.

Seu papel é prático, não cerimonial: **é uma ferramenta de decisão**. Diante de qualquer pedido de feature, proposta de parceria, oportunidade de receita ou tentação de pivô, a pergunta é: *"isso é compatível com quem dizemos ser?"*. Se este documento não conseguir rejeitar nada, ele falhou.

---

## 2. Missão

> **Colocar inteligência de nível institucional em cada decisão de investimento profissional — com a precisão, a auditabilidade e a neutralidade que o dever fiduciário exige.**

Cada palavra exclui alternativas:

- **"Inteligência de nível institucional"** — não somos dashboard nem consolidador de extratos. Entregamos o que hoje só existe dentro de grandes instituições: atribuição de performance, risco ex-ante, cenários, renda fixa calculada corretamente. Isso exclui análise superficial embalada em IA.
- **"Cada decisão"** — vivemos no fluxo de trabalho, no momento em que a decisão acontece (a preparação da reunião, a proposta, a revisão de carteira). Isso exclui ser mais um relatório mensal que ninguém abre.
- **"De investimento profissional"** — servimos o profissional que responde por clientes, não o investidor final. Isso exclui B2C.
- **"Precisão"** — números saem de motor determinístico, nunca de modelo generativo. Isso exclui atalhos de IA que alucinam basis points.
- **"Auditabilidade"** — toda análise é reproduzível, versionada e explicável. Isso exclui caixas-pretas, mesmo quando caixas-pretas seriam mais rápidas de construir.
- **"Neutralidade"** — não distribuímos produtos, não recebemos rebates, não competimos com nossos clientes. Isso exclui as formas mais fáceis de monetizar wealth tech.

## 3. Visão — o mundo em 2031

Ser **a camada de inteligência padrão do wealth management independente** — primeiro no Brasil, depois em mercados com complexidade local comparável — de modo que:

1. Toda reunião entre um profissional independente e seu cliente final é preparada, fundamentada e documentada pela nossa plataforma;
2. "Análise auditável" deixou de ser diferencial e virou exigência do mercado — porque nós elevamos a régua;
3. Quando agentes de IA consomem análise de carteiras na nossa região, consomem a nossa — somos a fonte que humanos e máquinas confiam.

**Sequência geográfica assumida:** profundidade local primeiro (Brasil), arquitetura global sempre (nenhuma decisão técnica pode assumir um único mercado, moeda ou idioma — ver Princípio 7). A expansão internacional é consequência de dominar mercados complexos, não um objetivo do dia 1.

## 4. O problema que existimos para resolver

O profissional de investimentos independente — consultor CVM, gestor de patrimônio, family officer, assessor fee-based — vive um paradoxo:

- **Cobra pelo seu julgamento**, mas passa a maior parte do tempo em trabalho que não é julgamento: consolidar posições, conferir números, montar PowerPoint, preencher documentação de suitability.
- **Tem dever fiduciário crescente** (regulação CVM apertando, clientes mais exigentes), mas ferramentas que não produzem evidência auditável do seu processo decisório.
- **Compete com instituições bilionárias** (bancos com copilotos de IA internos, plataformas verticalizadas) usando planilha, terminal de dados dos anos 2010 e consolidador que mostra a foto da carteira mas não a explica.

O custo disso é medido em horas por semana, em risco regulatório e — mais importante — em decisões de investimento piores do que poderiam ser.

## 5. Quem servimos

**Segmento-alvo (pressuposto P1, em validação — ver Seção 9):** o mid-market fiduciário brasileiro — consultorias de valores mobiliários (593 registradas, dobrou desde 2020), multi family offices e wealth managers independentes (~550 estruturas), gestores de patrimônio de pequeno e médio porte.

O que define nosso cliente não é o rótulo, é o perfil:

| Característica | Por que importa |
|---|---|
| Responde por clientes (dever fiduciário ou relação fee-based) | Precisa de evidência auditável do processo decisório |
| Opera multi-custódia | Nenhuma plataforma verticalizada o atende inteiro |
| Cobra pelo julgamento, não pela transação | Precisa demonstrar valor analítico continuamente |
| Pequeno demais para construir tecnologia própria | Compra software; não compete conosco |

**A quem servimos indiretamente:** o investidor final — que recebe análises melhores, decisões mais fundamentadas e transparência que hoje não tem. Ele é beneficiário, nunca usuário-alvo.

## 6. Crenças fundamentais — e o que as invalidaria

Crença sem critério de invalidação é dogma. Cada crença abaixo tem um sinal explícito de que estávamos errados; se o sinal ocorrer, este documento é revisado obrigatoriamente.

| # | Crença | O que a invalidaria |
|---|---|---|
| C1 | **O fosso é o motor quantitativo + workflow + confiança — nunca o LLM.** Modelos de fundação são commodity acessível a todos os concorrentes. | Modelos de fundação passarem a produzir cálculo financeiro auditável e reproduzível de ponta a ponta, sem motor externo, aceito por auditores e reguladores |
| C2 | **A consolidação de dados será comoditizada pelo Open Finance.** Não devemos gastar capital reconstruindo integrações custodiante a custodiante. | Estagnação do Open Investment (cobertura ou qualidade de dados insuficiente para uso profissional até meados de 2027), nos forçando a integrações proprietárias ou dependência estrutural de consolidadores |
| C3 | **O humano permanece no centro da relação de wealth no nosso horizonte de 10 anos.** IA municia o profissional; não o substitui. | Migração mensurável de patrimônio relevante para advisors 100% autônomos de IA no Brasil |
| C4 | **Regulação favorecerá quem nasceu auditável.** As diretrizes CVM sobre IA (esperadas 2026+) exigirão documentação, supervisão humana e explicabilidade. | CVM adotar postura permissiva duradoura que não diferencie plataformas auditáveis de caixas-pretas |
| C5 | **Interfaces migram para agentes em 3–5 anos.** Parte crescente do consumo de análise virá de agentes de IA, não de telas. | Adoção agêntica estagnar no mercado financeiro global até 2029 |
| C6 | **Precisão percebida é binária.** Um único número errado na frente do cliente final destrói a confiança do profissional na plataforma — não existe "95% correto" neste mercado. | (Autoevidente; funciona como restrição permanente de engenharia, não como aposta) |

## 7. Princípios inegociáveis

Princípios existem para resolver colisões entre dois bens. Cada um abaixo declara **o que sacrificamos**.

1. **O motor calcula, a IA traduz, o humano recomenda.** Nenhum número apresentado ao usuário nasce em modelo generativo; nenhuma recomendação de investimento sai da plataforma em nome próprio. *Sacrificamos:* velocidade de desenvolvimento e features "mágicas" que a concorrência pode lançar antes.
2. **Precisão antes de amplitude.** Uma classe de ativos só entra quando calculada em padrão institucional; até lá, declaramos a limitação abertamente. *Sacrificamos:* checklists de RFP e paridade de features com consolidadores.
3. **Auditável por padrão.** Toda análise é reproduzível, versionada e explicável — arquitetura que não permite trilha de auditoria não é aprovada, mesmo sendo mais simples. *Sacrificamos:* tempo de engenharia e algumas escolhas de stack convenientes.
4. **Neutralidade é produto.** Não distribuímos produtos financeiros, não recebemos rebates, não tomamos participação em clientes, não monetizamos fluxo. Receita vem exclusivamente de software. *Sacrificamos:* as linhas de receita mais lucrativas do setor — é o preço da confiança que vendemos.
5. **Vencemos a segunda-feira de manhã.** Priorizamos o que entra no ritual semanal do profissional (preparar reunião, revisar carteiras, responder cliente) sobre o que impressiona em demo. *Sacrificamos:* brilho de curto prazo em vendas.
6. **API primeiro, tela depois.** Toda capacidade nasce como serviço consumível por integrações e agentes; a interface é um dos consumidores. *Sacrificamos:* alguma velocidade inicial de UI.
7. **Profundidade local, arquitetura global.** Modelamos ativos brasileiros com profundidade máxima (marcação, tributação, cotização, previdência), mas nenhuma decisão estrutural assume mercado, moeda ou idioma únicos. *Sacrificamos:* simplicidade de modelagem no curto prazo.

## 8. O que NÃO somos

Anti-objetivos permanentes. Violá-los exige revisão formal deste documento — não uma decisão de sprint.

1. **Não somos corretora, distribuidora ou gestora** — e não nos tornaremos uma "para capturar mais margem".
2. **Não recomendamos investimentos autonomamente** — instrumentamos o profissional que recomenda e responde pela recomendação.
3. **Não somos produto B2C** — não construímos app para o investidor final, mesmo quando parecer atalho de crescimento (é o erro estratégico que dispersou nossos concorrentes).
4. **Não vendemos nem monetizamos dados de clientes** — dados do cliente pertencem ao cliente; agregações anônimas só com consentimento explícito e valor devolvido a ele.
5. **Não somos consultoria** — vendemos software escalável, não horas. Implantação assistida é onboarding, não linha de receita.
6. **Não perseguimos os cinco segmentos ao mesmo tempo** — bancos, assessorias de plataforma e demais segmentos esperam até que o beachhead esteja dominado.

## 9. Pressupostos em aberto

Diferente das crenças (apostas de longo prazo), estes são pontos que **sabemos que ainda não sabemos** — com status e critério de resolução. Nenhum documento derivado deve tratá-los como decididos.

| ID | Pressuposto | Status | Como resolver |
|---|---|---|---|
| P1 | O mid-market fiduciário é o beachhead certo | **Confirmado pelo fundador (2026-07-03)** — ele é assessor de investimentos, conhece o segmento e tem acesso a usuários potenciais. Validação de mercado pendente | 15–20 entrevistas de descoberta; critério: dor confirmada + disposição a pagar |
| P2 | Brasil como geografia inicial | **Confirmado (2026-07-03)** — Brasil primeiro, arquitetura global | Resolvido; detalhado em STRATEGY.md |
| P3 | Entrada de dados via Open Finance + parsing de documentos (sem integrações proprietárias) | **Confirmado como estratégia inicial (2026-07-03)** | Prova técnica de cobertura pendente (gate da Fase 1 em STRATEGY.md) |
| P4 | Modelo de precificação | **Direcionado (2026-07-03)** — assinatura SaaS por profissional e por organização; nunca % de AUM | Faixas e unit economics em BUSINESS_MODEL.md |
| P5 | Nome da empresa e marca | **Pendente** | Processo de naming antes do primeiro cliente externo |

## 10. Como saberemos que estamos cumprindo a missão

**Métrica-estrela: reuniões com cliente final preparadas pela plataforma, por semana.**

É a métrica que menos mente: captura simultaneamente confiança (ninguém leva número nosso a um cliente sem confiar), hábito (frequência semanal), valor entregue (o momento de maior valor do wealth management) e potencial de receita (reuniões preparadas ≈ patrimônio sob influência da plataforma). Consolidação passiva, logins e relatórios gerados-mas-não-usados não contam.

| Horizonte | Estado que valida a missão |
|---|---|
| **18 meses** | Organizações fiduciárias pagantes usando a plataforma **toda semana** para preparar reuniões reais; profissionais declarando que não voltariam ao processo anterior. Metas numéricas definidas em STRATEGY.md |
| **5 anos** | Padrão de facto do segmento fiduciário brasileiro; a trilha de auditoria da plataforma citada em processos de supervisão regulatória como referência de conformidade |
| **10 anos** | Camada de inteligência de investimento (para humanos e agentes) em múltiplos mercados de alta complexidade local |

## 11. Governança deste documento

- **Alteração de Missão (§2), Princípios (§7) ou Anti-objetivos (§8):** exige acordo explícito dos dois fundadores, com registro da justificativa em changelog neste arquivo.
- **Revisão obrigatória:** disparada quando (a) qualquer sinal de invalidação da Seção 6 ocorrer, (b) um pressuposto da Seção 9 mudar de status, ou (c) a cada 12 meses, o que vier primeiro.
- **Precedência:** em conflito entre este documento e qualquer documento posterior, este prevalece até que seja formalmente alterado.
- **Changelog:** v1.0 (2026-07-03) — versão inicial, aprovada pelo fundador em 2026-07-03.
