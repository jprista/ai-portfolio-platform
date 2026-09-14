"""Replay protocols — how a signal set is judged, once it exists.

The engine already replays bar by bar with no lookahead (``engine_test.py``
proves a signal from bar i cannot fill on bar i). What this module adds is the
*evaluation protocol* around that replay, because a single aggregate number
over one stretch of history is the easiest way to be fooled.

Three views, each answering a different way of being wrong:

``stop_sweep``      Is the stop the right size? Sweeps the risk CAP — how tight
                    the stop is allowed to be pulled — and reports realised
                    expectancy against the hit rate the arithmetic demands at
                    that risk. This is the honest answer to "use the smallest
                    stop possible": tightening the stop shrinks the target with
                    it while friction stays fixed, so the hit rate you need
                    climbs. The sweep shows where tightening stops paying.

``walk_forward``    Did it hold across time, or was it one lucky stretch?
                    Splits the sessions into sequential folds and reports each.
                    A strategy positive in one fold of five is not a strategy.

``session_curve``   The equity path, for drawdown and for seeing whether the
                    result rests on a handful of sessions.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bars import Session
from .contracts import Contract, CostModel
from .engine import ExecConfig, Trade, run
from .setups import Setup
from .stats import Stats, session_pnl, summarise


@dataclass
class StopRow:
    param_ticks: int
    n_trades: int
    win_rate: float
    required_win_rate: float
    avg_risk_points: float
    expectancy_cents: float
    total_cents: int
    cost_cents: int
    gross_cents: int

    @property
    def edge_gap(self) -> float:
        """How far the realised hit rate sits above what it has to be."""
        return self.win_rate - self.required_win_rate


def required_win_rate(avg_risk_points: float, cost_points: float, reward_r: float) -> float:
    """Hit rate at which a reward_r:1 trade breaks even after friction.

    p * (reward_r * R) - (1 - p) * R - cost = 0  =>  p = (R + cost) / (R * (1 + reward_r))

    The fair rate for the geometry alone is 1 / (1 + reward_r); the difference
    between the two is what the cost is really charging.
    """
    if avg_risk_points <= 0:
        return 1.0
    return (avg_risk_points + cost_points) / (avg_risk_points * (1.0 + reward_r))


def fair_win_rate(reward_r: float) -> float:
    return 1.0 / (1.0 + reward_r)


def _avg_risk_points(trades: list[Trade], contract: Contract, reward_r: float) -> float:
    """Average risk actually taken, recovered from realised outcomes.

    A stop exit loses exactly R; a target exit wins exactly reward_r * R. Both
    are read back so the figure reflects fills, not intentions.
    """
    vals = []
    for t in trades:
        if t.reason == "stop":
            vals.append(abs(contract.points(t.tick_delta)))
        elif t.reason == "target":
            vals.append(abs(contract.points(t.tick_delta)) / reward_r)
    return sum(vals) / len(vals) if vals else 0.0


def stop_sweep(
    sessions: list[Session],
    make_setup,
    contract: Contract,
    costs: CostModel,
    risk_caps: list[int],
    reward_r: float = 2.5,
    cost_points: float = 11.0,
    contracts: int = 1,
) -> list[StopRow]:
    """Run the same signal across a range of stop tightness caps.

    ``make_setup(cap)`` must return the signal configured so the stop can never
    risk more than ``cap`` ticks — that is the knob "use the smallest stop"
    actually turns.
    """
    rows: list[StopRow] = []
    for cap in risk_caps:
        setup = make_setup(cap)
        trades = run(sessions, setup, contract, costs, ExecConfig(target_r=reward_r, contracts=contracts))
        if not trades:
            rows.append(StopRow(cap, 0, 0.0, 1.0, 0.0, 0.0, 0, 0, 0))
            continue
        nets = [t.net_cents for t in trades]
        wins = sum(1 for x in nets if x > 0)
        avg_risk = _avg_risk_points(trades, contract, reward_r)
        rows.append(
            StopRow(
                param_ticks=cap,
                n_trades=len(trades),
                win_rate=wins / len(trades),
                required_win_rate=required_win_rate(avg_risk, cost_points, reward_r),
                avg_risk_points=avg_risk,
                expectancy_cents=sum(nets) / len(nets),
                total_cents=sum(nets),
                cost_cents=sum(t.cost_cents for t in trades),
                gross_cents=sum(t.gross_cents for t in trades),
            )
        )
    return rows


def walk_forward(
    sessions: list[Session],
    setup: Setup,
    contract: Contract,
    costs: CostModel,
    n_folds: int = 5,
    reward_r: float = 2.5,
    contracts: int = 1,
) -> list[Stats]:
    """Sequential folds, in chronological order. No fold is reordered."""
    if n_folds < 1:
        raise ValueError("n_folds must be positive")
    size = max(1, len(sessions) // n_folds)
    out: list[Stats] = []
    for f in range(n_folds):
        lo = f * size
        hi = len(sessions) if f == n_folds - 1 else (f + 1) * size
        chunk = sessions[lo:hi]
        if not chunk:
            continue
        trades = run(chunk, setup, contract, costs, ExecConfig(target_r=reward_r, contracts=contracts))
        out.append(summarise(f"fold {f + 1}/{n_folds} ({len(chunk)} sessões)", trades, chunk))
    return out


def session_curve(
    sessions: list[Session],
    setup: Setup,
    contract: Contract,
    costs: CostModel,
    reward_r: float = 2.5,
    contracts: int = 1,
) -> tuple[list[int], list[int]]:
    """(per-session P&L, cumulative equity) in centavos."""
    trades = run(sessions, setup, contract, costs, ExecConfig(target_r=reward_r, contracts=contracts))
    per = session_pnl(trades, sessions)
    equity: list[int] = []
    acc = 0
    for x in per:
        acc += x
        equity.append(acc)
    return per, equity
