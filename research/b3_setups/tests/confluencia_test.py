"""Tests for the Confluencia indicator and its NTSL twin's logic.

The behavioural claims made in profit/ConfluenciaB3.ntsl are asserted here, so
the documentation and the code cannot drift apart silently.
Run:  python3 tests/confluencia_test.py
"""
from __future__ import annotations

import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups.bars import Bar, Session  # noqa: E402
from b3setups.contracts import WIN, CostModel  # noqa: E402
from b3setups.data import synthetic_sessions  # noqa: E402
from b3setups.engine import ExecConfig, run  # noqa: E402
from b3setups.placebo import calibrate  # noqa: E402
from b3setups.setups import LONG, SHORT, Confluencia, confluence_score  # noqa: E402
from b3setups.stats import session_pnl  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        FAILURES.append(f"{name}{(': ' + detail) if detail else ''}")


sessions = synthetic_sessions(WIN, n_sessions=40, seed=31337)
all_scores: list[float] = []
for s in sessions:
    sc, _ = confluence_score(s.bars)
    all_scores.extend(x for x in sc if x is not None)

# --- The score must stay inside the documented band.
# Worst case: 30 + 25 + 20 weights, plus the 10 volume bonus = 85 in magnitude;
# the RSI brake only ever subtracts. 100 is the documented outer bound.
check("score produced", len(all_scores) > 1000, f"only {len(all_scores)} values")
check(
    "score within [-100, 100]",
    all(-100.0 <= x <= 100.0 for x in all_scores),
    f"range [{min(all_scores):.1f}, {max(all_scores):.1f}]",
)
print(f"  score range over {len(all_scores)} bars: "
      f"[{min(all_scores):.1f}, {max(all_scores):.1f}] mean {statistics.mean(all_scores):+.2f}")

# --- A flat, driftless series must not sit pinned at an extreme.
check(
    "score is centred on a symmetric series",
    abs(statistics.mean(all_scores)) < 15.0,
    f"mean {statistics.mean(all_scores):+.2f}",
)


# --- The RSI is a brake, never a trigger: it may only reduce |score|.
# Rebuild the score with the brake disabled and confirm no bar gains from it.
def score_without_brake(bars: list[Bar]) -> list[float | None]:
    return confluence_score(bars, w_rsi=0.0)[0]


gained = 0
for s in sessions[:10]:
    with_brake, _ = confluence_score(s.bars)
    no_brake = score_without_brake(s.bars)
    for a, b in zip(with_brake, no_brake):
        if a is None or b is None:
            continue
        if abs(a) > abs(b) + 1e-9:
            gained += 1
check("RSI only ever brakes", gained == 0, f"{gained} bars where the brake INCREASED |score|")
print(f"  bars where the RSI brake increased the score: {gained} (must be 0)")

# --- The cost gate must actually veto. A quiet series (small ATR) should
#     produce entries with the gate off and far fewer with it on.
quiet = synthetic_sessions(WIN, n_sessions=30, seed=4242, bar_sd_ticks=1.5)
gate_on = sum(
    1 for s in quiet for e in Confluencia(use_cost_gate=True).plan(s.bars, WIN).entries if e
)
gate_off = sum(
    1 for s in quiet for e in Confluencia(use_cost_gate=False).plan(s.bars, WIN).entries if e
)
print(f"  quiet market — entries armed: gate off {gate_off}, gate on {gate_on}")
check("cost gate vetoes a quiet market", gate_on == 0, f"{gate_on} entries survived the gate")
check("gate-off arms entries in the same series", gate_off > 0, "the probe series produced none")

# --- Entries are crosses, not levels: no two consecutive bars may both arm.
consec = 0
for s in sessions:
    ents = Confluencia().plan(s.bars, WIN).entries
    for i in range(1, len(ents)):
        if ents[i] is not None and ents[i - 1] is not None:
            consec += 1
check("entries are threshold crosses", consec == 0, f"{consec} consecutive armed bars")

# --- Long and short must both be reachable; a one-sided indicator is a bug.
sides = [e.side for s in sessions for e in Confluencia().plan(s.bars, WIN).entries if e]
check("longs occur", LONG in sides)
check("shorts occur", SHORT in sides)
print(f"  entries over 40 sessions: {sides.count(LONG)} long, {sides.count(SHORT)} short")

# --- allow_short=False must silence the short side entirely.
long_only = [e.side for s in sessions for e in Confluencia(allow_short=False).plan(s.bars, WIN).entries if e]
check("allow_short=False removes shorts", SHORT not in long_only, "a short survived")

# --- THE ONE THAT MATTERS: on data with no edge, the indicator must not
#     clear the placebo null. If it does, the null is broken, not the indicator.
family = [Confluencia(), Confluencia(threshold=35.0), Confluencia(atr_stop=2.0)]
target_rs: list[float | None] = [2.0, None]
costs = CostModel()
cal = calibrate(family, target_rs, WIN, costs, n_series=10, n_sessions=30, base_seed=660001)

held_out = synthetic_sessions(WIN, n_sessions=30, seed=778899)
best = -float("inf")
for setup in family:
    for tr in target_rs:
        trades = run(held_out, setup, WIN, costs, ExecConfig(target_r=tr))
        per = session_pnl(trades, held_out)
        best = max(best, sum(per) / len(per))
p = cal.p_value(best)
print(f"  placebo p-value for Confluencia on a no-edge series: {p:.3f} (must not be < 0.05)")
check(
    "Confluencia does not beat the placebo null on no-edge data",
    p >= 0.05,
    f"p={p:.4f} — investigate before trusting any real-data result",
)

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("confluencia_test: all checks passed")
