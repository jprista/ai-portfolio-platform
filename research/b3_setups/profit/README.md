# Confluência B3 — indicador para o Profit

`ConfluenciaB3.ntsl` — um placar de −100 a +100 que reúne as cinco camadas que
o levantamento em [`06_RESEARCH/TRADERS_B3_INDICADORES.md`](../../../06_RESEARCH/TRADERS_B3_INDICADORES.md)
mostrou serem as mais usadas no WIN e no WDO, na proporção em que aparecem nas
fontes — mais uma sexta camada que nenhum indicador de confluência costuma ter.

## Por que essas cinco, e nessas proporções

A regra que toda fonte séria repete é **2 a 3 indicadores complementares, nunca
empilhados**. Indicador redundante é apontado como erro de iniciante, e Pam
Semezzato (4ª no Top Traders InfoMoney 2025) conta que o caminho dela foi
*reduzir*. Então cada camada aqui mede uma coisa que nenhuma outra mede:

| Peso | Camada | Mede | Origem |
|---:|---|---|---|
| 30 | MME 9 / 21 / 50 alinhadas + inclinação | **direção** | O indicador nº 1 do ranking; setups 9.x e o *triple screen* do Tabajara |
| 25 | Preço × VWAP da sessão | **posição** | Consenso para minicontrato; filtro de viés do dia |
| 20 | ADX com DI+ / DI− | **força** | O indicador que Pam Semezzato destaca |
| 15 | IFR como **freio** | **exaustão** | "não compre esticado" |
| 10 | Volume × sua média | **participação** | Confirmação de rompimento |

O IFR entra **só como freio**: ele desconta nota de quem já está esticado na
direção do próprio placar, e nunca gera entrada sozinho. Usar IFR para entrar
contra tendência forte é justamente o erro que as fontes alertam.

O VWAP é recalculado do zero a cada pregão. Um VWAP que não zera na abertura é
outro indicador, e para day trade não significa nada.

## A sexta camada: o gate de custo

Esta é a parte que veio do **backtest**, não do levantamento.

Medindo a fricção real do WIN — 1 tick de slippage por lado mais emolumentos —
a ida e volta custa cerca de **11 pontos**, contra alvos típicos de 100 pontos.
São 11% do alvo consumidos antes de qualquer acerto. Se o ATR do momento não for
múltiplas vezes esse custo, **não existe movimento no gráfico que pague a
operação**, por melhor que esteja o placar.

Quando isso acontece a linha fica **cinza claro**. É o estado mais útil do
indicador: mercado morto é exatamente quando o operador de varejo mais força
barra e mais entrega dinheiro em spread.

Nos testes, num mercado artificialmente parado o gate derrubou **94 entradas
para 0**.

## Instalando

1. No Profit: **Estratégias → Editor de Estratégias → Novo → Indicador**
2. Cole o conteúdo de `ConfluenciaB3.ntsl`
3. Compile (F7) e aplique num **subgráfico** do WIN ou WDO, em 5 minutos
4. Ajuste `CustoPontosIdaVolta` ao ativo:
   - **WIN** — 1 tick = 5 pontos → use `11`
   - **WDO** — 1 tick = 0,5 ponto → use `2`

### Se algo não compilar

Não consigo compilar NTSL aqui, então os nomes das funções nativas foram
escritos pela convenção usual do Profit, mas **podem variar de versão**. Os
candidatos a divergir são exatamente quatro:

| Usado no código | Se der erro |
|---|---|
| `ATR(PerATR)` | Substitua por uma média de `TrueRange`, ou pelo nome do ATR na sua versão |
| `ADX(PerDI, PerADX)` | Confira a ordem dos argumentos no editor |
| `DIpos(n)` / `DIneg(n)` | Podem se chamar `DIPositivo` / `DINegativo` |
| `SetPlotColor(n, cor)` | Confira o nome no autocompletar |

Tudo mais — `MediaExp`, `Media`, `IFR`, `Plot`, `Date`, `High/Low/Close/Volume` —
é básico e estável. Se precisar desativar uma camada, **zere o peso dela** nos
`input` em vez de mexer no código; as outras continuam funcionando.

## Como ler

| Cor | Significado |
|---|---|
| **Verde** acima do limiar | As cinco camadas concordam na compra |
| **Vermelho** abaixo | As cinco camadas concordam na venda |
| **Cinza claro** | ATR não paga o custo — não há o que operar |
| **Cinza escuro** | Sem confluência — fora |

## O gêmeo em Python

As mesmas regras existem em `b3setups/setups.py` → `Confluencia`, para poderem
ser **testadas** em vez de acreditadas:

```bash
cd ..
python3 run_backtest.py --csv WIN_5min.csv --contract WIN
python3 tests/confluencia_test.py
```

Se você mudar um, mude o outro. O sentido de existirem os dois é que o
indicador que você olha e as regras que o backtest pontua sejam a mesma coisa.

---

## Nota de honestidade

**Este indicador organiza contexto. Ele não tem vantagem demonstrada.**

O backtest deste repositório mediu que, rodando 104 variantes dos setups mais
citados sobre séries construídas para **não ter vantagem nenhuma**, a busca
sozinha fabrica cerca de **R$ 27,58 por sessão** de lucro inexistente, e **59
das 104 variantes ficam positivas depois dos custos**. Um resultado bonito num
backtest é o resultado *esperado* do procedimento, não evidência de nada.

Rodado contra o nulo calibrado, o próprio Confluência devolve **p = 0,364** em
dado sem edge — ou seja, o teste corretamente não acusa vantagem onde não há.
Isso valida o instrumento, não o indicador.

Antes de operar isto com dinheiro, rode-o sobre os **seus** dados de WIN e veja
se passa do placebo. Se não passar, você tem um painel que ajuda a não operar
mercado morto — o que já vale alguma coisa — e nada que justifique tratá-lo como
promessa de lucro.

E o estudo da FGV-EESP encomendado pela CVM continua valendo: entre quem
persistiu 300+ pregões no mini índice, **97% perderam dinheiro**.

---

# ConfluenciaSinais.ntsl — onde comprar e onde vender

O `ConfluenciaB3.ntsl` acima é um painel de contexto. Este segundo arquivo é o
que dá **entrada, stop e alvo na tela**. Aplique-o **sobre o gráfico** (não num
subgráfico).

| Barra | Significado |
|---|---|
| Verde forte | sinal de **compra** nesta barra |
| Vermelha | sinal de **venda** nesta barra |
| Esverdeada / vinho | operação em andamento |
| Cinza | ATR não paga o custo — nada a operar |

| Linha | |
|---|---|
| Branca | preço de entrada |
| Vermelha | stop |
| Verde | alvo — sempre **2,5× o risco realmente assumido** |

Fora de operação as três linhas colapsam no preço, então a tela só "abre"
quando existe trade.

O sinal nasce no **fechamento** da barra marcada; a entrada real é na abertura
da seguinte. É assim que o backtest mede, para não se dar um preço que não
existia quando a decisão foi tomada.

## O stop: estrutural, com teto

O stop vai na **mínima das últimas `SwingBarras`** (compra) ou na máxima (venda),
um tick além. Esse é o menor stop que o gráfico justifica — abaixo dele o motivo
do trade deixou de existir.

Para apertá-lo você mexe em **`RiscoMaxTicks`**, o teto. E aqui está a aritmética
que decide o valor default:

> A ida e volta custa **~11 pontos no WIN, fixo**. Com alvo de 2,5R o acerto
> necessário é `(R + 11) / (3,5 × R)`.

| Risco | Acerto necessário | | Risco | Acerto necessário |
|---:|---:|---|---:|---:|
| 250 pts | 29,8% | | 50 pts | **35,0%** |
| 100 pts | 31,7% | | 40 pts | 36,5% |
| 70 pts | 33,2% | | 20 pts | 44,4% |

A geometria de um alvo 2,5R entrega **28,6%** sozinha. Ou seja: **apertar o stop
não deixa o trade mais barato — deixa a vantagem que você precisa ter maior.**

Por isso `RiscoMaxTicks` vem em **10 (= 50 pontos)**: é o stop mais apertado que
ainda cabe em 35% de acerto. Aperte mais por sua conta, sabendo o que passa a ser
exigido.

## Validando com replay

```bash
python3 run_replay.py --csv SEU_WIN_5min.csv --contract WIN
```

Três relatórios:

1. **Varredura de stop** — roda o mesmo sinal em vários tetos e mostra, para
   cada um, o acerto realizado contra o acerto exigido. A coluna "precisa" é
   aritmética exata e não depende do dado.
2. **Walk-forward** — divide o histórico em blocos cronológicos. Positivo em um
   bloco de cinco não é estratégia, é sorte concentrada.
3. **Nulo calibrado** — o mesmo sinal sobre séries sem vantagem nenhuma.

Ajuste a meta de acerto que você considera alcançável com `--plausible-hit 0.35`.
O motor devolve o teto mais apertado que cabe nela.

**Se o walk-forward não for positivo na maioria dos blocos, ou se o placebo
devolver p ≥ 0,05, o que você tem é um painel bonito — não uma vantagem.**
