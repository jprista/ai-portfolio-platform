#!/usr/bin/env python3
"""What actually reduces the pain of the stop — measured, one lever at a time.

The complaint "more stops than gains" is, at a 2.5R target, the design: the
geometry alone caps the hit rate at 1/(1+2.5) = 28.6%. So the question is not
how to stop losing trades, it is which of the legitimate levers moves the
outcome distribution, and what each one costs.

Four levers, isolated:

  stop fora do ruído   widen the stop past one bar's range, so noise stops
                       stop firing
  zero a zero          move the stop to entry after 1R, turning give-backs
                       into scratches
  saída parcial        book half at 1R and let half run to the target
  alvo menor           trade reward for reachability

Everything is counted per POSITION. Scaling out would otherwise inflate the
hit rate for free.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from b3setups.contracts import WIN, CostModel, cents_to_brl
from b3setups.data import synthetic_sessions
from b3setups.engine import ExecConfig, run
from b3setups.setups import ConfluenciaSinal
from b3setups.stats import summarise_positions

SESSIONS = 200
SEED = 4242


def main() -> int:
    s = synthetic_sessions(WIN, n_sessions=SESSIONS, seed=SEED, bars_per_session=108, bar_sd_ticks=24.0)
    rng = [b.high - b.low for x in s for b in x.bars]
    bar_range = sum(rng) / len(rng)
    costs = CostModel()
    wide = int(round(bar_range / WIN.tick_size))  # stop of one bar's range

    print(f"série de controle · {SESSIONS} sessões · range médio da barra {bar_range:.0f} pts")
    print(f"stop 'fora do ruído' = {wide} ticks = {wide * WIN.tick_size:.0f} pts\n")

    configs = [
        ("A · atual (2,5R, stop 50p)", 10, 2.5, None, None, 1),
        ("B · stop fora do ruído", wide, 2.5, None, None, 1),
        ("C · B + zero a zero em 1R", wide, 2.5, 1.0, None, 1),
        ("D · B + parcial em 1R", wide, 2.5, None, 1.0, 2),
        ("E · B + parcial + zero a zero", wide, 2.5, 1.0, 1.0, 2),
        ("F · E com alvo 1,5R", wide, 1.5, 1.0, 1.0, 2),
        ("G · E com alvo 1,0R", wide, 1.0, 0.5, 0.5, 2),
    ]

    head = (f"{'configuração':<32} {'posições':>9} {'verde':>7} {'zero':>6} {'vermelho':>9} "
            f"{'não-perde':>10} {'payoff':>7} {'exp/pos':>10} {'total':>12}")
    print(head)
    print("-" * len(head))
    for name, cap, reward, be, part, ctr in configs:
        setup = ConfluenciaSinal(min_risk_ticks=2, max_risk_ticks=cap, reward_r=reward)
        cfg = ExecConfig(target_r=reward, contracts=ctr, breakeven_at_r=be,
                         partial_at_r=part, partial_fraction=0.5)
        st = summarise_positions(name, run(s, setup, WIN, costs, cfg))
        if not st.n_positions:
            continue
        # normalise by contracts so A (1 lote) and D (2 lotes) stay comparable
        exp = st.expectancy_cents / ctr
        tot = st.total_cents / ctr
        pay = "inf" if st.payoff == float("inf") else f"{st.payoff:.2f}"
        print(f"{name:<32} {st.n_positions:>9} {100*st.win_rate:>6.1f}% "
              f"{100*st.flats/st.n_positions:>5.1f}% {100*st.losses/st.n_positions:>8.1f}% "
              f"{100*st.green_rate:>9.1f}% {pay:>7} {cents_to_brl(round(exp)):>10} "
              f"{cents_to_brl(round(tot)):>12}")

    print("\n'não-perde' = verde + zero a zero. É o que se sente operando.")
    print("'exp/pos' e 'total' normalizados por contrato, senão 2 lotes parecem o dobro.")
    print("\nTodos rodaram sobre série SEM vantagem: o total negativo é o esperado e correto.")
    print("O que transfere é a FORMA da distribuição, não o nível.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
