# PRODUCT_VISION.md — Visão de Produto

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-07-03 |
| **Status** | Final (delegação total; ciclo rascunho → autocrítica → revisão aplicado) |
| **Subordinado a** | [MISSION.md](../00_FOUNDATION/MISSION.md) · [STRATEGY.md](../00_FOUNDATION/STRATEGY.md) |
| **Documentos irmãos** | [PERSONAS.md](PERSONAS.md) · [MVP_SCOPE.md](MVP_SCOPE.md) |

---

## 1. O produto em uma frase

> **O copiloto de reunião do profissional de investimentos independente: transforma as carteiras dos seus clientes em análise institucional pronta, material apresentável e registro auditável — em minutos, não em horas.**

## 2. O objeto central do produto é a Reunião, não a carteira

Decisão de produto mais importante deste documento. Consolidadores organizam-se em torno da *carteira* (um dashboard que existe passivamente). Nós nos organizamos em torno da **Reunião** — o evento recorrente que estrutura a vida do nosso usuário e o momento onde ele é julgado pelo cliente dele.

Toda entidade do produto serve a esse objeto:

```
Organização (tenant)
 └── Profissional (usuário)
      └── Família/Cliente (o cliente final)
           ├── Carteiras (posições multi-custódia)
           ├── Reuniões (o objeto central: passadas, próxima, pauta, material, registro)
           └── Análises (execuções versionadas do motor + narrativas geradas)
```

A métrica-estrela (reuniões preparadas/semana) deixa de ser um KPI observado e vira **a arquitetura de informação do produto**: a home do usuário não é um dashboard de mercado — é *"suas próximas reuniões e o que precisa da sua atenção antes delas"*.

## 3. Os três momentos da Reunião (e onde o produto atua)

| Momento | O que o produto faz | Fase |
|---|---|---|
| **Antes** (preparação) | Análise completa da carteira desde a última reunião; briefing do que mudou e por quê; pontos de atenção (concentrações, desenquadramentos vs. política, vencimentos, custos); material apresentável com a marca do profissional | **MVP — é o produto inteiro na v1** |
| **Durante** (condução) | Modo apresentação do material; respostas fundamentadas a perguntas do cliente (Q&A sobre a carteira) | Parcial no MVP (material + Q&A); modo apresentação v1.1 |
| **Depois** (registro) | Ata/registro da reunião, decisões tomadas, pendências, documentação de suitability | v1.1+ — capturar o registro mínimo desde o MVP (trilha) |

## 4. Os cinco pilares do produto

1. **Ingestão sem fricção.** Open Finance (via agregador), parsing inteligente de extratos/planilhas com confirmação humana, entrada manual. O profissional nunca digita o que uma máquina pode ler. Todo dado carrega origem e nível de confiança visível.
2. **Motor de verdade.** Toda métrica (retorno TWR, risco, concentração, carrego, custos) calculada por motor determinístico, versionado e coberto por testes dourados. O que não calculamos com padrão institucional, declaramos abertamente que não calculamos (Princípio 2).
3. **Narrativa institucional.** A IA traduz os números do motor em análise escrita com tom de casa séria — em português profissional, citando exclusivamente valores do motor, sem recomendar. É a diferença entre "veja seu dashboard" e "aqui está a análise pronta".
4. **Fábrica de material.** Relatório/apresentação para o cliente final com a marca do *profissional* (não a nossa — ele é o herói, somos a equipe invisível), exportável (PDF), com padrão visual institucional.
5. **Trilha de auditoria.** Cada número clicável até a origem (transações + preços + versão do motor); cada texto gerado registrado com contexto e modelo; histórico imutável. É o pilar que o cliente não pede na demo e que renova o contrato no ano 3.

## 5. Princípios de experiência

1. **Valor em 30 minutos.** Da criação da conta à primeira análise real: menos de 30 minutos, no trial, sem falar com ninguém. Em bootstrap, onboarding é produto, não processo.
2. **Todo número se explica.** Clique em qualquer valor → de onde veio, como foi calculado, com que dados, calculado quando. A confiança se constrói número a número.
3. **Confiança declarada.** Dado incompleto, preço defasado ou classe não suportada aparecem sinalizados — nunca escondidos. Preferimos "não sabemos calcular isso ainda" a um número duvidoso (Crença C6: precisão percebida é binária).
4. **O profissional é o herói.** Nossa marca aparece discretamente para ele e nunca para o cliente final dele. O material é dele, o mérito é dele.
5. **Português institucional.** Tom de banco de primeira linha, não de fintech descolada. Nada de emojis, gamificação ou "parabéns pelo seu primeiro relatório! 🎉".
6. **Teclado e densidade.** Usuário profissional, uso diário: densidade de informação alta, atalhos, tabelas competentes — não um app de consumidor esticado.

## 6. O que o produto NÃO é (recusas de produto)

- **Não é dashboard de acompanhamento de mercado** — não competimos com terminal, home broker ou portal de notícias.
- **Não recomenda** — apresenta análise e pontos de atenção; a recomendação é do humano (Princípio 1; CVM 19/21).
- **Não é rede social nem marketplace** — sem feed, sem comunidade, sem oferta de produtos financeiros.
- **Não é ferramenta de backoffice** — não fazemos billing do escritório, folha, CRM completo (integrações futuras, nunca o core).
- **Não é app do investidor final** — o cliente final recebe material, nunca login (anti-objetivo 3 da missão).

## 7. Evolução prevista (horizonte de produto)

- **v1 (MVP):** o "Antes" da reunião completo — ingestão, motor, análise, briefing, material. Ver MVP_SCOPE.md.
- **v1.1:** registro pós-reunião + documentação de suitability; modo apresentação; alertas entre reuniões ("algo mudou na carteira do cliente X que merece uma ligação").
- **v2:** política de investimento por cliente (IPS) como contrato vivo — desenquadramentos monitorados continuamente; simulações de cenário; comparação com modelos da casa.
- **v3:** API pública para agentes e integrações (Crença C5) — a análise como serviço consumível por máquinas, com a mesma auditabilidade.

## 8. Governança

Revisão a cada gate de fase ou mudança em STRATEGY.md. **Changelog:** v1.0 (2026-07-03) — versão inicial sob delegação total.
