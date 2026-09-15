"""Bar-by-bar intraday execution.

Design decisions that determine whether the numbers mean anything:

* **Session-bounded.** Every position is closed at the last bar of its session.
  This is day trade; there is no overnight carry and no overnight gap risk to
  flatter the results.
* **Conservative intrabar ordering.** When a bar's range contains both the stop
  and the target, the stop is assumed to have been hit first. Intrabar order is
  unknowable from OHLC, and the optimistic assumption is the classic way a
  backtest invents an edge it does not have.
* **Gaps fill at the open.** A stop-entry or protective stop that the bar opens
  beyond fills at the open, not at the untouched trigger price.
* **Costs are money, not price.** Fills use clean prices; brokerage, exchange
  fees and slippage are applied once per round trip in integer centavos.
* **Degenerate geometry is refused.** A signal whose stop sits at or beyond the
  entry has no definable risk and is skipped rather than silently given a
  zero-risk target.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .bars import Bar, Session
from .contracts import Contract, CostModel
from .setups import LONG, SHORT, Entry, Plan, Setup


@dataclass(frozen=True)
class Trade:
    session: object
    side: int
    entry_ts: datetime
    exit_ts: datetime
    entry_ticks: int
    exit_ticks: int
    contracts: int
    gross_cents: int
    cost_cents: int
    reason: str

    @property
    def net_cents(self) -> int:
        return self.gross_cents - self.cost_cents

    @property
    def tick_delta(self) -> int:
        return (self.exit_ticks - self.entry_ticks) * self.side


@dataclass
class ExecConfig:
    """Execution parameters swept by the runner."""

    target_r: float | None = 2.0
    contracts: int = 1
    no_entry_last_frac: float = 0.10
    max_risk_ticks: int | None = None
    manage_entry_bar: bool = True
    """Whether stop and target are evaluated on the bar the entry filled on.

    OHLC does not say whether the bar's low came before or after the entry
    trigger. Evaluating the stop against the whole bar therefore sends
    small-risk trades disproportionately into the loss bucket, which leaves
    the surviving winners with a larger average risk than the losers and
    manufactures a positive expectancy on a series with no edge at all
    (measured at about +1.4 ticks/trade on a pure breakout).

    Skipping the entry bar is worse, not better: it removes the trade's ability
    to lose on the bar it opened on, and the same measurement rises to about
    +4.7 ticks/trade. True is therefore the default as the least biased of the
    available conventions. The residual is a property of OHLC resolution, not a
    defect that can be coded away, which is why the placebo calibration in
    ``placebo.py`` — not zero — is the benchmark a real result must clear.
    """


def _fill_stop_entry(bar: Bar, side: int, trigger: float) -> float | None:
    """Price at which a stop-entry order would fill on this bar, if at all."""
    if side == LONG:
        if bar.high < trigger:
            return None
        return max(trigger, bar.open)
    if bar.low > trigger:
        return None
    return min(trigger, bar.open)


def _fill_protective(bar: Bar, side: int, stop: float) -> float | None:
    """Price at which a protective stop would fill on this bar, if at all."""
    if side == LONG:
        if bar.low > stop:
            return None
        return min(stop, bar.open)
    if bar.high < stop:
        return None
    return max(stop, bar.open)


def _hits_target(bar: Bar, side: int, target: float) -> bool:
    return bar.high >= target if side == LONG else bar.low <= target


def run_session(
    session: Session,
    setup: Setup,
    contract: Contract,
    costs: CostModel,
    cfg: ExecConfig,
    history: list[Bar] | None = None,
) -> list[Trade]:
    """Replay one session. ``history`` is the preceding bars, for warm-up only.

    A real chart is continuous: an EMA50 on a 15-minute chart is warm at
    Monday's open because it carries Friday with it. Scoring each session from
    a cold start would make every higher timeframe look untradeable for the
    first fifty bars — an artefact of the harness, not of the indicator. The
    setup therefore sees history plus the session, and only the session's own
    slice of the resulting plan is ever acted on. Session-anchored indicators
    stay correct because ``session_vwap`` resets on the date, exactly as the
    NTSL version does.
    """
    bars = session.bars
    n = len(bars)
    warm = list(history) if history else []
    full = warm + bars
    offset = len(warm)
    plan_full: Plan = setup.plan(full, contract)
    plan = Plan(
        entries=plan_full.entries[offset:],
        exit_long=plan_full.exit_long[offset:],
        exit_short=plan_full.exit_short[offset:],
    )
    cutoff = max(1, int(n * (1.0 - cfg.no_entry_last_frac)))

    trades: list[Trade] = []
    pending: tuple[Entry, int] | None = None  # (entry, expires_at_index)

    side = 0
    entry_price = 0.0
    entry_ticks = 0
    entry_ts: datetime | None = None
    stop_price = 0.0
    target_price: float | None = None

    def close_position(i: int, price: float, reason: str) -> None:
        nonlocal side, entry_ts
        assert entry_ts is not None
        exit_ticks = contract.to_ticks(price)
        delta = (exit_ticks - entry_ticks) * side
        gross = delta * contract.tick_cents * cfg.contracts
        cost = costs.total_round_trip_cents(contract, cfg.contracts)
        trades.append(
            Trade(
                session=session.day,
                side=side,
                entry_ts=entry_ts,
                exit_ts=bars[i].ts,
                entry_ticks=entry_ticks,
                exit_ticks=exit_ticks,
                contracts=cfg.contracts,
                gross_cents=gross,
                cost_cents=cost,
                reason=reason,
            )
        )
        side = 0
        entry_ts = None

    for i in range(n):
        bar = bars[i]
        last_bar = i == n - 1
        closed_this_bar = False

        # 1. Manage an open position before anything else.
        if side != 0:
            stop_fill = _fill_protective(bar, side, stop_price)
            target_hit = target_price is not None and _hits_target(bar, side, target_price)
            if stop_fill is not None:
                close_position(i, stop_fill, "stop")
                closed_this_bar = True
            elif target_hit:
                assert target_price is not None
                close_position(i, target_price, "target")
                closed_this_bar = True
            elif (side == LONG and plan.exit_long[i]) or (side == SHORT and plan.exit_short[i]):
                close_position(i, bar.close, "signal")
                closed_this_bar = True
            elif last_bar:
                close_position(i, bar.close, "session_close")
                closed_this_bar = True

        # 2. Try to fill a pending entry (never on the bar that produced it).
        # A position closed on this bar consumes it: re-entering here would
        # reuse the same intrabar excursion that produced the exit, letting one
        # high satisfy two sequential targets. That inflates the win rate on a
        # series with no edge at all, so the next entry waits for a fresh bar.
        if side == 0 and not closed_this_bar and pending is not None and i <= cutoff:
            entry, expires = pending
            if i > expires:
                pending = None
            else:
                fill: float | None
                if entry.trigger is None:
                    fill = bar.open
                else:
                    fill = _fill_stop_entry(bar, entry.side, entry.trigger)
                if fill is not None:
                    risk = (fill - entry.stop) if entry.side == LONG else (entry.stop - fill)
                    risk_ticks = round(risk / contract.tick_size)
                    too_big = (
                        cfg.max_risk_ticks is not None and risk_ticks > cfg.max_risk_ticks
                    )
                    if risk_ticks > 0 and not too_big:
                        side = entry.side
                        entry_price = fill
                        entry_ticks = contract.to_ticks(fill)
                        entry_ts = bar.ts
                        stop_price = entry.stop
                        target_price = (
                            None
                            if cfg.target_r is None
                            else (
                                entry_price + cfg.target_r * risk
                                if side == LONG
                                else entry_price - cfg.target_r * risk
                            )
                        )
                        pending = None
                        if cfg.manage_entry_bar:
                            stop_fill = _fill_protective(bar, side, stop_price)
                            if stop_fill is not None:
                                close_position(i, stop_fill, "stop")
                            elif target_price is not None and _hits_target(
                                bar, side, target_price
                            ):
                                close_position(i, target_price, "target")
                            elif last_bar:
                                close_position(i, bar.close, "session_close")
                        elif last_bar:
                            # Nothing may be carried past the session.
                            close_position(i, bar.close, "session_close")
                    else:
                        pending = None

        # 3. Register this bar's signal for the NEXT bar. Never acted on now.
        if i < cutoff and plan.entries[i] is not None:
            e = plan.entries[i]
            assert e is not None
            pending = (e, i + e.valid_bars)

    return trades


def run(
    sessions: list[Session],
    setup: Setup,
    contract: Contract,
    costs: CostModel,
    cfg: ExecConfig,
    warmup_bars: int = 200,
) -> list[Trade]:
    """Replay every session in order, carrying warm-up history forward.

    ``warmup_bars`` caps how much history a setup sees, so cost stays linear in
    the number of sessions instead of quadratic.
    """
    out: list[Trade] = []
    history: list[Bar] = []
    for s in sessions:
        out.extend(run_session(s, setup, contract, costs, cfg, history=history[-warmup_bars:]))
        history.extend(s.bars)
    return out
