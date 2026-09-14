"""Bar series and trading-session structure.

Day trade is session-bounded: a setup never carries a position overnight, and
indicators that anchor to the session (VWAP) must reset at each open. Bars are
therefore always handled as a list of sessions, never as one flat series.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar. Prices are quoted values; volume is contracts."""

    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def session(self) -> date:
        return self.ts.date()

    @property
    def typical(self) -> float:
        """(H+L+C)/3 — the price VWAP weights by volume."""
        return (self.high + self.low + self.close) / 3.0


@dataclass(frozen=True)
class Session:
    """All bars of one trading day, in chronological order."""

    day: date
    bars: list[Bar]

    def __len__(self) -> int:
        return len(self.bars)


def split_sessions(bars: list[Bar], min_bars: int = 20) -> list[Session]:
    """Group a flat bar series into sessions, dropping stubs.

    Sessions shorter than ``min_bars`` (half-days, data gaps) are discarded:
    they cannot support indicator warmup and would inject noise into the
    trade statistics rather than signal.
    """
    grouped: dict[date, list[Bar]] = {}
    for bar in bars:
        grouped.setdefault(bar.session, []).append(bar)
    sessions = []
    for day in sorted(grouped):
        day_bars = sorted(grouped[day], key=lambda b: b.ts)
        if len(day_bars) >= min_bars:
            sessions.append(Session(day=day, bars=day_bars))
    return sessions


def validate(bars: list[Bar]) -> list[str]:
    """Return a list of data-quality complaints; empty means clean.

    Silent bad data is the classic way a backtest lies, so this is called by
    the runner before any strategy sees the series.
    """
    problems: list[str] = []
    if not bars:
        return ["empty series"]
    for i, b in enumerate(bars):
        if not (b.low <= b.open <= b.high and b.low <= b.close <= b.high):
            problems.append(f"bar {i} @ {b.ts}: OHLC inconsistent")
        if b.high < b.low:
            problems.append(f"bar {i} @ {b.ts}: high < low")
        if b.volume < 0:
            problems.append(f"bar {i} @ {b.ts}: negative volume")
        if i and bars[i - 1].ts >= b.ts:
            problems.append(f"bar {i} @ {b.ts}: timestamps not strictly increasing")
    return problems[:50]
