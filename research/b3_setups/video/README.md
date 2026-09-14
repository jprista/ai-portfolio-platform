# Vídeo explicativo — Confluência B3

`confluencia_b3.mp4` — 1920×1080, 30 fps, ~2min37.

Sete cenas: a regra de composição, as cinco camadas, a formação do placar numa
barra real, o gate de custo, o indicador percorrendo um pregão inteiro, e a nota
de honestidade.

## O princípio de construção

**Nenhum número do vídeo foi digitado à mão.** O placar, os componentes, o ATR,
as médias, o VWAP e o ADX saem de `b3setups`, chamando exatamente o mesmo código
que o backtest usa e que o indicador NTSL espelha. Se o indicador mudar, o vídeo
muda junto na próxima renderização — não há uma segunda versão dos fatos
esperando para divergir.

A série de preço é **sintética e está rotulada como tal em todos os frames**.
Ela é moldada em três fases para que cada estado do indicador possa ser mostrado
de propósito, em vez de torcer para aparecer num sorteio:

| Fase | Barras | O que demonstra |
|---|---|---|
| Mercado morto | 30 | ATR baixo → **gate de custo corta** |
| Tendência | 40 | Camadas alinhadas → **placar verde** |
| Reversão | 38 | Inversão → **placar vermelho** |

Antes delas há uma **sessão de aquecimento de 70 barras**, calculada mas nunca
exibida: uma MME50 com ADX de Wilder precisa de ~50 barras para dizer qualquer
coisa. Sem isso, metade do pregão exibido apareceria sem placar. É o mesmo motivo
pelo qual um operador abre o gráfico com histórico atrás, e não no leilão de
abertura.

## Renderizando

```bash
python3 video/render_video.py                 # vídeo completo
python3 video/render_video.py --probe 8       # 1 PNG por cena, para conferir layout
python3 video/render_video.py --out outro.mp4
```

Sem dependência de sistema: `Pillow` desenha os frames e o binário estático do
`imageio-ffmpeg` codifica. Os frames vão por pipe em RGB cru direto para o
ffmpeg — nada é gravado em disco além do arquivo final.

```bash
pip install pillow imageio-ffmpeg
```

## Uma divergência encontrada ao montar o vídeo

Fazer o vídeo expôs um bug latente. O `session_vwap` do Python ancorava no início
da lista recebida, o que estava certo porque o motor sempre chamava o indicador
uma sessão por vez. O NTSL, porém, reseta na virada de data (`Date <> Date[1]`).
Com a sessão de aquecimento — duas sessões numa lista só — as duas
implementações passariam a discordar.

Corrigido: o `session_vwap` agora reseta por data, idêntico ao NTSL, com teste
dourado cobrindo a virada. Era o tipo de divergência que só aparece quando o
mesmo código é obrigado a rodar num contexto novo.
