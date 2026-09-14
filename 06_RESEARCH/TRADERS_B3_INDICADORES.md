# Indicadores usados pelos maiores traders brasileiros no WIN e no WDO

> **Pesquisa exploratória — 14/09/2026.** Levantamento aberto de fontes públicas (imprensa
> especializada, plataformas, material de escolas de trading, papers acadêmicos e resultados
> de competições auditadas) sobre quais ferramentas os traders brasileiros de maior projeção
> usam para operar mini índice (WIN) e mini dólar (WDO) na B3.

---

## 0. Leia isto antes de tudo — o que a pesquisa consegue e não consegue provar

Esta é a parte mais importante do documento, e ela desagrada.

**Não existe base pública auditada que ligue "indicador X" a "trader lucrativo Y" no Brasil.**
O que existe são três coisas diferentes, que costumam ser confundidas:

| O que se pode medir | O que NÃO se pode concluir |
|---|---|
| Quem é mais **conhecido** (prêmios de influência, seguidores, mídia) | Que essas pessoas são as mais lucrativas |
| Quem **venceu competições** com regras e conta real auditada | Que a estratégia se sustenta fora de uma janela de dias |
| O que cada um **diz publicamente** que usa | Que é o que de fato gera o resultado — ou que gera algum |

Quase todo o conteúdo indexado sobre "os maiores traders do Brasil" é **material comercial**:
páginas de curso, publieditorial de corretora e conteúdo patrocinado. Números do tipo
"R$ 1,8 milhão em três dias" aparecem em peças pagas, sem extrato auditado. Tratei tudo isso
como *declaração de método*, não como *evidência de desempenho*.

E o contraponto duro, esse sim com dado primário:

> **Estudo da FGV-EESP (Chague & Giovannetti), encomendado pela CVM**, rastreou **todos** os
> investidores pessoa física que operaram minicontratos de índice e dólar na B3 entre
> **2012 e 2017**. Entre os que persistiram por **300+ pregões**, **97% perderam dinheiro**.
> Dos 3% que ficaram no azul, **2,6 pontos percentuais ganhavam menos de R$ 300/dia**.
> De ~20.000 pessoas que começaram a operar mini índice entre 2013 e 2015, **92,1% desistiram**.
> Conclusão dos autores: os ganhos se ligam muito mais a **sorte** do que a técnica — e a
> performance **não melhora** com o tempo de prática.

E a evidência acadêmica sobre os próprios indicadores é contraditória:

- **A favor:** estudo com o minicontrato futuro do Ibovespa em janelas de 5 minutos
  (jan/2008–fev/2010) construiu estratégia com **médias móveis + momentum** e encontrou
  relação retorno-risco relevante, sugerindo que o ativo **não** exibia eficiência de forma fraca
  naquele período.
- **Contra:** trabalho que testou **14.630 estratégias de análise técnica** concluiu que
  **nenhuma** gera retorno estatisticamente significativo depois de corrigir **data-snooping**
  (o viés de garimpar a regra que funcionou no passado).

**Implicação prática:** o mapa abaixo descreve fielmente **o que essa comunidade usa**.
Ele não é — e não pode ser — um mapa do que **funciona**. São perguntas separadas.

---

## 1. Quem são "os maiores" — três populações distintas

### 1.1 Os mais reconhecidos pelos pares (Prêmio Top Traders InfoMoney 2025)

Voto fechado entre profissionais: lista prévia de 200 traders, mais de 150 profissionais votando.
É o indicador mais defensável de *reputação* no meio — não de lucro.

| # | Nome | Marca operacional |
|---|---|---|
| 1 | **Alexandre Wolwacz (Stormer)** | Setups replicáveis e objetivos; se define como trader **de volatilidade**, não de tendência |
| 2 | **André Moraes** | Análise técnica clássica: tendência, suporte/resistência, médias móveis, leitura macro |
| 3 | **Caio Scotte** | (metodologia pública detalhada não localizada nesta pesquisa) |
| 4 | **Pam Semezzato** | Deliberadamente **poucos indicadores**: médias móveis + **ADX / DI+ / DI−** |
| 5 | **Fabrício Gonçalvez** | Abordagem por **risco, estatística e adaptação** — método achado via análise estatística em 2014 |

Fora do top 5, dois nomes aparecem de forma recorrente na imprensa e no ecossistema de cursos:
**André Machado ("Ogro de Wall Street")**, ex-Microsoft, criador do indicador **Tabajara**; e
**Flávio Lemos**, **CMT** (uma das primeiras certificações CMT do Brasil), engenheiro pela UFRJ,
autor do livro de análise técnica mais adotado no país e operador de futuros desde 1993.

### 1.2 Os que venceram competições com conta auditada

Categoria muito mais dura de falsificar — regras públicas, limites de contratos, resultado verificado.

- **Danillo Ramos Duarte** — campeão da **Copa BTG Trader** (prêmio de R$ 1 milhão), metalúrgico
  da Usiminas em Cubatão, 43 anos. Venceu entre **13 mil participantes**. Melhores resultados
  **no mini índice (WINZ25)**, também operando WDO, bitcoin e ether. Girou **2.247 contratos**
  na competição.
- **Leonardo da Costa** — agricultor capixaba, 34 anos, campeão do **1º Campeonato Brasileiro
  de Trade da Nelogica**: **R$ 21 mil em dois dias** dentro do limite de 10 contratos de WIN e WDO.
- **Thiago Baldelim** — advogado, campeão do torneio RocketTrader/Eai Invest, disputado em
  baterias de **15 minutos** operando WINFUT, WDOFUT e BITFUT, teto de 20 contratos por ativo.
  Fator decisivo relatado: **velocidade de execução**, não sofisticação de indicador.
- **Eduardo Ramos** — quarto pódio na **World Cup Trading Championship**, a principal competição
  global; **+258,1% em um trimestre**. Detalhe revelador: opera **um único trade por pregão**,
  em derivativos do S&P 500 — não em WIN/WDO.

> **O padrão que salta aos olhos:** nenhum campeão atribuiu a vitória a um indicador. Os fatores
> citados foram **velocidade, disciplina de risco e limite de contratos**. Quem sobe ao pódio
> fala de execução; quem vende curso fala de setup.

### 1.3 Quem de fato move o preço (e não aparece em lista nenhuma)

Mesas institucionais, tesourarias e **HFT**. Na B3, o high-frequency trading se concentra
exatamente nos ativos mais líquidos — **minicontratos futuros e dólar**. O acesso exige colocation
no data center da B3, latência ultrabaixa e volume mínimo (na faixa de **7.500 lotes de mini
índice** para enquadramento). Esse grupo **não usa IFR nem MACD**: usa microestrutura, arbitragem
e latência. É a contraparte real do trader de varejo no book do WIN e do WDO.

---

## 2. O mapa consolidado — as cinco camadas

A comunidade brasileira de WIN/WDO opera em camadas empilhadas. Quanto mais experiente o operador,
mais peso nas camadas 1 e 2 e menos nas 3.

### Camada 1 — Referências de preço (o que *todos* olham primeiro)

Não são indicadores. São níveis. E são a base de praticamente todo setup brasileiro de minicontrato.

| Referência | Uso |
|---|---|
| **Máxima, mínima, fechamento e ajuste do pregão anterior** | Nível-âncora do dia; o "ajuste" é específico do mercado futuro brasileiro |
| **Pivot Points** | Calculados a partir de H/L/C do dia anterior — dos níveis mais usados no day trade |
| **Suporte e resistência / topos e fundos** | WIN e WDO respeitam bem níveis técnicos por causa da altíssima liquidez e presença institucional |
| **Números redondos** | No WIN, marcas cheias do Ibovespa (130.000, 135.000) funcionam como barreira psicológica |
| **Fibonacci (38,2% / 50% / 61,8%)** | Força aumenta quando o nível coincide com topo/fundo anterior. **Flávio Lemos** é referência em Fibonacci + Força Relativa |
| **Abertura, gap e leilão** | Define o viés do dia |

### Camada 2 — Fluxo e microestrutura (o que separa o profissional no WDO)

Não derivam de preço histórico: leem o mercado em tempo real.

| Ferramenta | O que entrega |
|---|---|
| **Book de ofertas** | A *intenção* — ordens passivas organizadas por preço |
| **Times & Trades** | A *ação* — o que foi efetivamente agredido. Considerada a ferramenta central do tape reading |
| **Volume at Price / Volume Profile** | Histograma de volume por nível; **VPOC** = preço de maior volume negociado; **VAH/VAL** = bordas da área de valor |
| **VWAP** | Preço médio ponderado por volume do dia. Filtro de viés: acima do VWAP prioriza compra, abaixo prioriza venda. Especialmente eficaz em WIN e WDO pela liquidez |
| **Delta, CVD, Footprint** | Diferença entre agressão compradora e vendedora; **absorção** = volume agressivo alto sem avanço de preço, precede reversão |
| **Market Profile / Auction Market Theory** | Leitura de **balanço vs. desequilíbrio**. Padrão entre prop firms de futuros nos EUA; crescendo no Brasil. Dalton usava TPO; o fluxo moderno prefere perfil por **volume** |

> **Consenso forte entre tape readers brasileiros:** o **WDO/DOL é o ativo preferido** para leitura
> de fluxo — liquidez altíssima, volatilidade em ticks e forte presença institucional fazendo hedge
> tornam o fluxo mais claro e direcional. O **WIN é o mais líquido da B3** e mais didático para
> aprender, porque o fluxo é consistente e os padrões se repetem.

### Camada 3 — Indicadores clássicos, em ordem de frequência de citação

**1. Médias móveis — disparado o mais usado**

| Configuração | Origem / uso |
|---|---|
| **MME 9** | Base dos **setups 9.1, 9.2 e 9.3 de Larry Williams** — provavelmente os setups mais difundidos do Brasil. 9.1 = reversão (entrada no rompimento da máxima do candle de virada da média, stop na mínima); 9.2/9.3 = *trend following*, entrada em correções dentro de tendência |
| **MME 9 + MME 21** | Combinação padrão para timeframes de 1 a 15 minutos |
| **MME 50 + MME 200** | Leitura de tendência em gráficos maiores |
| **MMS 3, 8 e 20** | **Didi Index / Agulhada do Didi** (Odir Aguiar, 40+ anos de mercado): quando as três médias cruzam simultaneamente o corpo de um candle, há "agulhada"; saída na ordem 3 > 8 > 20 = agulhada de compra |
| **MME 5 + MME 49** | Compõem o **setup IFR2 do Stormer** |
| **MME 8 / 20 / 50 / 200 coloridas** | **Setup Tabajara** (André Machado): sistema de *triple screen* — a MME8 no gráfico de 5 min equivale à MME20 de 2 min, e a MME200 equivale à MME20 de 60 min. Colore médias e candles como semáforo: verde+verde = buscar compra, vermelho+vermelho = buscar venda, verde+preto = correção |

**2. VWAP** — tratado como indispensável no day trade de minicontrato. Combinação citada como
das mais fortes: **Volume Profile + VWAP**, com zona de alta convicção quando o VWAP converge
com o VPOC.

**3. IFR / RSI** — sobrecompra acima de 70, sobrevenda abaixo de 30. Variante brasileira de maior
impacto: o **IFR2** (RSI de 2 períodos) do Stormer, para reversão à média após quedas acentuadas.

**4. Bandas de Bollinger** — MMS20 central com 2 desvios-padrão. Volume 4 inteiro do *Manual de
Setups* do Stormer é dedicado a elas; o setup **"Príncipe de NY"** de **Rodrigo Cohen** é baseado
em Bollinger. Uso mais citado: **squeeze** (bandas estreitas antecedem movimento forte) e
reversão na banda **apenas** com confirmação do IFR.

**5. MACD** — direção e força de tendência; cruzamento com a linha de sinal.

**6. Estocástico** — mesmo papel do IFR, porém mais rápido; preferido em mercado lateral.

**7. ADX com DI+ / DI−** — mede *força* de tendência (não direção). Destaque no método de
**Pam Semezzato**, que deliberadamente reduziu o número de indicadores.

**8. ATR** — quase sempre para **dimensionar stop** e como base dos **Canais de Keltner**
(MME20 ± múltiplo do ATR).

**9. Volume** — confirmação de rompimento e alerta de reversão.

**10. Indicadores proprietários** — **Didi Index**, **Tabajara**, e o **Compass Indicator** da
Nelogica, desenvolvido especificamente para operações de tendência em WIN e WDO.

### Camada 4 — O tipo de gráfico como decisão estratégica

Peculiaridade brasileira forte: muita gente troca o eixo do tempo.

- **Renko** — tijolos por variação de preço, **sem eixo de tempo**; filtra ruído. Configuração
  citada para mini índice: **25R ou 35R**. O setup **"Cerca Elétrica"** de Rodrigo Cohen combina
  **Renko + médias móveis + tendência**, mirando ~100 pontos por operação no WIN — e ele alerta
  que **só funciona com mercado em tendência**.
- **Gráficos por volume ou por ticks** — normalizam a atividade em vez do relógio.
- **5 minutos** é o timeframe-base mais recorrente; 1–15 min para execução, 60 min para contexto.

### Camada 5 — Contexto macro (indispensável no WDO)

O WDO é muito menos "gráfico" do que o WIN. O que os operadores monitoram:

- **Diferencial de juros** Selic × Fed — atrai ou repele capital estrangeiro
- **Fluxo de investidor estrangeiro** e atuação do **Banco Central**
- **Payroll, CPI e decisões do Fed** — movem o dólar globalmente
- **S&P 500 / futuros americanos** e aversão a risco global
- **Commodities** — alta tende a enfraquecer o dólar contra o real
- **Janelas de maior movimento:** abertura (**9h–10h**) e o período da tarde, quando o mercado
  americano abre e saem os dados dos EUA

---

## 3. Ranking final — os indicadores mais usados

Consolidando todas as fontes, por frequência de citação e por peso nos métodos nomeados:

| Pos. | Ferramenta | Camada | Quem sustenta |
|---|---|---|---|
| 1 | **Médias móveis exponenciais** (9, 21, 50, 200) | Clássica | Larry Williams 9.1/9.2/9.3, Stormer, Tabajara, André Moraes, Pam Semezzato |
| 2 | **Suporte/resistência + níveis do dia anterior + pivots** | Preço | Universal |
| 3 | **VWAP** | Fluxo | Consenso para minicontratos |
| 4 | **Volume Profile / VPOC** | Fluxo | Tape readers, Market Profile |
| 5 | **Book + Times & Trades** | Fluxo | Padrão profissional no WDO/DOL |
| 6 | **IFR / RSI** (incl. IFR2) | Clássica | Stormer |
| 7 | **Bandas de Bollinger** | Clássica | Stormer (Vol. 4), Cohen ("Príncipe de NY") |
| 8 | **Fibonacci** | Preço | Flávio Lemos, Cohen |
| 9 | **Delta / CVD / Footprint** | Fluxo | Fluxo avançado, adoção crescente |
| 10 | **MACD** | Clássica | Difusão ampla, baixa diferenciação |
| 11 | **ADX / DI+ / DI−** | Clássica | Pam Semezzato |
| 12 | **ATR** (stop e Keltner) | Risco | Gestão de risco em geral |
| 13 | **MMS 3-8-20 (Didi Index)** | Proprietária | Didi Aguiar |
| 14 | **Estocástico** | Clássica | Mercado lateral |
| 15 | **Renko / gráfico por volume** | Estrutura | Cohen ("Cerca Elétrica") |

**A regra de composição que aparece em praticamente toda fonte séria:** escolher **2 a 3**
indicadores que meçam **aspectos complementares** — por exemplo uma **MME** (tendência), um
**IFR ou Estocástico** (momentum) e **volume ou VWAP** (confirmação). Empilhar indicadores
redundantes é apontado como erro de iniciante. **Pam Semezzato** conta exatamente isso: o excesso
de indicadores atrapalhava a decisão no ritmo acelerado do day trade, e o caminho foi **reduzir**.

---

## 4. O que os próprios nomes de topo dizem que importa mais do que indicador

Esta convergência é o achado mais consistente da pesquisa inteira — e ela **não é sobre indicadores**:

- **Flávio Lemos (CMT):** *"o tamanho da posição é mais importante do que o sinal de entrada"*;
  a escolha do indicador precisa respeitar o **ambiente de mercado** — cada contexto pede
  ferramenta diferente.
- **Fabrício Gonçalvez:** método achado por **estatística**; defende que o controle dos **dados
  operacionais próprios** é o que dá referência real de probabilidade de sucesso. E argumenta
  que day trade **não deveria ser a principal fonte de construção de patrimônio**.
- **Pam Semezzato:** gestão de risco como o diferencial central; **menos** indicadores, execução
  mais objetiva.
- **Rodrigo Cohen:** o setup **só vale sob a condição de mercado certa** (Cerca Elétrica exige
  tendência).
- **Campeões de torneio:** citaram **velocidade de execução** e respeito a **limites de contratos**.
- **Stormer:** setups **replicáveis**, com critérios claros de entrada, saída e risco — a ênfase
  está na replicabilidade, não no indicador em si.

Ninguém no topo atribui resultado a um indicador. Todos atribuem a **risco, contexto e execução**.

---

## 5. Lacunas honestas desta pesquisa

Para não passar por completa o que não é:

- **Metodologia não localizada em fonte pública confiável** para: Caio Scotte (3º do ranking),
  Rodrigo Prado ("Nomad Trader"), Jefferson Laatus e Richard Rytenband.
- **Josué Ramos** e **Fabrício Stagliano** aparecem como nomes de alta projeção, mas sem descrição
  técnica verificável de método — apenas caracterizações genéricas ("usa indicadores financeiros
  e observação de vários mercados").
- Vários domínios relevantes (InfoMoney, blog da Nelogica, Trader Brasil, arXiv, repositório da
  UFRJ) **não puderam ser acessados diretamente** pelo proxy de rede desta sessão; o conteúdo
  entrou via resumo de busca, com granularidade menor do que a leitura integral daria.
- **Nenhum número de performance citado em material comercial foi verificado.** Onde apareceram,
  estão marcados como declaração, não como fato.
- A "busca mundial" tem limite real: o assunto WIN/WDO é **quase inteiramente de língua
  portuguesa** e majoritariamente produzido por quem **vende educação financeira**. A camada
  internacional que de fato se aplica é a de **Auction Market Theory / Market Profile / order flow**,
  padrão entre prop firms de futuros nos EUA e em adoção crescente aqui.

---

## 6. Se o objetivo for construir algo sobre isso

Dois caminhos, com honestidade sobre cada um:

**Caminho defensável — instrumentar, não prescrever.** O achado da seção 4 e o estudo da FGV
apontam na mesma direção: o diferencial mensurável não está no sinal de entrada, está em
**risco, dimensionamento de posição e disciplina de execução**. Um produto que devolve ao operador
**as estatísticas reais dele** (expectativa matemática, distribuição de resultado por setup, por
horário, por tamanho de posição, drawdown) faz o que Fabrício Gonçalvez descreve como o que
funcionou para ele. Isso é **auditável** e compatível com a exigência de precisão numérica do
projeto.

**Caminho a evitar.** Vender sinal de indicador como se tivesse *edge* comprovado. A evidência
disponível — 97% de perdedores entre os persistentes no mini índice, e 14.630 estratégias sem
significância estatística após correção de data-snooping — **não sustenta** essa promessa. Além
do risco reputacional, há fronteira regulatória da CVM a respeitar.

---

## Fontes

**Evidência primária e acadêmica**
- [FGV-EESP — "Day trade é cassino, muito mais sorte do que técnica", diz pesquisador](https://eesp.fgv.br/noticia/day-trade-e-cassino-muito-mais-sorte-do-que-tecnica-diz-pesquisador)
- [FGV-EESP — Viver de especulação diária é quase impossível](https://eesp.fgv.br/noticia/viver-de-especulacao-diaria-e-quase-impossivel-mas-tem-cada-vez-mais-brasileiros-fazendo)
- [Chague & Giovannetti — "Day Trade: do outro lado das estatísticas" (arXiv)](https://arxiv.org/pdf/1912.04274)
- [IDEAS/RePEc — working paper FGV EESP 525](https://ideas.repec.org/p/fgv/eesptd/525.html)
- [SciELO/RAC — É possível bater o Ibovespa com operações de análise técnica no mercado futuro?](https://www.scielo.br/j/rac/a/GnJxbhfNGcgMFYvxSPr7wYp/)
- [SciELO/RBE — Análise técnica: sorte ou realidade?](https://www.scielo.br/j/rbe/a/VbBFrdLR4ZRdLryczP5b9HQ/?lang=pt)
- [UFRJ/Poli — Análise técnica para day trade: rentabilidade de indicadores](http://monografias.poli.ufrj.br/monografias/monopoli10024070.pdf)
- [UFU — Análise de Indicadores Técnicos para Negociação](https://repositorio.ufu.br/bitstream/123456789/33854/1/An%C3%A1liseIndicadoresT%C3%A9cnicos.pdf)
- [Suno — Day trade: investidores levam prejuízo 20 vezes maior em cinco anos](https://www.suno.com.br/noticias/day-trade-fgv-pesquisa-prejuizo-pessoa-fisica/)

**Rankings, competições e perfis**
- [InfoMoney — Top Traders: os 20 principais destaques do trading brasileiro em 2025](https://www.infomoney.com.br/mercados/top-traders-infomoney-lista-os-20-principais-destaques-do-trading-brasileiro-em-2025/)
- [InfoMoney — Stormer vence a 1ª edição do prêmio Top Traders](https://www.infomoney.com.br/mercados/stormer-vence-1a-edicao-do-premio-top-traders-infomoney/)
- [InfoMoney — É possível vencer no trading? Top 3 do mercado mostra caminho e armadilhas](https://www.infomoney.com.br/mercados/e-possivel-vencer-no-trading-top-3-do-mercado-mostra-caminho-e-armadilhas/)
- [Money Times — Copa BTG Trader: metalúrgico é campeão; veja ativos mais operados](https://www.moneytimes.com.br/copa-btg-trader-metalurgico-leva-premio-de-1-milhao-veja-ativos-mais-operados-grds/)
- [B3 Bora Investir — Metalúrgico campeão da Copa BTG Trader](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/day-trade/metalurgico-e-campeao-da-copa-btg-trader-conta-como-comecou-no-day-trade-e-o-que-vai-fazer-com-premio-de-r-1-milhao/)
- [NeoFeed — Agricultor capixaba se torna campeão brasileiro de day trade](https://neofeed.com.br/negocios/da-lavoura-a-bolsa-de-valores-agricultor-capixaba-se-torna-campeao-brasileiro-de-day-trade/)
- [NeoFeed — Na Copa do Mundo de Day Trade, um brasileiro sobe ao pódio pela quarta vez](https://neofeed.com.br/negocios/na-copa-do-mundo-de-day-trade-um-brasileiro-sobe-ao-podio-pela-quarta-vez/)
- [InfoMoney — RocketTrader e Eai Invest realizam campeonato de day trade](https://www.infomoney.com.br/mercados/rockettrader-e-eai-invest-realizam-campeonato-de-day-trade-com-disputa-acirrada/)
- [InfoMoney — Timing, fluxo e manejo de risco: a metodologia de Flávio Lemos](https://www.infomoney.com.br/mercados/timing-fluxo-e-manejo-de-risco-a-metodologia-operacional-de-flavio-lemos/)
- [InfoMoney — Como Pam Semezzato usa simplicidade para buscar consistência](https://www.infomoney.com.br/mercados/como-pam-semezzato-usa-simplicidade-para-buscar-consistencia-no-trade/)
- [InfoMoney — O que Pam Semezzato analisa antes de um trade](https://www.infomoney.com.br/mercados/o-que-pam-semezzato-analisa-antes-de-um-trade-mentoria-detalha-seu-metodo/)
- [InfoMoney — Day trade não dá dinheiro? Trader explica (Fabrício Gonçalvez)](https://www.infomoney.com.br/mercados/day-trade-nao-da-dinheiro-trader-explica-por-que-ve-mercado-assim/)
- [Nelogica — Fabrício Gonçalvez: trader de alta performance](https://blog.nelogica.com.br/traders-de-alta-performance-fabricio-goncalvez/)
- [Nelogica — Alexandre Wolwacz (Stormer)](https://blog.nelogica.com.br/alexandre-wolwacz-stormer-o-crocodilo-do-mercado-financeiro/)
- [Nelogica — André Moraes, eleito 2º melhor trader do Brasil](https://blog.nelogica.com.br/andre-moraes/)
- [Eu Quero Investir — "Ogro de Wall Street" e os segredos do day trade](https://euqueroinvestir.com/educacao-financeira/day-touro-andre-machado-ogro-de-wall-street)
- [Trader Brasil — Top traders do Brasil](https://www.traderbrasil.com/blog/top-traders-do-brasil.php)
- [Traders.com.br — Traders brasileiros de sucesso: histórias reais da B3](https://www.traders.com.br/blog/posts/traders-brasileiros-sucesso-historias)

**Setups e indicadores**
- [Nelogica — Setup 9.1 de compra e venda](https://ajuda.nelogica.com.br/hc/pt-br/articles/9739530172059-Setup-9-1-de-compra-e-venda)
- [FL Journal — Setup 9.1 de Larry Williams](https://flj.com.br/renda-variavel/compra-venda-setup-9-1/)
- [FL Journal — Setup 9.2 e 9.3 de Larry Williams](https://flj.com.br/renda-variavel/compra-venda-setup-9-2-9-3/)
- [Nelogica — Didi Index](https://ajuda.nelogica.com.br/hc/pt-br/articles/13161968774299-Didi-Index)
- [Trader Gráfico — Didi Index e a agulhada](https://tradergrafico.com.br/blog/?id=22)
- [Tryd — Tabajara Index](https://ajuda.tryd.com.br/hc/pt-br/articles/27739045042459-Tabajara-Index-Tabajara)
- [ForceSystem — Setup Tabajara do André Machado: como funciona](https://www.forcesystem.com.br/setup-tabajara-do-andre-machado-ogro-como-funciona/)
- [InfoMoney — Setup da Cerca Elétrica (Rodrigo Cohen)](https://www.infomoney.com.br/mercados/setup-da-cerca-eletrica-uma-estrategia-simples-e-eficaz-para-ganhar-no-day-trade/)
- [TheCap — 3 técnicas para day trade de Rodrigo Cohen](https://comoinvestir.thecap.com.br/3-tecnicas-para-ganhar-dinheiro-com-day-trade-rodrigo-cohen)
- [TheCap — Fibonacci para day trade de Rodrigo Cohen](https://comoinvestir.thecap.com.br/fibonacci-para-day-trade-rodrigo-cohen)
- [Nelogica — Os 10 melhores indicadores para day trade](https://blog.nelogica.com.br/melhores-indicadores-day-trade/)
- [B3 Bora Investir — 5 indicadores técnicos para operar no day trade](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/day-trade/conheca-5-indicadores-tecnicos-para-operar-no-day-trade/)
- [Sistema Quant — Melhores indicadores para day trade: o que os dados sustentam](https://sistemaquant.com.br/blog/melhores-indicadores-day-trade/)
- [Traders.com.br — VWAP: como usar no day trade](https://www.traders.com.br/blog/posts/vwap-como-usar-day-trade)
- [Traders.com.br — Volume Profile: como usar no trading](https://traders.com.br/blog/posts/volume-profile-como-usar-trading)
- [Traders.com.br — Pivot points: como calcular e usar no day trade](https://traders.com.br/blog/posts/pivot-points-como-usar-day-trade)
- [Nelogica — Canais de Keltner](https://blog.nelogica.com.br/canais-keltner/)
- [Nelogica — Compass Indicator](https://ajuda.nelogica.com.br/hc/pt-br/articles/50216498739611-Compass-Indicator-como-funciona-esse-indicador-no-Profit)
- [XP Educação — Gráfico Renko: o que é e como usar no day trade](https://blog.xpeducacao.com.br/grafico-renko/)
- [Nelogica — Gráfico Renko](https://ajuda.nelogica.com.br/hc/pt-br/articles/360050333071-Gr%C3%A1fico-Renko)

**Fluxo, microestrutura e contexto de mercado**
- [Nelogica — Tape reading: o que é e como funciona](https://blog.nelogica.com.br/tape-reading/)
- [Nelogica — Como fazer a leitura de fluxo no day trade](https://blog.nelogica.com.br/o-que-e-leitura-de-fluxo-no-mercado-financeiro/)
- [Trader Brasil — O que é tape reading? Leitura de fluxo na B3](https://www.traderbrasil.com/blog/o-que-e-tape-reading.php)
- [Traders.com.br — Order flow: como ler o livro de ofertas](https://www.traders.com.br/blog/posts/order-flow-como-ler-livro-de-ofertas)
- [Trader Brasil — Como operar mini dólar (WDO)](https://www.traderbrasil.com/blog/como-operar-mini-dolar-wdo-guia.php)
- [Trader Brasil — Como operar mini índice (WIN)](https://www.traderbrasil.com/blog/como-operar-mini-indice-win-guia.php)
- [United Daytraders — Delta e CVD: análise avançada de order flow](https://united-daytraders.com/blog/delta-cvd-advanced-order-flow)
- [Topstep — Intro to auction market theory and market profile](https://www.topstep.com/blog/intro-to-auction-market-theory-and-market-profile)
- [BrightFunded — Auction Market Theory: a prop trader's blueprint](https://brightfunded.com/blog/auction-market-theory-a-prop-trader-s-blueprint-for-market-context)
- [InfoMoney — Minidólar: fluxo estrangeiro e PMIs guiam o câmbio](https://www.infomoney.com.br/mercados/minidolar-hoje-futuro-do-dolar-wdov26-03092026/)
- [B3 Bora Investir — Conheça a estratégia HFT](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/day-trade/conheca-a-estrategia-hft-que-permite-que-investidores-operem-em-alta-velocidade/)
- [Suno — HFT: como funcionam os algoritmos de alta frequência](https://www.suno.com.br/artigos/hft-high-frequency-trading/)
