# SPIKE 001 — Fontes de dados (premissa P3) · Resultados

| | |
|---|---|
| **Data** | 2026-07-03 |
| **Objetivo** | Testar ao vivo a viabilidade da estratégia de dados (DATA_STRATEGY.md) antes da Fase 1 |
| **Status** | Parcialmente concluído — pendências listadas em §4 |

## 1. Fontes públicas — testadas ao vivo, funcionando

| Fonte | Teste | Resultado |
|---|---|---|
| **BCB/SGS** (CDI diário, série 12; IPCA, série 433) | Chamadas reais à API | ✅ JSON limpo, sem chave, sem custo. Séries de jan–jun/2026 baixadas e versionadas em `prototype/data/` |
| **Tesouro Transparente** (preços/taxas Tesouro Direto) | HEAD no dataset CKAN | ✅ CSV completo (~14 MB), atualizado no próprio dia do teste |
| **CVM dados abertos** (informes diários de fundos) | Não testado ainda | ⏳ Semana 2 — volume grande (zips mensais); validar pipeline de ingestão |

**Conclusão parcial:** a espinha dorsal de dados de referência do MVP (indexadores + títulos públicos + fundos) é pública, gratuita e estável — confirma a tese da DATA_STRATEGY §1.

## 2. Agregadores Open Finance — descoberta material de custo

Pesquisa de mercado (2026-07): **Pluggy ~R$ 2,5 mil/mês, Belvo ~R$ 6 mil/mês de piso** (taxa mínima de plataforma, relatos de mercado) — além do custo por conexão. A premissa H3 do BUSINESS_MODEL considerava apenas R$ 1–3/conexão e **subestimava o piso fixo**.

**Decisões decorrentes:**
1. O protótipo da Fase 0 **não usa agregador** — dados via arquivo/manual + fontes públicas bastam para a demo.
2. Contratação do agregador adiada para o **M2 da Fase 1**, precedida de negociação (plano startup/desconto de early stage; cotar Pluggy, Belvo e Klavi).
3. BUSINESS_MODEL H3 anotado com o piso de plataforma (gatilho §8 de COGS permanece válido).

## 3. Cotações B3 (ações/ETFs/FIIs)

Não testado neste spike. Candidatos: brapi, Cedro, provedores B3 de baixo custo. Ação na semana 2: cotar e validar termos de uso comercial (regra da DATA_STRATEGY §3).

## 4. Pendências do spike (semana 2 da Fase 0)

- [ ] Pipeline de ingestão CVM (informes diários de fundos) com carteira real
- [ ] Cotações B3: escolha de provedor + verificação de licença comercial
- [ ] **Parsing de extratos reais** — bloqueado aguardando extratos do fundador (2–3 PDFs de posição, podem ser anonimizados); é o teste que falta para a premissa P3
- [ ] Sandbox Pluggy: criar conta de desenvolvimento (gratuita) e medir cobertura de investimentos das instituições dos design partners
