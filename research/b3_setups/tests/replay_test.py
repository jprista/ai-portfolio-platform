"""Tests for the replay protocols and the trade geometry.

The arithmetic here is the part of the project that does NOT depend on data,
so it is pinned with hand-derived literals. Run:  python3 tests/replay_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups.contracts import WIN, CostModel  # noqa: E402
from b3setups.data import synthetic_sessions  # noqa: E402
from b3setups.engine import ExecConfig, run  # noqa: E402
from b3setups.replay import (  # noqa: E402
    fair_win_rate,
    required_win_rate,
    session_curve,
    stop_sweep,
    walk_forward,
)
from b3setups.setups import ConfluenciaSinal  # noqa: E402

FAILURES: list[str] = []


def check(name: str, got, want, tol: float = 1e-9) -> None:
    ok = (got == want) if isinstance(want, int) else abs(got - want) <= tol
    if not ok:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


# --- Break-even hit rate. p = (R + custo) / (R * (1 + alvo)).
# R=100, custo=11, alvo=2.5 -> 111 / 350 = 0.31714285714...
check("required R=100", required_win_rate(100, 11, 2.5), 111.0 / 350.0)
# R=20 -> 31 / 70 = 0.442857...
check("required R=20", required_win_rate(20, 11, 2.5), 31.0 / 70.0)
# R=10 -> 21 / 35 = 0.6
check("required R=10", required_win_rate(10, 11, 2.5), 0.6)
# Zero cost must collapse onto the pure geometry: 1 / 3.5
check("required with no cost", required_win_rate(100, 0, 2.5), 1.0 / 3.5)
check("fair 2.5R", fair_win_rate(2.5), 1.0 / 3.5)
check("fair 1R", fair_win_rate(1.0), 0.5)
# Degenerate risk must not divide by zero.
check("required at zero risk", required_win_rate(0, 11, 2.5), 1.0)

# --- Tightening the stop must RAISE the required hit rate, always.
prev = 0.0
for r_points in (400, 200, 100, 50, 25, 12):
    cur = required_win_rate(r_points, 11, 2.5)
    if cur <= prev:
        FAILURES.append(f"required rate not monotone as the stop tightens at R={r_points}")
    prev = cur
print(f"  R=250pts exige {required_win_rate(250, 11, 2.5):.1%}  ->  "
      f"R=25pts exige {required_win_rate(25, 11, 2.5):.1%}  (geometria: {fair_win_rate(2.5):.1%})")

sessions = synthetic_sessions(WIN, n_sessions=40, seed=515151)
costs = CostModel()


def make(cap: int) -> ConfluenciaSinal:
    return ConfluenciaSinal(min_risk_ticks=2, max_risk_ticks=cap, reward_r=2.5)


# --- The cap must actually bind: a tighter cap means a smaller realised risk.
rows = stop_sweep(sessions, make, WIN, costs, [6, 12, 24, 48], reward_r=2.5, cost_points=11.0)
risks = [r.avg_risk_points for r in rows if r.n_trades > 0]
if len(risks) < 4:
    FAILURES.append("stop_sweep produced empty rows on a series that should trade")
elif not all(risks[i] < risks[i + 1] for i in range(len(risks) - 1)):
    FAILURES.append(f"the risk cap does not bind: realised risks {risks}")
print(f"  risco médio realizado por teto {[r.param_ticks for r in rows]}: "
      f"{[round(x) for x in risks]} pontos")

# --- Realised reward must be 2.5x the realised risk on target exits, because
#     the engine derives the target from the fill, not from the intention.
trades = run(sessions, make(12), WIN, costs, ExecConfig(target_r=2.5))
tg = [t for t in trades if t.reason == "target"]
st = [t for t in trades if t.reason == "stop"]
if tg and st:
    avg_win = sum(WIN.points(t.tick_delta) for t in tg) / len(tg)
    avg_loss = -sum(WIN.points(t.tick_delta) for t in st) / len(st)
    ratio = avg_win / avg_loss
    print(f"  ganho médio {avg_win:.0f} pts / perda média {avg_loss:.0f} pts = {ratio:.2f}R")
    if not 2.2 <= ratio <= 2.8:
        FAILURES.append(f"realised reward/risk is {ratio:.2f}, expected about 2.5")
else:
    FAILURES.append("no target/stop exits to verify the reward ratio")

# --- Walk-forward partitions by session, so no trade may be lost or doubled.
folds = walk_forward(sessions, make(12), WIN, costs, n_folds=4, reward_r=2.5)
check("folds returned", len(folds), 4)
check("walk-forward conserves trades", sum(f.n_trades for f in folds), len(trades))
check("walk-forward conserves sessions", sum(f.n_sessions for f in folds), len(sessions))

# --- The equity curve must be the running sum of the per-session P&L.
per, equity = session_curve(sessions, make(12), WIN, costs, reward_r=2.5)
check("curve length", len(equity), len(sessions))
acc = 0
bad = 0
for i, x in enumerate(per):
    acc += x
    if equity[i] != acc:
        bad += 1
check("equity is the running sum", bad, 0)
check("final equity equals total", equity[-1], sum(per))

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("replay_test: all checks passed")
