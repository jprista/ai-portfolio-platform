#!/usr/bin/env python3
"""Exports the indicator running on several chart axes, as JSON for the viewer.

One underlying 1-minute series is transformed into each axis, so any difference
the viewer shows comes from the axis alone and not from a different market.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from b3setups.contracts import WIN, CostModel, cents_to_brl
from b3setups.data import synthetic_sessions
from b3setups.engine import ExecConfig, run
from b3setups.replay import required_win_rate
from b3setups.resample import resample, sessions_from, to_renko
from b3setups.setups import ConfluenciaSinal, confluence_score
from b3setups import indicators as ind

COST_POINTS = 11.0
COST_BRL = 2.54
REWARD = 2.5
GATE_MIN = 44.0
SEED = 606061


def pack(label: str, kind: str, sessions, show_day_index: int = 1) -> dict:
    """Series for one chart axis, plus the numbers that decide the axis."""
    costs = CostModel()
    setup = ConfluenciaSinal(min_risk_ticks=2, max_risk_ticks=10, reward_r=REWARD)
    trades = run(sessions, setup, WIN, costs, ExecConfig(target_r=REWARD))

    # Aggregate stats over ALL sessions.
    ranges = [b.high - b.low for s in sessions for b in s.bars]
    bar_range = sum(ranges) / len(ranges)
    swings = []
    for s in sessions:
        b = s.bars
        for i in range(4, len(b)):
            w = b[i - 4 : i + 1]
            swings.append(max(x.high for x in w) - min(x.low for x in w))
    swing = sum(swings) / len(swings) if swings else 0.0

    risks = [
        abs(WIN.points(t.tick_delta)) if t.reason == "stop"
        else abs(WIN.points(t.tick_delta)) / REWARD
        for t in trades if t.reason in ("stop", "target")
    ]
    avg_risk = sum(risks) / len(risks) if risks else 0.0
    per_session = len(trades) / len(sessions)

    atr_all = []
    for s in sessions:
        _sc, a = confluence_score(s.bars)
        atr_all.extend(v for v in a if v is not None)

    # One session is drawn. It is replayed with the preceding session as
    # warm-up, exactly as the engine does, so the drawn score is the real one.
    day = sessions[min(show_day_index, len(sessions) - 1)]
    warm = sessions[show_day_index - 1].bars if show_day_index > 0 else []
    full = list(warm) + day.bars
    off = len(warm)
    score, atr = confluence_score(full)
    vwap = ind.session_vwap(full)
    ema9 = ind.ema([b.close for b in full], 9)

    plan = setup.plan(full, WIN)
    signals = []
    for i in range(off, len(full)):
        e = plan.entries[i]
        if e is None:
            continue
        entry = full[i].close
        risk = abs(entry - e.stop)
        signals.append({
            "i": i - off,
            "side": e.side,
            "entry": round(entry, 1),
            "stop": round(e.stop, 1),
            "target": round(entry + REWARD * risk * (1 if e.side == 1 else -1), 1),
            "risk": round(risk, 1),
        })

    bars = [
        {"o": round(b.open, 1), "h": round(b.high, 1), "l": round(b.low, 1),
         "c": round(b.close, 1), "v": round(b.volume)}
        for b in day.bars
    ]
    return {
        "label": label,
        "kind": kind,
        "bars": bars,
        "score": [None if x is None else round(x, 1) for x in score[off:]],
        "atr": [None if x is None else round(x, 1) for x in atr[off:]],
        "vwap": [None if x is None else round(x, 1) for x in vwap[off:]],
        "ema9": [None if x is None else round(x, 1) for x in ema9[off:]],
        "signals": signals,
        "stats": {
            "barsPerSession": round(sum(len(s) for s in sessions) / len(sessions)),
            "signalsPerSession": round(per_session, 1),
            "barRange": round(bar_range),
            "swing": round(swing),
            "stop": round(avg_risk),
            "stopOverBar": round(avg_risk / bar_range, 2) if bar_range else None,
            "required": round(100 * required_win_rate(avg_risk, COST_POINTS, REWARD), 1)
            if avg_risk else None,
            "frictionPerSession": round(per_session * COST_BRL, 2),
            "atrMin": round(min(atr_all), 1) if atr_all else 0,
            "atrMax": round(max(atr_all), 1) if atr_all else 0,
            "atrSpread": round(max(atr_all) - min(atr_all), 1) if atr_all else 0,
        },
    }


def main() -> int:
    base = synthetic_sessions(
        WIN, n_sessions=30, bars_per_session=540,
        bar_sd_ticks=10.7, minutes_per_bar=1, seed=SEED,
    )
    flat = [b for s in base for b in s.bars]

    out = {"gateMin": GATE_MIN, "reward": REWARD, "costPoints": COST_POINTS,
           "costBrl": COST_BRL, "fair": round(100 / (1 + REWARD), 1), "axes": []}

    for minutes in (1, 3, 5, 15):
        s = sessions_from(resample(flat, minutes))
        out["axes"].append(pack(f"{minutes} min", "tempo", s))
    for brick, name in ((75.0, "15R"), (125.0, "25R")):
        s = sessions_from(to_renko(flat, brick))
        out["axes"].append(pack(f"Renko {name}", "renko", s))

    dest = Path(__file__).resolve().parent / "chart_data.json"
    dest.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{dest}  ({dest.stat().st_size / 1024:.0f} KB)")
    for a in out["axes"]:
        st = a["stats"]
        print(f"  {a['label']:<10} {st['barsPerSession']:>4} barras/s  "
              f"{st['signalsPerSession']:>5} sinais/s  stop/bar {st['stopOverBar']}  "
              f"exige {st['required']}%  fricção R$ {st['frictionPerSession']}/sessão  "
              f"ATR spread {st['atrSpread']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
