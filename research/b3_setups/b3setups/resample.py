"""Changing the chart's axis: time aggregation and Renko bricks.

Both exist here for one reason — to answer "which chart does this indicator
run on" by measuring instead of asserting. The two transforms are not
interchangeable: time bars keep the clock and let volume and volatility vary
bar to bar, while Renko throws the clock away and fixes the bar's height by
construction. Any indicator that reads volatility or volume per bar is
therefore reading something different on each.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .bars import Bar, Session


def resample(bars: list[Bar], minutes: int) -> list[Bar]:
    """Aggregate a bar series onto a coarser time grid.

    Buckets are anchored to the session's own first bar rather than to the
    wall clock, so a pregão opening at 09:05 does not lose its first bars to a
    partial bucket.
    """
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    if not bars:
        return []

    out: list[Bar] = []
    bucket: list[Bar] = []
    anchor: datetime | None = None
    current_day = None

    def flush() -> None:
        if not bucket:
            return
        out.append(
            Bar(
                ts=bucket[0].ts,
                open=bucket[0].open,
                high=max(b.high for b in bucket),
                low=min(b.low for b in bucket),
                close=bucket[-1].close,
                volume=sum(b.volume for b in bucket),
            )
        )
        bucket.clear()

    for b in bars:
        if b.session != current_day:
            flush()
            current_day = b.session
            anchor = b.ts
        assert anchor is not None
        if bucket and (b.ts - anchor) >= timedelta(minutes=minutes):
            flush()
            anchor = b.ts
        bucket.append(b)
    flush()
    return out


def to_renko(bars: list[Bar], brick_points: float) -> list[Bar]:
    """Convert to Renko bricks of fixed height, session by session.

    Bricks carry an OHLC shaped like a candle so the rest of the code can read
    them, but be clear about what that means: **open and close are exactly one
    brick apart, and high and low equal them.** Every bar has the same height
    by construction. That is the whole point of Renko, and it is also why any
    indicator reading per-bar range — ATR above all — stops measuring anything
    on this chart.

    Volume accumulated since the previous brick is attributed to the brick that
    closes, so a brick that took an hour to form and one that took ten seconds
    carry wildly different volume with no way to tell them apart.
    """
    if brick_points <= 0:
        raise ValueError("brick_points must be positive")
    out: list[Bar] = []
    current_day = None
    anchor = 0.0
    pending_volume = 0.0

    for b in bars:
        if b.session != current_day:
            current_day = b.session
            anchor = b.close
            pending_volume = 0.0
        pending_volume += b.volume

        while b.close >= anchor + brick_points:
            top = anchor + brick_points
            out.append(Bar(ts=b.ts, open=anchor, high=top, low=anchor,
                           close=top, volume=pending_volume))
            anchor = top
            pending_volume = 0.0
        while b.close <= anchor - brick_points:
            bottom = anchor - brick_points
            out.append(Bar(ts=b.ts, open=anchor, high=anchor, low=bottom,
                           close=bottom, volume=pending_volume))
            anchor = bottom
            pending_volume = 0.0
    return out


def sessions_from(bars: list[Bar], min_bars: int = 20) -> list[Session]:
    """Group transformed bars back into sessions.

    Renko timestamps repeat (several bricks can close on one source bar), so
    the strict-increase rule that ``bars.validate`` applies to time series does
    not hold here; grouping only needs the date.
    """
    grouped: dict[object, list[Bar]] = {}
    for b in bars:
        grouped.setdefault(b.session, []).append(b)
    return [
        Session(day=day, bars=grouped[day])
        for day in sorted(grouped)
        if len(grouped[day]) >= min_bars
    ]
