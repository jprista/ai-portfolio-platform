#!/usr/bin/env python3
"""Renders the explainer video for the Confluencia B3 indicator.

Every number on screen is produced by b3setups — the score, the ATR, the
averages, the VWAP, the ADX. The price series is synthetic and is labelled as
such on screen throughout; it is shaped into three phases so each state of the
indicator can be shown deliberately instead of hoped for.

Frames are drawn with Pillow and piped as raw RGB into ffmpeg, so nothing is
written to disk except the final file.

    python3 video/render_video.py            # full render
    python3 video/render_video.py --probe 5  # one frame per scene, as PNGs
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scene_data import scene_series  # noqa: E402

W, H = 1920, 1080
FPS = 30
SEED = 41

BG = (14, 18, 22)
PANEL = (21, 26, 32)
PANEL2 = (28, 35, 43)
RULE = (40, 49, 59)
INK = (232, 236, 241)
INK2 = (169, 180, 193)
INK3 = (119, 130, 143)
ACCENT = (79, 209, 197)
GREEN = (53, 201, 127)
RED = (240, 99, 122)
GATE = (138, 149, 162)
AMBER = (232, 178, 92)

FONTS = "/usr/share/fonts/truetype/liberation/"


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    name = {
        "bold": "LiberationSans-Bold.ttf",
        "reg": "LiberationSans-Regular.ttf",
        "mono": "LiberationMono-Regular.ttf",
        "monob": "LiberationMono-Bold.ttf",
    }[kind]
    return ImageFont.truetype(FONTS + name, size)


F = {
    "h1": font("bold", 78),
    "h2": font("bold", 54),
    "h3": font("bold", 38),
    "body": font("reg", 30),
    "small": font("reg", 24),
    "tiny": font("reg", 20),
    "num": font("monob", 46),
    "numS": font("mono", 24),
    "numM": font("monob", 30),
    "label": font("bold", 22),
}


# ---------------------------------------------------------------- utilities


def mix(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease(t: float) -> float:
    """Ease-out cubic."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_io(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def fade(t: float, start: float, dur: float = 0.5) -> float:
    """Alpha 0..1 for something appearing at ``start`` seconds over ``dur``."""
    return ease((t - start) / dur) if t >= start else 0.0


class Frame:
    def __init__(self) -> None:
        self.img = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.img)

    def text(self, xy, s, f, color, anchor="la", alpha=1.0):
        if alpha <= 0.01:
            return
        self.d.text(xy, s, font=f, fill=mix(BG, color, alpha), anchor=anchor)

    def rect(self, box, color, alpha=1.0, radius=0, outline=None, width=1):
        if alpha <= 0.01:
            return
        c = mix(BG, color, alpha)
        o = mix(BG, outline, alpha) if outline else None
        if radius:
            self.d.rounded_rectangle(box, radius=radius, fill=c, outline=o, width=width)
        else:
            self.d.rectangle(box, fill=c, outline=o, width=width)

    def line(self, pts, color, width=2, alpha=1.0):
        if alpha <= 0.01 or len(pts) < 2:
            return
        self.d.line(pts, fill=mix(BG, color, alpha), width=width, joint="curve")

    def dashed(self, x0, y, x1, color, width=2, alpha=1.0, dash=14, gap=10):
        if alpha <= 0.01:
            return
        c = mix(BG, color, alpha)
        x = x0
        while x < x1:
            self.d.line([(x, y), (min(x + dash, x1), y)], fill=c, width=width)
            x += dash + gap

    def footer(self, t: float, extra: str = "") -> None:
        note = "Série de exemplo — não é dado real de WIN"
        if extra:
            note += "   ·   " + extra
        self.text((64, H - 44), note, F["tiny"], INK3, alpha=0.9)
        self.text((W - 64, H - 44), "Confluência B3", F["tiny"], INK3, anchor="ra", alpha=0.9)


# ---------------------------------------------------------------- chart


class Chart:
    """Price panel with candles, averages and VWAP."""

    def __init__(self, data, box):
        self.data = data
        self.x0, self.y0, self.x1, self.y1 = box
        bars = data["bars"]
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        pad = (max(highs) - min(lows)) * 0.08
        self.pmax = max(highs) + pad
        self.pmin = min(lows) - pad
        self.n = len(bars)
        self.step = (self.x1 - self.x0) / self.n

    def px(self, i: float) -> float:
        return self.x0 + (i + 0.5) * self.step

    def py(self, price: float) -> float:
        frac = (price - self.pmin) / (self.pmax - self.pmin)
        return self.y1 - frac * (self.y1 - self.y0)

    def grid(self, fr: Frame, alpha=1.0):
        fr.rect((self.x0 - 24, self.y0 - 18, self.x1 + 24, self.y1 + 18), PANEL, alpha, radius=10)
        for k in range(5):
            y = self.y0 + k * (self.y1 - self.y0) / 4
            fr.line([(self.x0, y), (self.x1, y)], RULE, 1, alpha * 0.8)

    def candles(self, fr: Frame, upto: int, alpha=1.0, dim_from: int | None = None):
        bw = max(2, int(self.step * 0.62))
        for i in range(min(upto, self.n)):
            b = self.data["bars"][i]
            up = b.close >= b.open
            col = GREEN if up else RED
            a = alpha
            if dim_from is not None and i < dim_from:
                a = alpha * 0.28
            cx = self.px(i)
            fr.line([(cx, self.py(b.high)), (cx, self.py(b.low))], col, 1, a * 0.85)
            top, bot = self.py(max(b.open, b.close)), self.py(min(b.open, b.close))
            if bot - top < 2:
                bot = top + 2
            fr.rect((cx - bw / 2, top, cx + bw / 2, bot), col, a)

    def series(self, fr: Frame, key: str, color, upto: int, width=3, alpha=1.0):
        pts = []
        for i in range(min(upto, self.n)):
            v = self.data[key][i]
            if v is not None:
                pts.append((self.px(i), self.py(v)))
        fr.line(pts, color, width, alpha)


class Oscillator:
    """The score panel below the chart."""

    def __init__(self, data, box):
        self.data = data
        self.x0, self.y0, self.x1, self.y1 = box
        self.n = len(data["bars"])
        self.step = (self.x1 - self.x0) / self.n
        self.lim = 100.0

    def px(self, i):
        return self.x0 + (i + 0.5) * self.step

    def py(self, v):
        return self.y1 - ((v + self.lim) / (2 * self.lim)) * (self.y1 - self.y0)

    def frame(self, fr: Frame, alpha=1.0):
        fr.rect((self.x0 - 24, self.y0 - 18, self.x1 + 24, self.y1 + 18), PANEL, alpha, radius=10)
        thr = self.data["threshold"]
        fr.dashed(self.x0, self.py(thr), self.x1, GREEN, 1, alpha * 0.5)
        fr.dashed(self.x0, self.py(-thr), self.x1, RED, 1, alpha * 0.5)
        fr.line([(self.x0, self.py(0)), (self.x1, self.py(0))], RULE, 1, alpha)
        fr.text((self.x1 + 12, self.py(thr)), f"+{thr:.0f}", F["numS"], GREEN, "lm", alpha * 0.8)
        fr.text((self.x1 + 12, self.py(-thr)), f"-{thr:.0f}", F["numS"], RED, "lm", alpha * 0.8)

    def bars(self, fr: Frame, upto: int, alpha=1.0):
        bw = max(2, int(self.step * 0.62))
        thr = self.data["threshold"]
        zero = self.py(0)
        for i in range(min(upto, self.n)):
            s = self.data["score"][i]
            atr = self.data["atr"][i]
            if s is None:
                continue
            gate_off = atr is None or atr < self.data["atr_min"]
            if gate_off:
                col = GATE
            elif s >= thr:
                col = GREEN
            elif s <= -thr:
                col = RED
            else:
                col = INK3
            y = self.py(s)
            top, bot = (y, zero) if s >= 0 else (zero, y)
            if bot - top < 2:
                bot = top + 2
            fr.rect((self.px(i) - bw / 2, top, self.px(i) + bw / 2, bot), col, alpha)


# ---------------------------------------------------------------- layer spec

LAYERS = [
    ("MME 9 / 21 / 50", "direção", 30, "ema9", ACCENT,
     "Três médias alinhadas e inclinadas", "O indicador nº 1 do ranking."),
    ("VWAP da sessão", "posição", 25, "vwap", AMBER,
     "Preço acima ou abaixo do médio do dia", "Zera na abertura de cada pregão."),
    ("ADX com DI+ / DI−", "força", 20, None, (147, 168, 255),
     "Quanta convicção há no movimento", "O indicador que Pam Semezzato destaca."),
    ("IFR como freio", "exaustão", 15, None, RED,
     "Desconta de quem já está esticado", "Nunca gera entrada sozinho."),
    ("Volume × média", "participação", 10, None, INK2,
     "Se o mercado está participando", "Confirmação de rompimento."),
]


# ---------------------------------------------------------------- scenes

def title_block(fr: Frame, t: float, kicker: str, title: str, sub: str = ""):
    a1 = fade(t, 0.0, 0.5)
    fr.text((140, 96), kicker.upper(), F["label"], ACCENT, alpha=a1)
    fr.line([(140, 130), (140 + 420 * ease(min(1, t / 0.7)), 130)], RULE, 2, a1)
    fr.text((140, 152), title, F["h2"], INK, alpha=fade(t, 0.15, 0.5))
    if sub:
        fr.text((140, 216), sub, F["body"], INK2, alpha=fade(t, 0.35, 0.5))


def scene_intro(fr: Frame, t: float, D: dict):
    a = fade(t, 0.3, 0.9)
    fr.text((W / 2, 400), "Confluência B3", F["h1"], INK, anchor="ma", alpha=a)
    fr.line(
        [(W / 2 - 260 * ease(max(0, (t - 1.0)) / 0.8), 506),
         (W / 2 + 260 * ease(max(0, (t - 1.0)) / 0.8), 506)],
        ACCENT, 3, fade(t, 1.0, 0.4),
    )
    fr.text((W / 2, 546), "Como funciona o indicador", F["h3"], INK2, anchor="ma", alpha=fade(t, 1.4, 0.7))
    chips = ["5 camadas complementares", "1 gate de custo", "WIN · WDO · 5 min"]
    for i, c in enumerate(chips):
        ca = fade(t, 2.3 + i * 0.25, 0.5)
        x = W / 2 + (i - 1) * 420
        fr.rect((x - 190, 650, x + 190, 706), PANEL2, ca, radius=28)
        fr.text((x, 678), c, F["small"], INK2, anchor="mm", alpha=ca)


def scene_regra(fr: Frame, t: float, D: dict):
    title_block(fr, t, "o princípio", "A regra que toda fonte séria repete",
                "2 a 3 indicadores complementares. Nunca empilhados.")
    redundant = ["MACD", "IFR", "Estocástico", "CCI", "Williams %R"]
    distinct = [(l[0], l[1]) for l in LAYERS]

    fr.text((300, 330), "O QUE QUASE TODO MUNDO FAZ", F["label"], RED, anchor="ma", alpha=fade(t, 1.0))
    for i, name in enumerate(redundant):
        a = fade(t, 1.3 + i * 0.16, 0.4)
        y = 400 + i * 86
        fr.rect((110, y, 490, y + 66), PANEL, a, radius=8)
        fr.text((134, y + 33), name, F["body"], INK2, anchor="lm", alpha=a)
        fr.text((466, y + 33), "momentum", F["small"], RED, anchor="rm", alpha=a * 0.95)
    fr.text((300, 862), "cinco leituras da mesma coisa", F["small"], INK3, anchor="ma", alpha=fade(t, 3.0))

    ax = fade(t, 3.6, 0.6)
    fr.text((W / 2, 600), "→", F["h1"], ACCENT, anchor="mm", alpha=ax)

    fr.text((1330, 330), "O QUE ESTE INDICADOR FAZ", F["label"], GREEN, anchor="ma", alpha=fade(t, 4.0))
    for i, (name, mede) in enumerate(distinct):
        a = fade(t, 4.3 + i * 0.22, 0.4)
        y = 400 + i * 86
        fr.rect((1100, y, 1560, y + 66), PANEL, a, radius=8)
        fr.text((1124, y + 33), name, F["body"], INK, anchor="lm", alpha=a)
        fr.text((1536, y + 33), mede, F["small"], GREEN, anchor="rm", alpha=a * 0.95)
    fr.text((1330, 862), "cinco medidas diferentes", F["small"], INK3, anchor="ma", alpha=fade(t, 5.6))
    fr.footer(t)


def scene_camadas(fr: Frame, t: float, D: dict):
    title_block(fr, t, "as cinco camadas", "Cada uma mede algo que nenhuma outra mede")
    ch = Chart(D, (140, 320, 1090, 880))
    ch.grid(fr, fade(t, 0.2))
    ch.candles(fr, ch.n, fade(t, 0.4))

    per = 7.2
    total = 0
    for idx, (name, mede, peso, key, col, line1, line2) in enumerate(LAYERS):
        start = 1.2 + idx * per
        a = fade(t, start, 0.6)
        if a <= 0.01:
            continue
        if key:
            reveal = ease(min(1.0, max(0.0, (t - start) / 1.4)))
            ch.series(fr, key, col, int(ch.n * reveal), 3, a)
            if key == "ema9":
                ch.series(fr, "ema21", mix(col, INK3, 0.45), int(ch.n * reveal), 2, a * 0.85)
                ch.series(fr, "ema50", mix(col, INK3, 0.7), int(ch.n * reveal), 2, a * 0.7)
        y = 330 + idx * 108
        fr.rect((1150, y, 1790, y + 92), PANEL, a, radius=10)
        fr.rect((1150, y, 1156, y + 92), col, a)
        fr.text((1184, y + 22), name, F["h3"], INK, alpha=a)
        fr.text((1184, y + 62), line1, F["small"], INK2, alpha=a)
        fr.text((1766, y + 24), str(peso), F["num"], col, anchor="ra", alpha=a)
        fr.text((1766, y + 68), mede, F["small"], col, anchor="ra", alpha=a * 0.9)
        total = peso if a > 0.5 else total

    ta = fade(t, 1.2 + 5 * per - 1.2, 0.8)
    fr.text((1470, 900), "peso total  100", F["numM"], ACCENT, anchor="ma", alpha=ta)
    fr.footer(t)


def scene_placar(fr: Frame, t: float, D: dict):
    title_block(fr, t, "somando", "Como o placar de uma barra é formado",
                f"Barra {D['focus_i']} — {D['focus_phase']}")
    parts = D["parts"][D["focus_i"]]
    score = D["score"][D["focus_i"]]
    order = [("tendencia", "Tendência", ACCENT), ("vwap", "VWAP", AMBER),
             ("forca", "Força (ADX/DI)", (147, 168, 255)), ("ifr", "Freio do IFR", RED),
             ("volume", "Volume", INK2)]
    cx = 1050
    scale = 6.2
    running = 0.0
    for i, (key, label, col) in enumerate(order):
        a = fade(t, 1.0 + i * 1.5, 0.5)
        v = parts[key]
        y = 340 + i * 96
        fr.text((170, y + 26), label, F["h3"], INK if a > 0.3 else INK3, alpha=a)
        grow = ease(min(1.0, max(0.0, (t - (1.0 + i * 1.5)) / 0.8)))
        x_from = cx + running * scale
        x_to = cx + (running + v) * scale
        bar_to = x_from + (x_to - x_from) * grow
        lo, hi = min(x_from, bar_to), max(x_from, bar_to)
        fr.rect((lo, y, max(hi, lo + 2), y + 52), col, a, radius=4)
        sign = "+" if v >= 0 else ""
        fr.text((hi + 18 if v >= 0 else lo - 18, y + 26), f"{sign}{v:.1f}",
                F["numM"], col, anchor="lm" if v >= 0 else "rm", alpha=a)
        running += v
    fr.line([(cx, 320), (cx, 830)], RULE, 2, fade(t, 0.6))
    fr.text((cx, 292), "0", F["numS"], INK3, anchor="ma", alpha=fade(t, 0.6))

    fa = fade(t, 8.2, 0.8)
    fr.rect((620, 878, 1300, 962), PANEL2, fa, radius=12)
    fr.text((660, 920), "PLACAR DA BARRA", F["label"], INK3, anchor="lm", alpha=fa)
    col = GREEN if score >= D["threshold"] else (RED if score <= -D["threshold"] else INK2)
    fr.text((1260, 920), f"{score:+.1f}", F["num"], col, anchor="rm", alpha=fa)
    fr.footer(t, "componentes calculados pelo próprio indicador")


def scene_gate(fr: Frame, t: float, D: dict):
    title_block(fr, t, "a sexta camada", "O gate de custo",
                "A parte que veio do backtest, não do levantamento.")
    rows = [
        ("Slippage — 1 tick por lado", "10 pontos", RED, 1.0),
        ("Emolumentos day trade", "~1 ponto", RED, 1.6),
        ("Custo da ida e volta", "11 pontos", AMBER, 2.4),
        ("Alvo típico de um setup", "100 pontos", INK2, 3.2),
    ]
    for i, (label, val, col, st) in enumerate(rows):
        a = fade(t, st, 0.5)
        y = 330 + i * 78
        if i == 2:
            fr.line([(150, y - 12), (900, y - 12)], RULE, 2, a)
        fr.text((160, y + 24), label, F["body"], INK2 if i < 2 else INK, alpha=a)
        fr.text((880, y + 24), val, F["numM"], col, anchor="ra", alpha=a)

    a4 = fade(t, 4.2, 0.6)
    fr.rect((150, 660, 900, 742), PANEL2, a4, radius=10)
    fr.text((176, 701), "11% do alvo consumido antes de qualquer acerto",
            F["body"], AMBER, anchor="lm", alpha=a4)

    a5 = fade(t, 5.4, 0.6)
    fr.text((160, 790), "A REGRA", F["label"], ACCENT, alpha=a5)
    fr.text((160, 826), "ATR  ≥  4 × 11  =  44 pontos", F["h3"], INK, alpha=a5)
    fr.text((160, 882), "Abaixo disso não existe movimento no gráfico", F["small"], INK2, alpha=fade(t, 6.0))
    fr.text((160, 914), "que pague a operação. A linha fica cinza.", F["small"], INK2, alpha=fade(t, 6.0))

    # ATR of the example session against the threshold
    a6 = fade(t, 7.0, 0.7)
    bx0, by0, bx1, by1 = 1010, 340, 1790, 700
    fr.rect((bx0 - 20, by0 - 44, bx1 + 20, by1 + 20), PANEL, a6, radius=10)
    fr.text((bx0, by0 - 34), "ATR DA SESSÃO DE EXEMPLO  (pontos)", F["label"], INK3, alpha=a6)
    vals = [v for v in D["atr"] if v is not None]
    vmax = max(vals) * 1.15
    n = len(D["atr"])
    step = (bx1 - bx0) / n
    ythr = by1 - (44 / vmax) * (by1 - by0)
    reveal = ease(min(1.0, max(0.0, (t - 7.4) / 2.6)))
    for i in range(int(n * reveal)):
        v = D["atr"][i]
        if v is None:
            continue
        y = by1 - (v / vmax) * (by1 - by0)
        col = GATE if v < 44 else ACCENT
        fr.rect((bx0 + i * step, y, bx0 + (i + 1) * step - 1, by1), col, a6 * 0.95)
    fr.dashed(bx0, ythr, bx1, AMBER, 2, a6)
    fr.text((bx1, ythr - 26), "44", F["numS"], AMBER, anchor="ra", alpha=a6)

    a7 = fade(t, 10.6, 0.7)
    fr.rect((1010, 748, 1790, 940), PANEL2, a7, radius=12)
    fr.text((1040, 790), "NO TESTE, EM MERCADO PARADO", F["label"], INK3, alpha=a7)
    fr.text((1040, 850), "94", F["h2"], INK2, anchor="lm", alpha=a7)
    fr.text((1130, 850), "entradas", F["body"], INK3, anchor="lm", alpha=a7)
    fr.text((1420, 850), "→", F["h3"], INK3, anchor="mm", alpha=a7)
    fr.text((1530, 850), "0", F["h2"], GREEN, anchor="lm", alpha=a7)
    fr.text((1590, 850), "com o gate", F["body"], INK3, anchor="lm", alpha=a7)
    fr.footer(t)


def scene_live(fr: Frame, t: float, D: dict):
    title_block(fr, t, "ao vivo", "O indicador percorrendo um pregão")
    ch = Chart(D, (140, 300, 1700, 640))
    osc = Oscillator(D, (140, 720, 1700, 940))
    ch.grid(fr, 1.0)
    osc.frame(fr, 1.0)

    lead = 1.2
    play = max(0.0, t - lead)
    span = 33.0
    k = int(min(1.0, play / span) * ch.n)
    ch.candles(fr, k, 1.0)
    ch.series(fr, "ema9", ACCENT, k, 2, 0.9)
    ch.series(fr, "vwap", AMBER, k, 2, 0.75)
    osc.bars(fr, k, 1.0)

    i = max(0, min(ch.n - 1, k - 1))
    s = D["score"][i]
    atr = D["atr"][i]
    if s is not None and atr is not None:
        gate_off = atr < D["atr_min"]
        if gate_off:
            label, col = "CUSTO NÃO PAGA", GATE
        elif s >= D["threshold"]:
            label, col = "CONFLUÊNCIA DE COMPRA", GREEN
        elif s <= -D["threshold"]:
            label, col = "CONFLUÊNCIA DE VENDA", RED
        else:
            label, col = "SEM CONFLUÊNCIA", INK3
        fr.rect((1170, 96, 1790, 232), PANEL2, 1.0, radius=12)
        fr.rect((1170, 96, 1178, 232), col, 1.0)
        fr.text((1206, 128), label, F["label"], col)
        fr.text((1206, 168), f"{s:+.0f}", F["num"], col)
        fr.text((1770, 132), f"ATR {atr:.0f} pts", F["numS"], INK3, anchor="ra")
        fr.text((1770, 168), f"limite {D['atr_min']:.0f}", F["numS"], INK3, anchor="ra")
        fr.text((1770, 204), f"barra {i + 1}/{ch.n}", F["numS"], INK3, anchor="ra")
    fr.footer(t)


def scene_honesto(fr: Frame, t: float, D: dict):
    title_block(fr, t, "antes de operar isto", "O indicador organiza contexto.",
                "Ele não tem vantagem demonstrada.")
    rows = [
        ("R$ 27,58", "por sessão é o lucro que a BUSCA sozinha fabrica,\nrodando 104 variantes sobre ruído puro", AMBER, 1.2),
        ("59 de 104", "variantes ficam positivas depois dos custos\nem série sem vantagem nenhuma", AMBER, 2.8),
        ("p = 0,364", "é o que este indicador devolve contra o nulo calibrado —\no teste corretamente não acusa vantagem onde não há", ACCENT, 4.4),
        ("97%", "dos que persistiram 300+ pregões no mini índice\nperderam dinheiro  (FGV-EESP, a pedido da CVM)", RED, 6.0),
    ]
    for label, text, col, st in rows:
        a = fade(t, st, 0.6)
        y = 330 + rows.index((label, text, col, st)) * 152
        fr.text((150, y + 10), label, F["h2"], col, alpha=a)
        for j, ln in enumerate(text.split("\n")):
            fr.text((620, y + 14 + j * 40), ln, F["body"], INK2, alpha=a)

    a = fade(t, 8.0, 0.8)
    fr.line([(150, 962), (1770, 962)], RULE, 2, a)
    fr.text((150, 990), "Rode sobre os seus dados de WIN e veja se passa do placebo.",
            F["body"], INK, alpha=a)
    fr.text((1770, 992), "research/b3_setups", F["small"], INK3, anchor="ra", alpha=a)


SCENES = [
    ("intro", 6.0, scene_intro),
    ("regra", 13.0, scene_regra),
    ("camadas", 41.0, scene_camadas),
    ("placar", 19.0, scene_placar),
    ("gate", 20.0, scene_gate),
    ("live", 42.0, scene_live),
    ("honesto", 16.0, scene_honesto),
]


def load_data() -> dict:
    D = scene_series(SEED)
    from b3setups.setups import confluence_score

    # The displayed bars alone would restart the warm-up, so the breakdown is
    # taken from the same full series scene_data computed the score over.
    from scene_data import build_session

    all_bars, d0 = build_session(SEED)
    _s, _a, parts = confluence_score(all_bars, return_components=True)
    D["parts"] = parts[d0:]

    score = D["score"]
    n = len(score)
    # All five layers active makes the waterfall teach the whole mechanism,
    # including the RSI braking against the score's own direction.
    full = [
        i for i in range(n)
        if D["parts"][i] and all(abs(v) > 0.01 for v in D["parts"][i].values())
    ]
    D["focus_i"] = (
        max(full, key=lambda i: abs(score[i]))
        if full
        else max((i for i in range(n) if score[i] is not None), key=lambda i: abs(score[i]))
    )
    fi = D["focus_i"]
    phases = [(30, "fase morta"), (70, "fase de tendência")]
    D["focus_phase"] = next((label for cut, label in phases if fi < cut), "fase de reversão")
    return D


def build_frame(D: dict, gt: float) -> Frame:
    acc = 0.0
    for name, dur, fn in SCENES:
        if gt < acc + dur:
            fr = Frame()
            fn(fr, gt - acc, D)
            # cross-fade to black at each seam keeps cuts from flashing
            local = gt - acc
            if local < 0.35:
                k = 1.0 - ease(local / 0.35)
                fr.img = Image.blend(fr.img, Image.new("RGB", (W, H), BG), k * 0.85)
            if dur - local < 0.35:
                k = 1.0 - ease((dur - local) / 0.35)
                fr.img = Image.blend(fr.img, Image.new("RGB", (W, H), BG), k * 0.85)
            return fr
        acc += dur
    fr = Frame()
    SCENES[-1][2](fr, SCENES[-1][1], D)
    return fr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="video/confluencia_b3.mp4")
    ap.add_argument("--probe", type=float, default=None,
                    help="render one PNG per scene at this offset into each scene")
    args = ap.parse_args()

    D = load_data()
    total = sum(d for _, d, _ in SCENES)

    if args.probe is not None:
        acc = 0.0
        out = Path("video/probe")
        out.mkdir(parents=True, exist_ok=True)
        for name, dur, _fn in SCENES:
            gt = acc + min(args.probe, dur - 0.5)
            build_frame(D, gt).img.save(out / f"{name}.png")
            acc += dur
        print(f"probe frames in {out}/  (total {total:.0f}s, {int(total * FPS)} frames)")
        return 0

    import imageio_ffmpeg

    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
        "-movflags", "+faststart", args.out,
    ]
    n_frames = int(total * FPS)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for f in range(n_frames):
        proc.stdin.write(build_frame(D, f / FPS).img.tobytes())
        if f % 300 == 0:
            print(f"  {f}/{n_frames}  ({100 * f / n_frames:.0f}%)", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"done: {args.out}  ({total:.0f}s, {n_frames} frames)")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
