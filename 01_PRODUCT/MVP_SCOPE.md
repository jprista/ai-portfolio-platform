# MVP_SCOPE.md — Escopo do MVP (v1)

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [STRATEGY.md](../00_FOUNDATION/STRATEGY.md) · [PRODUCT_VISION.md](PRODUCT_VISION.md) |
| **Janela de construção** | Fase 1: out/2026 – mar/2027 (6 meses), com design partners usando desde o mês 2 |

---

## 1. A regra deste documento

O MVP entrega **o "Antes" da Reunião, completo e confiável** — nada além. Este documento é um contrato de corte: o que está em "Fora" só entra mediante revisão formal, e a resposta padrão para toda ideia nova durante a Fase 1 é *"lista v1.1"*. Prazo negocia com escopo; **nunca com precisão (C6) nem com auditabilidade (Princípio 3)** — se colidirem, o prazo perde (R6 do STRATEGY.md).

## 2. O caminho dourado (a jornada que define "pronto")

> Marina (P2) cria a conta da organização, convida a sócia e conecta os dados de 3 famílias — via Open Finance onde possível, subindo extratos em PDF onde não. Em menos de 30 minutos vê a primeira carteira consolidada, com cada posição marcada com origem e confiança do dado. Agenda a reunião de revisão da família Souza para quinta-feira. Na quarta, abre o **briefing**: o que mudou desde a última reunião, performance vs. CDI e vs. a meta da família, três pontos de atenção (concentração em um emissor bancário, fundo com taxa acima dos pares, CDB vencendo em 40 dias) — cada número clicável até a origem. Gera o **relatório com a marca dela**, revisa, ajusta um comentário, exporta o PDF. Na reunião, o cliente pergunta "por que rendi menos que o CDI?" — ela abre o Q&A e obtém a decomposição, na hora, com fontes. Depois, marca a reunião como realizada; tudo fica registrado e auditável.

Se essa jornada funciona de ponta a ponta com dados reais, o MVP está pronto. Tudo no §3 existe para servi-la.

## 3. Dentro do MVP — por pilar, com critério de aceite

### 3.1 Ingestão

| Item | Critério de aceite |
|---|---|
| Conexão Open Finance via agregador | Conectar instituição, importar posições e movimentações; re-sincronização diária automática |
| Upload de extrato/posição (PDF, XLSX, CSV) com parsing por IA | Extração estruturada com **fila de confirmação humana**: nada entra na carteira sem o profissional aprovar o que foi lido; taxa de extração correta ≥ 95% nos formatos dos 5 maiores custodiantes |
| Entrada manual e edição | CRUD de posições/transações com validação; toda edição registrada (quem, quando, valor anterior) |
| Origem e confiança do dado | Toda posição exibe fonte (Open Finance / documento / manual), data do dado e sinalização de defasagem |

### 3.2 Motor de cálculo (classes de ativo v1)

**Suportadas com padrão institucional:** caixa e conta; Tesouro Direto (preços públicos); RF bancária — CDB/LCI/LCA/LC pré, % CDI, CDI+ e IPCA+ (curva de acúmulo pelo indexador; marcação na curva, com metodologia publicada); fundos de investimento e FIEs de previdência com dados públicos CVM (cotas diárias); ações, FIIs, ETFs e BDRs (fechamento B3).

**Fora da v1 — sempre com limitação declarada na interface, nunca silêncio:** debêntures e crédito privado negociado (v1.1 — exige fonte de marcação), COE, offshore, cripto, derivativos, ilíquidos (imóveis/participações — apenas posição informativa manual, excluída das métricas de risco, com aviso).

**Métricas v1:** TWR (mês, YTD, 12m, desde o início, entre reuniões) · comparação CDI, IPCA e Ibovespa · contribuição aporte/resgate vs. rendimento · volatilidade 12m anualizada e drawdown máximo · concentração por emissor, classe, indexador e liquidez · escada de liquidez (D0 / até 30 / até 360 / 360+) · vencimentos em 90 dias · taxa média contratada da RF (carrego) · custo ponderado de fundos (taxa adm/perf) vs. mediana da classe.

**Critério de aceite global do motor:** 100% das métricas expostas cobertas por **testes dourados** (carteiras reais verificadas à mão — ENGINEERING_PRINCIPLES.md); divergência tolerada ≤ 0,01% vs. cálculo manual; toda execução do motor é versionada e reproduzível.

### 3.3 Análise e IA

| Item | Critério de aceite |
|---|---|
| Resumo executivo da carteira | Narrativa institucional em pt-BR; **todo número proveniente do motor** (validador de proveniência — AI_ARCHITECTURE.md); zero linguagem de recomendação |
| "O que mudou" entre reuniões | Delta de posições, performance, riscos e custos desde a última reunião registrada |
| Pontos de atenção | Regras determinísticas (concentração > limiares, vencimentos, custo acima de pares, defasagem de dado) narradas pela IA — a detecção nunca é do LLM |
| Briefing de reunião | Uma página: contexto da família, o que mudou, pontos de atenção, pauta sugerida |
| Q&A sobre a carteira | Respostas fundamentadas apenas no contexto do motor; "não sei calcular isso ainda" quando fora do suportado |

### 3.4 Fábrica de material

Relatório para o cliente final (PDF): capa e identidade do escritório (logo/cores), seções configuráveis, texto editável antes de exportar, padrão visual institucional. Critério: um profissional o entrega a um cliente real sem retrabalho estético.

### 3.5 Estrutura e confiança

Organização multi-tenant com papéis (admin/profissional) · famílias/clientes e reuniões (agendar, preparar, marcar como realizada) · trilha de auditoria completa (dados, edições, execuções de motor, gerações de IA, exportações) · isolamento por tenant testado (SECURITY_COMPLIANCE.md) · LGPD mínimo viável (consentimento, exportação/exclusão por titular, criptografia) · backup diário com teste de restauração.

**Não-funcionais:** primeira análise em < 30 min do cadastro; análise de carteira (200 posições) em < 60 s; relatório em < 90 s; disponibilidade alvo 99,5% (sem SLA formal na v1).

## 4. Fora do MVP (lista v1.1+ — a resposta é "ainda não")

Rebalanceamento e otimização · simulações e cenários · política de investimento (IPS) monitorada · alertas proativos entre reuniões · registro pós-reunião completo e suitability formal (v1.1 prioritário) · modo apresentação · API pública · integrações CRM · white-label · multi-idioma/multi-moeda · app mobile · billing automatizado (cobrança manual/Pix na Fase 1) · classes excluídas em 3.2.

## 5. Critérios de sucesso do MVP

São os do Gate 1→2 (STRATEGY.md): ≥ 3 design partners preparando reuniões reais **toda semana** · pagando preço de tabela ao fim do período · cobertura ≥ 70% do patrimônio deles pelas classes v1 · zero incidentes de número errado apresentado a cliente final · "não voltaria ao processo antigo" espontâneo.

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
