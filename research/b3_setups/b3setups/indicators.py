"""Technical indicators, implemented to the definitions the setups assume.

Every function returns a list the same length as its input, with ``None`` for
bars inside the warmup window. Callers must treat ``None`` as "no opinion" —
never as zero. Wilder's smoothing is used for RSI, ATR and ADX because that is
what the platforms these setups were designed on (Profit, MetaTrader) use;
a simple-average RSI would shift every IFR2 signal.

Indicators are analysis, not the money path, so they are plain floats.
"""
from __future__ import annotations

from .bars import Bar

Series = list[float | None]


def sma(values: list[float], period: int) -> Series:
    """Simple moving average."""
    out: Series = [None] * len(values)
    if period <= 0:
        raise ValueError("period must be positive")
    running = 0.0
    for i, v in enumerate(values):
        running += v
        if i >= period:
            running -= values[i - period]
        if i >= period - 1:
            out[i] = running / period
    return out


def ema(values: list[float], period: int) -> Series:
    """Exponential moving average, seeded with the first SMA.

    Seeding on the SMA (rather than the first price) is the platform
    convention; it keeps the early values from being dragged by a single bar.
    """
    out: Series = [None] * len(values)
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return out
    k = 2.0 / (period + 1.0)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = (values[i] - prev) * k + prev
        out[i] = prev
    return out


def rsi(values: list[float], period: int) -> Series:
    """Wilder's Relative Strength Index (IFR).

    Period 2 is the one that matters here: it drives Stormer's IFR2.
    """
    out: Series = [None] * len(values)
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) <= period:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        gains += max(delta, 0.0)
        losses += max(-delta, 0.0)
    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = _rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, len(values)):
        delta = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(delta, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-delta, 0.0)) / period
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def stdev_pop(values: list[float], period: int) -> Series:
    """Rolling population standard deviation — Bollinger's convention."""
    out: Series = [None] * len(values)
    means = sma(values, period)
    for i in range(period - 1, len(values)):
        m = means[i]
        assert m is not None
        window = values[i - period + 1 : i + 1]
        var = sum((v - m) ** 2 for v in window) / period
        out[i] = var**0.5
    return out


def bollinger(
    values: list[float], period: int = 20, mult: float = 2.0
) -> tuple[Series, Series, Series]:
    """Bollinger Bands: (lower, middle, upper)."""
    mid = sma(values, period)
    sd = stdev_pop(values, period)
    lower: Series = [None] * len(values)
    upper: Series = [None] * len(values)
    for i in range(len(values)):
        m, s = mid[i], sd[i]
        if m is not None and s is not None:
            lower[i] = m - mult * s
            upper[i] = m + mult * s
    return lower, mid, upper


def true_range(bars: list[Bar]) -> Series:
    """True Range; undefined on the first bar."""
    out: Series = [None] * len(bars)
    for i in range(1, len(bars)):
        prev_close = bars[i - 1].close
        out[i] = max(
            bars[i].high - bars[i].low,
            abs(bars[i].high - prev_close),
            abs(bars[i].low - prev_close),
        )
    return out


def atr(bars: list[Bar], period: int = 14) -> Series:
    """Average True Range with Wilder smoothing."""
    tr = true_range(bars)
    out: Series = [None] * len(bars)
    vals = [t for t in tr[1:] if t is not None]
    if len(vals) < period:
        return out
    prev = sum(vals[:period]) / period
    out[period] = prev
    for i in range(period + 1, len(bars)):
        t = tr[i]
        if t is None:
            continue
        prev = (prev * (period - 1) + t) / period
        out[i] = prev
    return out


def session_vwap(bars: list[Bar]) -> Series:
    """Volume-weighted average price, anchored to the start of the series.

    Call this per session: VWAP that does not reset at the open is a
    different (and, for day trade, meaningless) indicator.

    Falls back to a running average of typical price when the feed carries no
    volume, so an export without a volume column degrades rather than divides
    by zero — the report flags when this happened.
    """
    out: Series = [None] * len(bars)
    cum_pv = 0.0
    cum_v = 0.0
    cum_p = 0.0
    for i, b in enumerate(bars):
        cum_pv += b.typical * b.volume
        cum_v += b.volume
        cum_p += b.typical
        out[i] = (cum_pv / cum_v) if cum_v > 0 else (cum_p / (i + 1))
    return out


def adx(bars: list[Bar], period: int = 14) -> tuple[Series, Series, Series]:
    """Wilder's ADX with directional indicators: (di_plus, di_minus, adx).

    This is the indicator Pam Semezzato singles out; it measures trend
    *strength*, not direction.
    """
    n = len(bars)
    di_plus: Series = [None] * n
    di_minus: Series = [None] * n
    adx_out: Series = [None] * n
    if n <= period * 2:
        return di_plus, di_minus, adx_out

    plus_dm: list[float] = [0.0] * n
    minus_dm: list[float] = [0.0] * n
    tr = true_range(bars)
    for i in range(1, n):
        up = bars[i].high - bars[i - 1].high
        down = bars[i - 1].low - bars[i].low
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0

    tr_s = sum(t for t in tr[1 : period + 1] if t is not None)
    p_s = sum(plus_dm[1 : period + 1])
    m_s = sum(minus_dm[1 : period + 1])

    dx_values: list[tuple[int, float]] = []
    for i in range(period, n):
        if i > period:
            t = tr[i] or 0.0
            tr_s = tr_s - (tr_s / period) + t
            p_s = p_s - (p_s / period) + plus_dm[i]
            m_s = m_s - (m_s / period) + minus_dm[i]
        if tr_s <= 0:
            continue
        pdi = 100.0 * p_s / tr_s
        mdi = 100.0 * m_s / tr_s
        di_plus[i] = pdi
        di_minus[i] = mdi
        denom = pdi + mdi
        if denom > 0:
            dx_values.append((i, 100.0 * abs(pdi - mdi) / denom))

    if len(dx_values) >= period:
        prev = sum(d for _, d in dx_values[:period]) / period
        adx_out[dx_values[period - 1][0]] = prev
        for idx, d in dx_values[period:]:
            prev = (prev * (period - 1) + d) / period
            adx_out[idx] = prev
    return di_plus, di_minus, adx_out
