# b3_setups — testando os setups de WIN/WDO contra a própria sorte

Motor de backtest para os setups que os traders brasileiros mais citam
(9.1/9.2/9.3, IFR2, Bandas de Bollinger, agulhada do Didi, filtro de VWAP),
construído para responder à pergunta que o levantamento em
[`06_RESEARCH/TRADERS_B3_INDICADORES.md`](../../06_RESEARCH/TRADERS_B3_INDICADORES.md)
deixou em aberto: **isso funciona, ou só parece funcionar?**

Sem dependências. Python 3.11+, stdlib apenas — mesma disciplina do
`services/engine/engine_core`.

---

## O que este projeto faz de diferente

Um backtest comum pergunta "o melhor setup deu lucro?". Essa pergunta é
respondida com "sim" quase sempre, por dois motivos que **nada têm a ver com o
mercado**:

**1. A busca.** Testar 104 variantes e reportar a melhor infla o resultado do
vencedor mesmo que nenhuma tenha vantagem alguma.

**2. O simulador.** Em resolução OHLC não se sabe a ordem dos eventos dentro da
barra. Não existe convenção neutra: avaliar o stop contra a barra inteira joga
os trades de risco pequeno para o balde de perda e deixa os vencedores com risco
médio maior — o que **fabrica expectativa positiva numa série que é
comprovadamente um martingale**. Medimos esse resíduo: ~**+1,3 tick por trade**
num breakout puro (e piora para ~+4,7 se a barra de entrada for ignorada, por
isso a convenção atual é a menos enviesada das disponíveis).

Os dois são propriedades **do procedimento**, não do mercado. Então o
procedimento inteiro — mesma família, mesmo motor, mesmos custos, mesma
volatilidade — é rodado sobre séries que **não têm edge por construção**, e a
distribuição do melhor resultado nessas séries vira o nulo.

Um resultado real só interessa se passar desse nulo.

Rodando o pipeline completo sobre uma série sem edge, ele se auto-diagnostica:

```
best-variant mean P&L per session on the no-edge series:
  median                      27.58
  90th percentile             41.55
observed best on this data    29.45
placebo p-value               0.5000
  INDISTINGUISHABLE from what this same search produces on
  data with no edge at all. No evidence of an edge here.
```

Ou seja: **a busca sozinha fabrica ~R$ 27,58/sessão de lucro inexistente**, e
59 de 104 variantes ficam positivas depois dos custos numa série que é ruído
puro. Qualquer backtest que não calibre isso está reportando esse número como
se fosse edge.

---

## Rodando

### Com dado real (o que interessa)

```bash
python3 run_backtest.py --csv WIN_5min.csv --contract WIN
```

O carregador aceita os formatos que você já tem em mãos — ele fareja o
delimitador, o separador decimal e o formato de data:

| Origem | Cabeçalho típico |
|---|---|
| **Profit / Nelogica** | `Data;Hora;Abertura;Máxima;Mínima;Fechamento;Volume` |
| **MetaTrader 5** | `<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>` |
| **Genérico** | `timestamp,open,high,low,close,volume` |

Coluna faltando gera erro nomeando o cabeçalho — nunca leitura silenciosa da
coluna errada. Barras inconsistentes (OHLC impossível, timestamp fora de ordem)
abortam a execução antes de qualquer estratégia ver o dado.

**Granularidade:** 5 minutos é o timeframe-base que a comunidade usa e o mínimo
razoável aqui. Quanto mais fino o dado, menor o artefato intrabarra.

### Sem dado real (série de controle)

```bash
python3 run_backtest.py --synthetic --sessions 250
```

Não diz **nada** sobre se os setups funcionam no WIN real. Serve para medir o
quanto o procedimento inventa sozinho.

### Parâmetros que mudam a conclusão

```bash
--slippage-ticks 1     # execução. 1 tick/lado é o piso realista em WIN
--exchange-cents 27    # emolumentos day trade, por lado, por contrato
--brokerage-cents 0    # corretagem (zero em várias corretoras nos minis)
--placebo 30           # séries de controle para o nulo (0 desliga)
--boot 2000            # reamostragens do bootstrap
```

`--slippage-ticks` é o parâmetro mais importante. Em WIN 1 tick = 5 pontos =
R$ 1,00/contrato; ida e volta com 1 tick/lado custa **R$ 2,54** contra alvos
tipicamente de 100 pontos (R$ 20). Rode com 0, 1 e 2 e veja quantas variantes
sobrevivem.

---

## Como está montado

```
b3setups/
  contracts.py   Specs de WIN/WDO e modelo de custo. Preço vira índice inteiro
                 de tick; P&L em centavos inteiros — float é proibido no
                 caminho de dinheiro (ENGINEERING_PRINCIPLES §4.1).
  bars.py        Barra, sessão, validação de qualidade do dado.
  indicators.py  MMS, MME, IFR (Wilder), Bollinger, ATR, VWAP de sessão,
                 ADX/DI. Warmup devolve None, nunca zero.
  setups.py      Os setups publicados. Contrato anti-lookahead no topo do
                 arquivo: sinal da barra i só é executável a partir de i+1.
  engine.py      Loop barra a barra. Stop antes de alvo quando ambos cabem na
                 barra; gap preenche na abertura; posição fechada na sessão;
                 não reabre na mesma barra em que fechou.
  stats.py       Reality Check de White, Sharpe Deflacionado, bootstrap de
                 bloco estacionário.
  placebo.py     O nulo calibrado descrito acima.
  report.py      Renderização em texto.
tests/           Testes dourados (valores derivados à mão) + calibração.
```

### Testes

```bash
for t in tests/*_test.py; do python3 "$t" || exit 1; done
```

- `indicators_test.py` — valores conferidos à mão, com a aritmética no comentário.
- `engine_test.py` — 10 cenários de execução, incluindo **o guard de lookahead**
  (barra cujo próprio range cruza o gatilho não pode preencher) e a regra
  conservadora stop-antes-de-alvo.
- `stats_test.py` — o Reality Check rejeita 1/20 sob ruído puro (nominal 5%) e
  detecta um edge injetado com p=0,003.
- `placebo_test.py` — o gerador é martingale (t = +0,09), o artefato OHLC está
  travado numa faixa documentada, e o placebo **não** acusa edge numa série sem
  edge.

O teste do artefato é proposital: se alguém mexer no motor e o viés sair da
faixa, o teste quebra e avisa que o nulo precisa ser recalibrado antes de
qualquer resultado ser levado a sério.

---

## Limites honestos

- **Nenhum resultado sobre WIN real foi produzido aqui.** O ambiente desta
  sessão tem egresso de rede restrito por política (403 no proxy para provedores
  de cotação), então não houve dado de mercado. O motor está pronto e testado;
  falta a série.
- **Cada setup é uma variante documentada**, não a leitura única da regra do
  autor. Isso é deliberado: o tamanho da família é insumo da correção.
- **OHLC não resolve ordem intrabarra.** O artefato é medido e calibrado, não
  eliminado. Dado tick-a-tick reduziria bastante.
- **Custo é premissa declarada,** não cotação. Emolumentos mudam por circular.
- **A série sintética é um random walk sem drift** — sem gaps entre barras, sem
  clusters de volatilidade, sem notícia das 10h. É um nulo conservador para
  medir o procedimento, não um simulador de B3.
