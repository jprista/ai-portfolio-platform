"""Golden and calibration tests for the statistics layer.

The calibration tests matter more than the arithmetic ones: a Reality Check
that rejects the null on pure noise would silently bless every result the
project produces. Run:  python3 tests/stats_test.py
"""
from __future__ import annotations

import random
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups.bars import Session  # noqa: E402
from b3setups.engine import Trade  # noqa: E402
from b3setups.stats import (  # noqa: E402
    bootstrap_mean_ci,
    deflated_sharpe,
    norm_cdf,
    norm_ppf,
    reality_check,
    session_pnl,
    summarise,
)

FAILURES: list[str] = []


def check(name: str, got, want, tol: float = 1e-9) -> None:
    ok = (got == want) if isinstance(want, (int, str)) else abs(got - want) <= tol
    if not ok:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


# --- Inverse normal against published quantiles
check("ppf(0.975)", norm_ppf(0.975), 1.959963984540054, 1e-7)
check("ppf(0.025)", norm_ppf(0.025), -1.959963984540054, 1e-7)
check("ppf(0.99)", norm_ppf(0.99), 2.3263478740408408, 1e-7)
check("cdf(0)", norm_cdf(0.0), 0.5, 1e-12)
check("cdf(1.96)", norm_cdf(1.959963984540054), 0.975, 1e-9)


# --- summarise arithmetic, fully hand-derived
def mk_trade(day, net: int) -> Trade:
    # gross/cost split is irrelevant to the checks below; keep cost at 0 so
    # net == gross and the expectations stay legible.
    return Trade(
        session=day, side=1, entry_ts=datetime(2026, 3, 2, 9, 5),
        exit_ts=datetime(2026, 3, 2, 9, 10), entry_ticks=0, exit_ticks=net // 100,
        contracts=1, gross_cents=net, cost_cents=0, reason="target",
    )


class FakeSession:
    def __init__(self, day):
        self.day = day


days = ["d1", "d2", "d3", "d4"]
sessions = [FakeSession(d) for d in days]
# d1: +300 and -100 ; d2: +200 ; d3: no trade ; d4: -400
trades = [mk_trade("d1", 300), mk_trade("d1", -100), mk_trade("d2", 200), mk_trade("d4", -400)]

st = summarise("t", trades, sessions)
check("n_trades", st.n_trades, 4)
check("wins", st.wins, 2)
check("losses", st.losses, 2)
check("total", st.total_cents, 0)          # 300 - 100 + 200 - 400 = 0
check("win_rate", st.win_rate, 0.5)
check("expectancy", st.expectancy_cents, 0.0)
check("profit_factor", st.profit_factor, 1.0)   # gross win 500 / gross loss 500
check("avg_win", st.avg_win_cents, 250.0)       # (300 + 200)/2
check("avg_loss", st.avg_loss_cents, -250.0)    # (-100 + -400)/2

# session P&L is zero-filled: d3 had no trade and must still count as an observation
sp = session_pnl(trades, sessions)
check("session pnl len", len(sp), 4)
check("session pnl d1", sp[0], 200)   # 300 - 100
check("session pnl d3", sp[2], 0)
check("session pnl d4", sp[3], -400)

# equity path 200, 400, 400, 0 -> peak 400, trough after peak 0 -> drawdown 400
check("max drawdown", st.max_drawdown_cents, 400)

# --- Bootstrap CI brackets the observed mean of a well-behaved series
rng = random.Random(7)
vals = [rng.gauss(50.0, 10.0) for _ in range(300)]
mean, lo, hi = bootstrap_mean_ci(vals, n_boot=500, seed=1)
if not lo < mean < hi:
    FAILURES.append(f"bootstrap CI does not bracket the mean: {lo} < {mean} < {hi}")
if not (40.0 < mean < 60.0):
    FAILURES.append(f"bootstrap mean implausible: {mean}")

# --- SIZE: on pure noise the family test must mostly NOT reject.
# A broken implementation (e.g. forgetting to recentre) rejects almost always.
rejections = 0
REPS, K, N = 20, 15, 120
for rep in range(REPS):
    r = random.Random(1000 + rep)
    matrix = [[int(r.gauss(0, 500)) for _ in range(K)] for _ in range(N)]
    _, _, p, _ = reality_check(matrix, [f"s{j}" for j in range(K)], n_boot=300, seed=rep)
    if p < 0.05:
        rejections += 1
rate = rejections / REPS
if rate > 0.25:
    FAILURES.append(f"reality check over-rejects on noise: {rejections}/{REPS} = {rate:.2f}")
print(f"  reality-check size on pure noise: {rejections}/{REPS} rejections at 5%")

# --- POWER: a genuinely strong column must be detected.
r = random.Random(99)
matrix = [[int(r.gauss(0, 500)) for _ in range(K - 1)] + [int(r.gauss(400, 500))] for _ in range(N)]
best, _, p, _ = reality_check(matrix, [f"s{j}" for j in range(K)], n_boot=300, seed=5)
check("reality check picks the strong column", best, f"s{K - 1}")
if p > 0.05:
    FAILURES.append(f"reality check missed a real edge: p={p:.3f}")
print(f"  reality-check power on an injected edge: p={p:.4f}")

# --- Deflated Sharpe: more trials must raise the hurdle and lower the probability.
r = random.Random(3)
rets = [r.gauss(30.0, 300.0) for _ in range(250)]
sr1, sr0_1, prob1 = deflated_sharpe(rets, n_trials=1)
sr2, sr0_2, prob2 = deflated_sharpe(rets, n_trials=200)
check("same observed SR", round(sr1, 12), round(sr2, 12))
if not sr0_2 > sr0_1:
    FAILURES.append(f"expected max SR did not rise with trials: {sr0_1} -> {sr0_2}")
if not prob2 < prob1:
    FAILURES.append(f"deflated probability did not fall with trials: {prob1} -> {prob2}")
print(f"  deflated Sharpe: N=1 prob={prob1:.4f}  ->  N=200 prob={prob2:.4f}")

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("stats_test: all golden and calibration checks passed")
