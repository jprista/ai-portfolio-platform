"""Trade statistics and the multiple-testing machinery.

The reason this module exists: running many setup variants over one price
series and reporting the best one is exactly the procedure that produces
impressive backtests with no out-of-sample value. Two corrections are applied.

* **White's Reality Check** (Bootstrap Reality Check, White 2000). The null is
  that *no* strategy in the tested family has positive expected P&L. The test
  statistic is the maximum across strategies, and its null distribution is
  obtained by a stationary block bootstrap of the aligned per-session P&L
  matrix, recentred so each strategy has zero mean. The resulting p-value is
  for the family, not for a strategy picked after the fact.

* **Deflated Sharpe Ratio** (Bailey & Lopez de Prado 2014). Adjusts an observed
  Sharpe for the number of trials, the length of the series, and the skew and
  kurtosis of returns — a Sharpe that looks good at N=1 may be unremarkable as
  the best of N=200.

Block bootstrap rather than i.i.d. resampling because intraday P&L is
autocorrelated across sessions: a regime that suits a trend setup lasts days.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .contracts import cents_to_brl
from .engine import Trade

EULER_GAMMA = 0.5772156649015329


# --------------------------------------------------------------------------
# Normal distribution helpers (stdlib only)
# --------------------------------------------------------------------------


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """Inverse normal CDF — Acklam's rational approximation, |err| < 1.15e-9."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    p_low, p_high = 0.02425, 1.0 - 0.02425
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    if p > p_high:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
        ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
    )


# --------------------------------------------------------------------------
# Per-strategy statistics
# --------------------------------------------------------------------------


@dataclass
class Stats:
    name: str
    n_trades: int
    n_sessions: int
    wins: int
    losses: int
    total_cents: int
    gross_cents: int
    cost_cents: int
    expectancy_cents: float
    win_rate: float
    profit_factor: float
    max_drawdown_cents: int
    sharpe_sessions: float
    avg_win_cents: float
    avg_loss_cents: float

    @property
    def total_brl(self):
        return cents_to_brl(self.total_cents)

    @property
    def cost_drag_pct(self) -> float:
        """Costs as a share of gross profit, when gross is positive."""
        return 100.0 * self.cost_cents / self.gross_cents if self.gross_cents > 0 else float("nan")


def session_pnl(trades: list[Trade], sessions: list) -> list[int]:
    """Per-session net P&L in centavos, zero-filled over every session.

    Zero-filling matters: a setup that trades on 5 of 200 sessions must not be
    scored as if it had 5 observations. The bootstrap needs a common index.
    """
    by_day: dict[object, int] = {}
    for t in trades:
        by_day[t.session] = by_day.get(t.session, 0) + t.net_cents
    return [by_day.get(s.day, 0) for s in sessions]


def summarise(name: str, trades: list[Trade], sessions: list) -> Stats:
    nets = [t.net_cents for t in trades]
    wins = [x for x in nets if x > 0]
    losses = [x for x in nets if x < 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    per_session = session_pnl(trades, sessions)

    equity = 0
    peak = 0
    max_dd = 0
    for x in per_session:
        equity += x
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    mean_s = sum(per_session) / len(per_session) if per_session else 0.0
    sd_s = _stdev(per_session)
    sharpe = (mean_s / sd_s * math.sqrt(252.0)) if sd_s > 0 else 0.0

    return Stats(
        name=name,
        n_trades=len(trades),
        n_sessions=len(sessions),
        wins=len(wins),
        losses=len(losses),
        total_cents=sum(nets),
        gross_cents=sum(t.gross_cents for t in trades),
        cost_cents=sum(t.cost_cents for t in trades),
        expectancy_cents=(sum(nets) / len(nets)) if nets else 0.0,
        win_rate=(len(wins) / len(nets)) if nets else 0.0,
        profit_factor=(gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        max_drawdown_cents=max_dd,
        sharpe_sessions=sharpe,
        avg_win_cents=(sum(wins) / len(wins)) if wins else 0.0,
        avg_loss_cents=(sum(losses) / len(losses)) if losses else 0.0,
    )


def _stdev(xs: list[int] | list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5


def _skew_kurt(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    if n < 4:
        return 0.0, 3.0
    m = sum(xs) / n
    sd = _stdev(xs)
    if sd == 0:
        return 0.0, 3.0
    s = sum(((x - m) / sd) ** 3 for x in xs) / n
    k = sum(((x - m) / sd) ** 4 for x in xs) / n
    return s, k


# --------------------------------------------------------------------------
# Stationary block bootstrap
# --------------------------------------------------------------------------


def _block_indices(n: int, mean_block: float, rng: random.Random) -> list[int]:
    """Politis & Romano stationary bootstrap index sequence."""
    p = 1.0 / mean_block
    idx: list[int] = []
    cur = rng.randrange(n)
    while len(idx) < n:
        idx.append(cur)
        if rng.random() < p:
            cur = rng.randrange(n)
        else:
            cur = (cur + 1) % n
    return idx


def bootstrap_mean_ci(
    values: list[int] | list[float],
    n_boot: int = 2000,
    mean_block: float = 5.0,
    alpha: float = 0.05,
    seed: int = 12345,
) -> tuple[float, float, float]:
    """(mean, lower, upper) percentile CI from a stationary block bootstrap."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    observed = sum(values) / n
    means = []
    for _ in range(n_boot):
        idx = _block_indices(n, mean_block, rng)
        means.append(sum(values[i] for i in idx) / n)
    means.sort()
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return observed, lo, hi


def reality_check(
    matrix: list[list[int]],
    names: list[str],
    n_boot: int = 2000,
    mean_block: float = 5.0,
    seed: int = 12345,
) -> tuple[str, float, float, list[float]]:
    """White's Reality Check over a sessions x strategies P&L matrix.

    Args:
        matrix: ``matrix[s][k]`` is strategy k's net P&L on session s, centavos.
        names: strategy names, aligned with the columns.

    Returns:
        (best_name, best_statistic, family_p_value, per_strategy_means)
    """
    n_sessions = len(matrix)
    k = len(names)
    if n_sessions == 0 or k == 0:
        return "", 0.0, 1.0, []

    # Column-major once: the bootstrap inner loop is the hot path, and
    # sum(map(col.__getitem__, idx)) is several times faster than indexing
    # the row-major matrix per element.
    columns = [[matrix[s][j] for s in range(n_sessions)] for j in range(k)]
    means = [sum(col) / n_sessions for col in columns]
    root_n = math.sqrt(n_sessions)
    v = [root_n * m for m in means]
    best_j = max(range(k), key=lambda j: v[j])
    v_max = v[best_j]

    rng = random.Random(seed)
    exceed = 0
    for _ in range(n_boot):
        idx = _block_indices(n_sessions, mean_block, rng)
        for j in range(k):
            bm = sum(map(columns[j].__getitem__, idx)) / n_sessions
            if root_n * (bm - means[j]) >= v_max:  # recentred: null of no edge
                exceed += 1
                break
    p_value = (exceed + 1) / (n_boot + 1)
    return names[best_j], v_max, p_value, means


def deflated_sharpe(
    returns: list[int] | list[float], n_trials: int, benchmark_sr: float = 0.0
) -> tuple[float, float, float]:
    """(observed SR, expected max SR under the null, deflated SR probability).

    SR here is per-session (not annualised); ``n_trials`` is the size of the
    family searched. The returned probability is P(true SR > benchmark).
    """
    xs = [float(x) for x in returns]
    n = len(xs)
    if n < 4:
        return 0.0, 0.0, 0.5
    sd = _stdev(xs)
    if sd == 0:
        return 0.0, 0.0, 0.5
    sr = (sum(xs) / n) / sd
    skew, kurt = _skew_kurt(xs)

    if n_trials > 1:
        z1 = norm_ppf(1.0 - 1.0 / n_trials)
        z2 = norm_ppf(1.0 - 1.0 / (n_trials * math.e))
        sr0 = benchmark_sr + ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)
        # Expected max of n_trials independent SR estimates, scaled by their sd.
        sr0 = sr0 / math.sqrt(n - 1)
    else:
        sr0 = benchmark_sr

    denom = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr
    if denom <= 0:
        return sr, sr0, 0.5
    z = (sr - sr0) * math.sqrt(n - 1) / math.sqrt(denom)
    return sr, sr0, norm_cdf(z)


@dataclass
class PositionStats:
    """Outcomes counted per POSITION, not per fill.

    Scaling out splits one decision into several rows, and a partial booked at
    1R is nearly always green. Counting rows would therefore report a hit rate
    that rises with the number of partials and says nothing about whether the
    decisions were good. Everything below groups the legs back together first.

    ``flat`` exists because a breakeven stop creates a third outcome that is
    neither a win nor a loss, and folding it into either one misreports what
    the technique actually does.
    """

    name: str
    n_positions: int
    wins: int
    flats: int
    losses: int
    total_cents: int
    expectancy_cents: float
    avg_win_cents: float
    avg_loss_cents: float
    cost_cents: int

    @property
    def win_rate(self) -> float:
        return self.wins / self.n_positions if self.n_positions else 0.0

    @property
    def green_rate(self) -> float:
        """Share of positions that did not end red — what a trader feels."""
        decided = self.n_positions
        return (self.wins + self.flats) / decided if decided else 0.0

    @property
    def payoff(self) -> float:
        return abs(self.avg_win_cents / self.avg_loss_cents) if self.avg_loss_cents else float("inf")


def by_position(trades: list[Trade], flat_band_cents: int = 0) -> list[int]:
    """Net result of each position, in centavos, legs recombined."""
    groups: dict[tuple, int] = {}
    order: list[tuple] = []
    for t in trades:
        key = (t.session, t.position_id)
        if key not in groups:
            groups[key] = 0
            order.append(key)
        groups[key] += t.net_cents
    return [groups[k] for k in order]


def summarise_positions(name: str, trades: list[Trade], flat_band_cents: int = 300) -> PositionStats:
    """Group legs into positions and classify each as win, flat or loss.

    ``flat_band_cents`` is the width around zero that counts as a scratch; a
    breakeven exit never lands exactly on zero once costs are charged.
    """
    nets = by_position(trades)
    wins = [x for x in nets if x > flat_band_cents]
    losses = [x for x in nets if x < -flat_band_cents]
    flats = [x for x in nets if -flat_band_cents <= x <= flat_band_cents]
    return PositionStats(
        name=name,
        n_positions=len(nets),
        wins=len(wins),
        flats=len(flats),
        losses=len(losses),
        total_cents=sum(nets),
        expectancy_cents=(sum(nets) / len(nets)) if nets else 0.0,
        avg_win_cents=(sum(wins) / len(wins)) if wins else 0.0,
        avg_loss_cents=(sum(losses) / len(losses)) if losses else 0.0,
        cost_cents=sum(t.cost_cents for t in trades),
    )
