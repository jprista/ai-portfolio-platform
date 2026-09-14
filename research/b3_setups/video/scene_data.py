"""Builds the example session the video plays, and scores it with the real code.

The price series is SYNTHETIC and labelled as such on screen. It is shaped into
three phases so the video can show each state of the indicator on purpose
rather than hoping a random draw contains them:

    fase 1  mercado morto      ATR baixo  -> gate de custo corta
    fase 2  tendencia          ATR sobe   -> placar verde
    fase 3  exaustao/correcao  IFR freia  -> placar esvazia

Everything drawn from this module downstream — score, ATR, EMAs, VWAP, ADX —
comes from b3setups, not from hand-written numbers. If the indicator changes,
the video changes with it.
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from b3setups import indicators as ind  # noqa: E402
from b3setups.bars import Bar  # noqa: E402
from b3setups.contracts import WIN  # noqa: E402
from b3setups.setups import confluence_score  # noqa: E402

PHASES = [
    # (n_bars, drift_ticks_per_bar, sd_ticks, volume_scale)
    (30, 0.0, 3.0, 0.50),     # morto        -> gate corta
    (40, 2.8, 11.0, 1.35),    # tendencia    -> placar verde
    (38, -2.7, 10.5, 1.20),   # reversao     -> placar vermelho
]
SUBSTEPS = 12


WARMUP_BARS = 70
"""A full prior session, computed but never shown.

An MME50 plus Wilder's ADX need roughly fifty bars before they say anything.
Without a warm-up day the first half of the displayed session would carry no
score at all — which is true of the real indicator too, and is exactly why a
trader opens the chart with history behind it rather than at the opening bell.
"""


def _phase_bars(rng, price, clock, n_bars, drift, sd, vol_scale):
    step_sd = sd / SUBSTEPS**0.5
    step_drift = drift / SUBSTEPS
    out = []
    for _ in range(n_bars):
        path = [price]
        for _ in range(SUBSTEPS):
            path.append(path[-1] + round(rng.gauss(step_drift, step_sd)))
        o, c = path[0], path[-1]
        hi, lo = max(path), min(path)
        vol = max(200.0, rng.gauss(9000.0 * vol_scale, 1500.0))
        out.append(
            Bar(
                ts=clock,
                open=WIN.to_price(o),
                high=WIN.to_price(hi),
                low=WIN.to_price(lo),
                close=WIN.to_price(c),
                volume=round(vol),
            )
        )
        price = c
        clock += timedelta(minutes=5)
    return out, price, clock


def build_session(seed: int = 7, start_price: float = 132_000.0) -> tuple[list[Bar], int]:
    """Returns (all bars, index where the displayed session starts)."""
    rng = random.Random(seed)
    price = WIN.to_ticks(start_price)
    bars: list[Bar] = []

    clock = datetime.combine(datetime(2026, 4, 13).date(), time(9, 5))
    warm, price, _ = _phase_bars(rng, price, clock, WARMUP_BARS, 0.4, 7.0, 1.0)
    bars.extend(warm)

    display_from = len(bars)
    clock = datetime.combine(datetime(2026, 4, 14).date(), time(9, 5))
    for n_bars, drift, sd, vol_scale in PHASES:
        seg, price, clock = _phase_bars(rng, price, clock, n_bars, drift, sd, vol_scale)
        bars.extend(seg)
    return bars, display_from


def scene_series(seed: int = 7) -> dict:
    """Bars plus every series the video draws, all from the real indicator.

    Indicators are computed over the warm-up session as well and only then
    sliced to the displayed day, so every value on screen is the value the
    indicator would actually show on a chart with history behind it.
    """
    bars, d0 = build_session(seed)
    closes = [b.close for b in bars]
    volumes = [b.volume for b in bars]
    scores, atr = confluence_score(bars)
    di_p, di_m, adx_v = ind.adx(bars, 14)
    cut = lambda s: s[d0:]  # noqa: E731
    return {
        "bars": bars[d0:],
        "score": cut(scores),
        "atr": cut(atr),
        "ema9": cut(ind.ema(closes, 9)),
        "ema21": cut(ind.ema(closes, 21)),
        "ema50": cut(ind.ema(closes, 50)),
        "vwap": cut(ind.session_vwap(bars)),
        "rsi": cut(ind.rsi(closes, 14)),
        "vol_avg": cut(ind.sma(volumes, 20)),
        "di_plus": cut(di_p),
        "di_minus": cut(di_m),
        "adx": cut(adx_v),
        # Cost gate, exactly as the NTSL indicator computes it.
        "cost_points_round_trip": 11.0,
        "atr_multiple": 4.0,
        "atr_min": 44.0,
        "threshold": 45.0,
    }


if __name__ == "__main__":
    d = scene_series()
    n = len(d["bars"])
    print(f"bars: {n}")
    gate_off = [i for i in range(n) if d["atr"][i] is not None and d["atr"][i] < d["atr_min"]]
    green = [i for i in range(n) if d["score"][i] is not None and d["score"][i] >= 45]
    red = [i for i in range(n) if d["score"][i] is not None and d["score"][i] <= -45]
    print(f"gate OFF (ATR < 44 pts): {len(gate_off)} barras, indices {gate_off[:6]}..{gate_off[-3:] if gate_off else ''}")
    print(f"placar verde (>= +45):   {len(green)} barras, indices {green[:8]}")
    print(f"placar vermelho (<= -45):{len(red)} barras, indices {red[:8]}")
    ok = [s for s in d["score"] if s is not None]
    print(f"placar: min {min(ok):.0f}  max {max(ok):.0f}")
    a = [x for x in d["atr"] if x is not None]
    print(f"ATR pontos: min {min(a):.0f}  max {max(a):.0f}  (limite do gate = 44)")
    px = [b.close for b in d["bars"]]
    print(f"preco: {px[0]:.0f} -> max {max(px):.0f} -> fim {px[-1]:.0f}")
