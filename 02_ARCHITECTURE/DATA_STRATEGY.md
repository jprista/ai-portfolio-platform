# DATA_STRATEGY.md — Estratégia de Dados

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [ARCHITECTURE.md](ARCHITECTURE.md) · pressuposto P3 do [MISSION.md](../00_FOUNDATION/MISSION.md) |

---

## 1. Tese de dados

Dados são o fosso dos consolidadores — e a nossa estratégia é **não travar essa guerra**: usar infraestrutura pública regulada (Open Finance) e dados públicos de mercado (a riqueza subestimada do Brasil: CVM, Tesouro, BCB), completar com parsing inteligente de documentos, e concentrar nosso investimento onde ninguém está — **qualidade, reconciliação e proveniência**. O diferencial não é ter o dado; é ser a única plataforma onde o profissional sabe *exatamente* o quanto pode confiar em cada dado.

## 2. Dados de carteira (por prioridade)

| Via | Cobertura esperada | Custo | Risco |
|---|---|---|---|
| **1. Open Finance** (via agregador — Pluggy ou equivalente, com camada de abstração `PortfolioSource` própria) | Bancos e corretoras grandes; melhora a cada trimestre | R$ 1–3/conexão/mês (H3 do BUSINESS_MODEL) | Qualidade heterogênea entre instituições; gaps em fundos exclusivos e previdência |
| **2. Parsing de documentos** (extratos PDF/XLSX dos custodiantes, via IA + confirmação humana) | Qualquer instituição que emita extrato — é o fallback universal | Tokens de LLM (H2) | Erro de extração → mitigado pela fila de confirmação obrigatória |
| **3. Entrada manual** | 100% | Tempo do usuário | Erro humano → validações + trilha de edição |

A abstração `PortfolioSource` é obrigatória desde o dia 1: trocar de agregador (ou adicionar um segundo) não pode tocar o domínio. **Gate técnico da Fase 1:** vias 1+2 cobrindo ≥ 70% do patrimônio dos design partners (R2 do STRATEGY.md dispara o plano B: API de consolidador).

## 3. Dados de mercado e referência (fontes v1)

| Dado | Fonte | Custo |
|---|---|---|
| Cotas e cadastro de fundos (incl. FIEs de previdência) | CVM — Informe Diário (dados abertos) | Gratuito |
| Preços de Tesouro Direto | Tesouro Transparente | Gratuito |
| Séries CDI, SELIC, IPCA, PTAX | BCB/SGS | Gratuito |
| Fechamento de ações/FIIs/ETFs/BDRs | Provedor de baixo custo sobre dados B3 (avaliar: brapi, Cedro, outro) — contrato na Fase 1 | Baixo |
| Ibovespa e índices de mercado | Idem | Baixo |
| Curvas de juros (pré, IPCA) para v1.1+ | Anbima (parcialmente pago) — adiado; v1 usa indexadores contratuais | — |

Regra de licenciamento: **nenhuma fonte entra sem verificação de termos de uso para fim comercial** (registrada em ADR). Dados de mercado vivem no esquema `market` (global, sem tenant, versionado por data de captura).

## 4. Modelo canônico (conceitos)

- **Instrument** — identidade única de um ativo (tipo, emissor, indexador, vencimento, identificadores externos: CNPJ do fundo, ticker, código Tesouro). Deduplicado globalmente.
- **Transaction** — evento imutável (compra, venda, aporte, resgate, provento, custódia). Correção = estorno + nova transação, nunca UPDATE (auditabilidade I4).
- **Position** — derivada de transações quando há histórico; *informada* quando só há foto do extrato. Os dois modos coexistem com `provenance` explícita.
- **PricePoint / IndexSeries** — preços e séries com fonte e timestamp de captura.
- **AnalysisRun** — snapshot imutável de inputs + versão do motor + outputs (I2). É a unidade de auditoria e de reprodutibilidade.

Todo valor monetário: `NUMERIC` no banco, aritmética `Decimal` no motor — **float é proibido em caminho de dinheiro** (ENGINEERING_PRINCIPLES.md).

## 5. Qualidade e confiança do dado (o diferencial)

Cada posição carrega um **selo de confiança** calculado, exibido na UI e propagado às análises:

- **A (alta):** derivada de transações Open Finance, preço do dia, reconciliada.
- **B (boa):** posição informada por fonte primária, preço ≤ D-3.
- **C (atenção):** documento parseado sem reconciliação, preço defasado, ou classe com metodologia simplificada.
- **D (manual):** informada pelo usuário sem fonte.

Reconciliação contínua: posição derivada × posição informada; divergência acima do limiar nunca é ajustada em silêncio — vira alerta para o profissional decidir (com registro). Relatórios exibem nota metodológica com o mix de confiança — transparência que P3 (Eduardo) mostrará ao auditor dele.

## 6. Golden dataset

Ativo de engenharia de primeira classe: 10–20 carteiras reais anonimizadas (começando pelas do fundador e dos design partners, com consentimento), com métricas calculadas e conferidas à mão, mantidas como suíte de testes dourados. Nenhuma mudança no motor entra sem passar por elas; toda classe de ativo nova exige seus casos dourados assinados pelo fundador antes de ir a produção (C6: precisão é binária).

## 7. LGPD aplicada a dados (resumo operacional — detalhe em SECURITY_COMPLIANCE.md)

Classificação: dados de clientes finais (CPF, patrimônio, posições) = **sensíveis ao negócio, minimização máxima** — coletamos só o que a análise exige (nome/apelido da família, sem endereço, sem estado civil, sem nada que não usemos). Papéis: o escritório é controlador; nós, operadores. Retenção: dados de tenant apagados em até 30 dias após rescisão (com backout de backups em 90); trilha de auditoria anonimizada preservada. **Dados de clientes jamais treinam modelos nem viram "benchmark de mercado" sem consentimento explícito e agregação irreversível** (anti-objetivo 4 da missão).

**Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
