"""Calibration tests for the placebo null and the simulator's known artifact.

These are the tests that stop this project from fooling itself. If a change to
the engine, the setups or the statistics makes a no-edge series look profitable
*after* calibration, one of these fails. Run:  python3 tests/placebo_test.py
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups.contracts import WIN, CostModel  # noqa: E402
from b3setups.data import synthetic_sessions  # noqa: E402
from b3setups.engine import ExecConfig, run  # noqa: E402
from b3setups.placebo import calibrate  # noqa: E402
from b3setups.setups import (  # noqa: E402
    LONG,
    SHORT,
    DidiAgulhada,
    Entry,
    Plan,
    Setup,
    Setup91,
    Setup92,
    Setup93,
)
from b3setups.stats import session_pnl  # noqa: E402

FAILURES: list[str] = []
NO_COST = CostModel(brokerage_cents_per_side=0, exchange_cents_per_side=0, slippage_ticks_per_side=0)


class PureBreakout(Setup):
    """No filter: every bar arms a breakout of its own extreme."""

    def __init__(self, side: int):
        self.side = side
        self.name = f"breakout({'L' if side == LONG else 'S'})"

    def plan(self, bars, contract):
        p = Plan.blank(len(bars))
        tick = contract.tick_size
        for i in range(len(bars)):
            if self.side == LONG:
                p.entries[i] = Entry(LONG, bars[i].high + tick, bars[i].low, 3)
            else:
                p.entries[i] = Entry(SHORT, bars[i].low - tick, bars[i].high, 3)
        return p


# --- The generator must be a martingale: no drift in close-to-close returns.
drifts = []
for seed in range(12):
    s = synthetic_sessions(WIN, n_sessions=30, seed=5000 + seed)
    c = [b.close for ss in s for b in ss.bars]
    r = [c[i] - c[i - 1] for i in range(1, len(c))]
    drifts.append(statistics.mean(r) / (statistics.stdev(r) / len(r) ** 0.5))
mean_t = statistics.mean(drifts)
if abs(mean_t) > 1.5:
    FAILURES.append(f"synthetic generator shows drift: mean t-stat {mean_t:+.2f}")
print(f"  generator drift t-stat across 12 seeds: {mean_t:+.3f} (must stay near 0)")

# --- KNOWN ARTIFACT, asserted on purpose so it cannot silently change.
# At OHLC resolution the intrabar order is unknowable, so a pure breakout shows
# a positive gross expectancy on a martingale. It is small and bounded; if it
# grows, the engine has acquired a new bias and the placebo null shifts.
arts = []
for side in (LONG, SHORT):
    ms = []
    for seed in range(10):
        s = synthetic_sessions(WIN, n_sessions=30, seed=1000 + seed)
        t = run(s, PureBreakout(side), WIN, NO_COST, ExecConfig(target_r=2.0))
        if t:
            ms.append(sum(x.gross_cents for x in t) / len(t))
    arts.append(statistics.mean(ms))
print(f"  OHLC artifact (gross, no costs): long {arts[0]:+.0f} c/trade, short {arts[1]:+.0f} c/trade")
for label, a in zip(("long", "short"), arts):
    if not 0.0 <= a <= 600.0:
        FAILURES.append(
            f"breakout {label} artifact {a:+.0f} c/trade outside the documented 0..600 band — "
            "the engine's bias changed; re-derive the placebo null before trusting results"
        )

# --- The placebo must NOT flag a no-edge series as an edge.
family = [Setup91(9), Setup92(9), Setup93(9), DidiAgulhada()]
target_rs: list[float | None] = [1.0, 2.0]
costs = CostModel()

cal = calibrate(family, target_rs, WIN, costs, n_series=10, n_sessions=30, base_seed=880001)

held_out = synthetic_sessions(WIN, n_sessions=30, seed=999331)
best_observed = -float("inf")
for setup in family:
    for tr in target_rs:
        trades = run(held_out, setup, WIN, costs, ExecConfig(target_r=tr))
        per = session_pnl(trades, held_out)
        best_observed = max(best_observed, sum(per) / len(per))

p = cal.p_value(best_observed)
print(f"  placebo p-value on a held-out no-edge series: {p:.3f} (must not be < 0.05)")
if p < 0.05:
    FAILURES.append(
        f"placebo declared an edge on a no-edge series: p={p:.4f}. "
        "The null is mis-calibrated and every real result would be overstated."
    )

# --- The placebo null must itself be positive: that is the whole point.
if cal.median <= 0:
    FAILURES.append(
        f"placebo median is {cal.median:.1f} — expected a POSITIVE fake edge from the search; "
        "a non-positive null means calibrate() is not exercising the family"
    )
print(f"  placebo median fake edge: {cal.median:+.1f} centavos/session over {cal.family_size} variants")

# --- p_value must be monotone and bounded.
if not cal.p_value(float("inf")) <= cal.p_value(-float("inf")):
    FAILURES.append("placebo p_value is not monotone")
if not 0.0 < cal.p_value(0.0) <= 1.0:
    FAILURES.append("placebo p_value out of range")

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("placebo_test: all calibration checks passed")
