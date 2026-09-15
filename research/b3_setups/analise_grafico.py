#!/usr/bin/env python3
"""Which chart does the indicator run on? Measured, not asserted.

What is compared is deliberately restricted to properties that do NOT depend on
the series having an edge, because the control series has none by construction:

  sinais/sessão      how often the setup fires
  risco médio        the structural stop the chart produces, in points
  acerto exigido     (R + custo) / (R * (1 + alvo)) — exact arithmetic
  custo/bruto        how much of the gross the friction eats
  gate ativo         share of bars where the cost gate has an opinion

All five are structural. Whether any edge exists is a separate question that
needs real WIN data and run_replay.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from b3setups import indicators as ind
from b3setups.contracts import WIN, CostModel, cents_to_brl
from b3setups.data import synthetic_sessions
from b3setups.engine import ExecConfig, run
from b3setups.replay import required_win_rate, fair_win_rate
from b3setups.resample import resample, sessions_from, to_renko
from b3setups.setups import ConfluenciaSinal, confluence_score

COST_POINTS = 11.0
REWARD = 2.5
N_SESSIONS = 60
GATE_MIN = 44.0


def measure(label: str, sessions, note: str = "") -> dict:
    setup = ConfluenciaSinal(min_risk_ticks=2, max_risk_ticks=10, reward_r=REWARD)
    costs = CostModel()
    trades = run(sessions, setup, WIN, costs, ExecConfig(target_r=REWARD))

    gate_on = gate_total = 0
    atr_lo = atr_hi = None
    for s in sessions:
        _sc, a = confluence_score(s.bars)
        for v in a:
            if v is None:
                continue
            gate_total += 1
            if v >= GATE_MIN:
                gate_on += 1
            atr_lo = v if atr_lo is None else min(atr_lo, v)
            atr_hi = v if atr_hi is None else max(atr_hi, v)

    # Raw structural stop the chart itself produces, before any cap: the
    # 5-bar swing. This is the number that actually varies with the axis.
    raw = []
    for sess in sessions:
        b = sess.bars
        for i in range(5, len(b)):
            w = b[i - 4 : i + 1]
            raw.append(max(x.high for x in w) - min(x.low for x in w))
    raw_stop = sum(raw) / len(raw) if raw else 0.0
    ranges = [b.high - b.low for sess in sessions for b in sess.bars]
    bar_range = sum(ranges) / len(ranges) if ranges else 0.0

    risks = []
    for t in trades:
        if t.reason == "stop":
            risks.append(abs(WIN.points(t.tick_delta)))
        elif t.reason == "target":
            risks.append(abs(WIN.points(t.tick_delta)) / REWARD)
    avg_risk = sum(risks) / len(risks) if risks else 0.0
    gross = sum(t.gross_cents for t in trades)
    cost = sum(t.cost_cents for t in trades)
    n_bars = sum(len(s) for s in sessions)

    return {
        "label": label,
        "note": note,
        "bars_session": n_bars / max(1, len(sessions)),
        "trades": len(trades),
        "per_session": len(trades) / max(1, len(sessions)),
        "avg_risk": avg_risk,
        "raw_stop": raw_stop,
        "bar_range": bar_range,
        "required": required_win_rate(avg_risk, COST_POINTS, REWARD) if avg_risk else float("nan"),
        "drag": (100.0 * cost / gross) if gross > 0 else float("nan"),
        "gate_pct": (100.0 * gate_on / gate_total) if gate_total else float("nan"),
        "atr_lo": atr_lo or 0.0,
        "atr_hi": atr_hi or 0.0,
    }


def row(m: dict) -> str:
    req = f"{100 * m['required']:>6.1f}%" if m["required"] == m["required"] else f"{'—':>7}"
    gate = f"{m['gate_pct']:>7.0f}%" if m["gate_pct"] == m["gate_pct"] else f"{'—':>8}"
    # How much noise the stop has to survive: one bar's own range.
    noise = m["avg_risk"] / m["bar_range"] if m["bar_range"] > 0 else float("nan")
    noise_s = f"{noise:>7.2f}x" if noise == noise else f"{'—':>8}"
    custo_alvo = 100.0 * COST_POINTS / (REWARD * m["avg_risk"]) if m["avg_risk"] > 0 else float("nan")
    ca = f"{custo_alvo:>8.0f}%" if custo_alvo == custo_alvo else f"{'—':>9}"
    return (f"{m['label']:<12} {m['bars_session']:>7.0f} {m['per_session']:>8.1f} "
            f"{m['bar_range']:>8.0f} {m['raw_stop']:>9.0f} {m['avg_risk']:>7.0f} "
            f"{noise_s} {req} {ca} {gate}  {m['note']}")


def main() -> int:
    base = synthetic_sessions(
        WIN, n_sessions=N_SESSIONS, bars_per_session=540,
        bar_sd_ticks=10.7, minutes_per_bar=1, seed=606061,
    )
    flat = [b for s in base for b in s.bars]
    print(f"série de controle: {N_SESSIONS} sessões de 540 barras de 1 minuto "
          f"({len(flat)} barras)\n")

    head = (f"{'gráfico':<12} {'barras/s':>7} {'sinais/s':>8} {'range bar':>8} "
            f"{'swing 5b':>9} {'stop':>7} {'stop/bar':>8} {'exige':>7} "
            f"{'custo/alvo':>9} {'gate on':>8}")
    print("TEMPO (minutos)")
    print(head)
    print("-" * (len(head) + 22))
    results = []
    for m in (1, 2, 3, 5, 10, 15, 30):
        s = sessions_from(resample(flat, m))
        if not s:
            continue
        r = measure(f"{m} min", s)
        results.append(r)
        print(row(r))

    print(f"\nRENKO (tijolo em pontos; 1 tick = 5 pontos no WIN)")
    print(head)
    print("-" * (len(head) + 22))
    renkos = []
    for bricks, name in ((75.0, "15R"), (125.0, "25R"), (175.0, "35R")):
        s = sessions_from(to_renko(flat, bricks))
        if not s:
            continue
        r = measure(f"renko {name}", s, note="ATR congelado")
        renkos.append((r, bricks))
        print(row(r))

    print("\n" + "=" * 78)
    print("POR QUE O RENKO QUEBRA ESTE INDICADOR")
    print("=" * 78)
    for r, bricks in renkos:
        print(f"  {r['label']:<11} ATR varia de {r['atr_lo']:.1f} a {r['atr_hi']:.1f} pontos "
              f"— amplitude de {r['atr_hi'] - r['atr_lo']:.1f}")
    ref = next((r for r in results if r["label"] == "5 min"), None)
    if ref:
        print(f"  {'5 min':<11} ATR varia de {ref['atr_lo']:.1f} a {ref['atr_hi']:.1f} pontos "
              f"— amplitude de {ref['atr_hi'] - ref['atr_lo']:.1f}")
    print()
    print("  Todo tijolo Renko tem a MESMA altura por construção, então o ATR fica")
    print("  praticamente congelado. O gate de custo compara ATR com 44 pontos:")
    print("  num tijolo de 125 pontos ele nunca fecha, num de 25 nunca abre.")
    print("  A camada que existe para dizer 'hoje não paga' para de funcionar.")
    print()
    print("  E o volume por tijolo mistura um tijolo que levou uma hora com outro que")
    print("  levou dez segundos, então 'volume acima da média' passa a medir duração,")
    print("  não participação. Duas das seis camadas morrem; uma terceira distorce.")

    print("\n" + "=" * 78)
    print("O CRITÉRIO QUE DECIDE O TEMPO GRÁFICO")
    print("=" * 78)
    print("  'stop/bar' é o stop dividido pelo range médio de UMA barra.")
    print("  Abaixo de 1,0 o stop cabe dentro do ruído de uma única barra: você")
    print("  é estopado pela oscilação normal, não por estar errado na direção.")
    print()
    for r in results:
        if r["bar_range"] <= 0 or r["avg_risk"] <= 0:
            continue
        ratio = r["avg_risk"] / r["bar_range"]
        cap_share = 100.0 * r["avg_risk"] / r["raw_stop"] if r["raw_stop"] > 0 else 0.0
        if ratio < 0.7:
            v = "stop dentro do ruído de uma barra"
        elif ratio < 1.2:
            v = "stop na fronteira do ruído"
        else:
            v = "stop acima do ruído de uma barra"
        print(f"  {r['label']:<8} stop/bar {ratio:>4.2f}x | o teto responde por "
              f"{100 - cap_share:>4.0f}% do stop estrutural   {v}")
    print()
    print("  Quanto mais lento o gráfico, maior o swing natural — e mais o teto de 50")
    print("  pontos deixa de ser 'o stop do gráfico' e vira uma distância arbitrária.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
