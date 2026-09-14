"""Placebo calibration — the benchmark a real result actually has to clear.

Two things make "is the best variant's P&L greater than zero?" the wrong
question:

1. **The search.** Picking the best of N variants inflates the winner's
   apparent performance even when none of them has an edge.
2. **The simulator.** At OHLC resolution the order of events inside a bar is
   unknowable. Every convention for resolving it leaves a residual bias
   (see ``ExecConfig.manage_entry_bar``), so a strategy can show a positive
   expectancy on a series that is provably a martingale.

Both are properties of the *procedure*, and both can be measured by running the
identical procedure — same family, same engine, same costs, same volatility —
over series that contain no edge by construction. The distribution of the best
variant's result across those runs is the null this project tests against.

A real result is interesting only if it lands beyond that distribution.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Callable, Sequence

from .contracts import Contract, CostModel
from .data import synthetic_sessions
from .engine import ExecConfig, run
from .setups import Setup
from .stats import session_pnl


@dataclass
class PlaceboResult:
    """Distribution of the best-variant per-session mean over no-edge runs."""

    best_means: list[float]        # centavos per session, one per placebo series
    n_series: int
    n_sessions: int
    family_size: int

    @property
    def median(self) -> float:
        return statistics.median(self.best_means)

    @property
    def mean(self) -> float:
        return statistics.mean(self.best_means)

    def percentile(self, q: float) -> float:
        xs = sorted(self.best_means)
        if not xs:
            return 0.0
        k = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
        return xs[k]

    def p_value(self, observed: float) -> float:
        """Share of no-edge runs whose best variant matched or beat ``observed``."""
        at_least = sum(1 for m in self.best_means if m >= observed)
        return (at_least + 1) / (len(self.best_means) + 1)


def calibrate(
    family: Sequence[Setup],
    target_rs: Sequence[float | None],
    contract: Contract,
    costs: CostModel,
    n_series: int = 30,
    n_sessions: int = 250,
    base_seed: int = 770001,
    contracts: int = 1,
    progress: Callable[[int, int], None] | None = None,
) -> PlaceboResult:
    """Run the whole family over ``n_series`` independent no-edge series."""
    best_means: list[float] = []
    family_size = len(family) * len(target_rs)

    for s_i in range(n_series):
        sessions = synthetic_sessions(
            contract, n_sessions=n_sessions, seed=base_seed + s_i * 7919
        )
        best = -float("inf")
        for setup in family:
            for tr in target_rs:
                cfg = ExecConfig(target_r=tr, contracts=contracts)
                trades = run(sessions, setup, contract, costs, cfg)
                per_session = session_pnl(trades, sessions)
                mean = sum(per_session) / len(per_session)
                if mean > best:
                    best = mean
        best_means.append(best)
        if progress is not None:
            progress(s_i + 1, n_series)

    return PlaceboResult(
        best_means=best_means,
        n_series=n_series,
        n_sessions=n_sessions,
        family_size=family_size,
    )
