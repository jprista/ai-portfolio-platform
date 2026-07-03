# Protótipo demonstrável — Fase 0

**O que é:** a demo que transforma entrevista em pré-venda (ROADMAP.md, semanas 3–6): carteira → motor determinístico → briefing de reunião + relatório institucional com marca do profissional. **Não é o MVP** — mas o motor, as regras de insight e os testes dourados são sementes reais da Fase 1.

## Rodar

```
py tests/golden_test.py   # suíte dourada (17 verificações, derivação independente)
py demo.py                # gera out/: briefing .md + relatório .html + run imutável .json
```

Abra `out/relatorio_familia_almeida.html` no navegador (Ctrl+P → PDF para ver o formato final).

## O que já obedece à arquitetura definida

- **I1** — todo número nasce no motor (`engine/`); a narrativa é template preenchido com outputs do motor (a camada LLM entra com a Claude API na Fase 1, com Verificador de Proveniência).
- **I2** — execuções imutáveis: `out/run_*.json` com hash dos inputs + versão do motor.
- **Decimal em todo caminho de dinheiro**; retornos por Modified Dietz mensal encadeado (aproximação de TWR com fluxos ponderados por dia — metodologia declarada no relatório).
- **Selo de confiança A–D** por posição, exibido no material (DATA_STRATEGY §5).
- **Detecção determinística** de pontos de atenção (concentração de emissor de crédito/FGC, vencimentos ≤ 90 dias, taxa acima da mediana, confiança de dado) — o LLM nunca detecta, só narra.
- **Dados reais:** CDI diário e IPCA (BCB/SGS, 1º semestre 2026) versionados em `data/`.

## Dados da demo

`data/portfolio_familia_almeida.json` é **fictício** (rotulado no próprio arquivo). Substituir por 2–3 carteiras reais anonimizadas do fundador — os valores viram casos dourados conferidos à mão (ENGINEERING_PRINCIPLES §2).

## Limitações declaradas (por desenho — Princípio 2 da missão)

Valorização de posições vem informada no JSON (o accrual por indexador/curva é Fase 1); sem parsing de PDF ainda (aguarda extratos reais); medianas de taxa de fundos são referências demo (produção: universo CVM); concentração por *gestor* de fundos fora do escopo (candidata a regra v1 — decisão registrada em `engine/insights.py`).
