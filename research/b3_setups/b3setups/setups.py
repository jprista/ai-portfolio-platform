"""The setups, written to the rules their authors published.

LOOKAHEAD CONTRACT — the single most important property in this file.
A :class:`Plan` produced for a session exposes two arrays indexed by bar:

  ``entries[i]``  an order derived from information available *at the close of
                  bar i*. The engine may only act on it from bar ``i+1``.
  ``exit_long[i]`` / ``exit_short[i]``  a flag derived from the close of bar i,
                  acted on at that same close. This is legitimate: the decision
                  and the fill use the same observable price.

No function here may read ``bars[j]`` for ``j > i`` when filling slot ``i``.
Every setup is a documented *variant* of a published rule, not the one true
reading of it; variants exist precisely so the multiple-testing correction in
``stats.py`` has the trials it needs to correct for.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import indicators as ind
from .bars import Bar
from .contracts import Contract

LONG = 1
SHORT = -1


@dataclass(frozen=True)
class Entry:
    """A pending order, actionable from the bar after the one that produced it.

    Attributes:
        side: LONG or SHORT.
        trigger: Stop-entry price. ``None`` means enter at the next open.
        stop: Protective stop price.
        valid_bars: How many subsequent bars the trigger stays armed.
    """

    side: int
    trigger: float | None
    stop: float
    valid_bars: int = 3


@dataclass
class Plan:
    entries: list[Entry | None]
    exit_long: list[bool] = field(default_factory=list)
    exit_short: list[bool] = field(default_factory=list)

    @staticmethod
    def blank(n: int) -> "Plan":
        return Plan(entries=[None] * n, exit_long=[False] * n, exit_short=[False] * n)


class Setup:
    """Base class. ``name`` must uniquely identify the parameterised variant."""

    name: str = "setup"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        raise NotImplementedError


def _closes(bars: list[Bar]) -> list[float]:
    return [b.close for b in bars]


# --------------------------------------------------------------------------
# Larry Williams' 9-period EMA family — the most widely taught setups in Brazil
# --------------------------------------------------------------------------


class Setup91(Setup):
    """9.1 — reversal. The EMA9 turns up after falling; buy the break of the
    high of the bar on which it turned, stop at that bar's low.
    """

    def __init__(self, period: int = 9, valid_bars: int = 3, allow_short: bool = True):
        self.period = period
        self.valid_bars = valid_bars
        self.allow_short = allow_short
        self.name = f"9.1(ema{period},v{valid_bars}{',L' if not allow_short else ''})"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        e = ind.ema(_closes(bars), self.period)
        tick = contract.tick_size
        for i in range(2, len(bars)):
            a, b, c = e[i - 2], e[i - 1], e[i]
            if a is None or b is None or c is None:
                continue
            if c > b and b <= a:  # turned up
                p.entries[i] = Entry(LONG, bars[i].high + tick, bars[i].low, self.valid_bars)
            elif self.allow_short and c < b and b >= a:  # turned down
                p.entries[i] = Entry(SHORT, bars[i].low - tick, bars[i].high, self.valid_bars)
        return p


class Setup92(Setup):
    """9.2 — trend continuation. With the EMA9 rising, a bar that dips to touch
    the average is a correction; buy the break of its high, stop at its low.
    """

    def __init__(self, period: int = 9, valid_bars: int = 3, allow_short: bool = True):
        self.period = period
        self.valid_bars = valid_bars
        self.allow_short = allow_short
        self.name = f"9.2(ema{period},v{valid_bars}{',L' if not allow_short else ''})"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        e = ind.ema(_closes(bars), self.period)
        tick = contract.tick_size
        for i in range(1, len(bars)):
            cur, prev = e[i], e[i - 1]
            if cur is None or prev is None:
                continue
            if cur > prev and bars[i].low <= cur:
                p.entries[i] = Entry(LONG, bars[i].high + tick, bars[i].low, self.valid_bars)
            elif self.allow_short and cur < prev and bars[i].high >= cur:
                p.entries[i] = Entry(SHORT, bars[i].low - tick, bars[i].high, self.valid_bars)
        return p


class Setup93(Setup):
    """9.3 — breakout of the correction. With the EMA9 rising, arm a trigger on
    the high of a corrective (down) bar; the stop sits under the correction low.
    """

    def __init__(self, period: int = 9, valid_bars: int = 3, allow_short: bool = True):
        self.period = period
        self.valid_bars = valid_bars
        self.allow_short = allow_short
        self.name = f"9.3(ema{period},v{valid_bars}{',L' if not allow_short else ''})"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        e = ind.ema(_closes(bars), self.period)
        tick = contract.tick_size
        run_low: float | None = None
        run_high: float | None = None
        for i in range(1, len(bars)):
            cur, prev = e[i], e[i - 1]
            if cur is None or prev is None:
                continue
            rising = cur > prev
            down_bar = bars[i].close < bars[i].open
            up_bar = bars[i].close > bars[i].open
            if rising and down_bar:
                run_low = bars[i].low if run_low is None else min(run_low, bars[i].low)
                p.entries[i] = Entry(LONG, bars[i].high + tick, run_low, self.valid_bars)
            else:
                run_low = None
            if self.allow_short and not rising and up_bar:
                run_high = bars[i].high if run_high is None else max(run_high, bars[i].high)
                p.entries[i] = Entry(SHORT, bars[i].low - tick, run_high, self.valid_bars)
            elif rising:
                run_high = None
        return p


# --------------------------------------------------------------------------
# Stormer's IFR2 — mean reversion on a 2-period RSI, filtered by a long average
# --------------------------------------------------------------------------


class IFR2(Setup):
    """Buy extreme short-term oversold while above a long trend average; give
    the position back when the oscillator normalises.

    Stormer's published pairing is an EMA5 exit with an EMA49 trend filter;
    the exit here is the oscillator itself, which is the intraday reading.
    """

    def __init__(
        self,
        entry_thr: float = 25.0,
        exit_thr: float = 75.0,
        trend_period: int = 49,
        rsi_period: int = 2,
        allow_short: bool = True,
    ):
        self.entry_thr = entry_thr
        self.exit_thr = exit_thr
        self.trend_period = trend_period
        self.rsi_period = rsi_period
        self.allow_short = allow_short
        self.name = (
            f"IFR2(in{entry_thr:g},out{exit_thr:g},ema{trend_period}"
            f"{',L' if not allow_short else ''})"
        )

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        closes = _closes(bars)
        r = ind.rsi(closes, self.rsi_period)
        trend = ind.ema(closes, self.trend_period)
        a = ind.atr(bars, 14)
        for i in range(len(bars)):
            rv, tv, av = r[i], trend[i], a[i]
            if rv is None or tv is None or av is None or av <= 0:
                continue
            if rv < self.entry_thr and closes[i] > tv:
                p.entries[i] = Entry(LONG, None, bars[i].close - 2.0 * av, valid_bars=1)
            elif self.allow_short and rv > (100.0 - self.entry_thr) and closes[i] < tv:
                p.entries[i] = Entry(SHORT, None, bars[i].close + 2.0 * av, valid_bars=1)
            p.exit_long[i] = rv > self.exit_thr
            p.exit_short[i] = rv < (100.0 - self.exit_thr)
        return p


# --------------------------------------------------------------------------
# Bollinger band reversion, with the RSI confirmation the sources insist on
# --------------------------------------------------------------------------


class BollingerReversion(Setup):
    """Fade a pierce of the band, but only with the oscillator agreeing.
    The target is the middle band; the stop is an ATR multiple.
    """

    def __init__(
        self,
        period: int = 20,
        mult: float = 2.0,
        rsi_period: int = 14,
        rsi_thr: float = 30.0,
        atr_stop: float = 1.5,
        allow_short: bool = True,
    ):
        self.period = period
        self.mult = mult
        self.rsi_period = rsi_period
        self.rsi_thr = rsi_thr
        self.atr_stop = atr_stop
        self.allow_short = allow_short
        self.name = (
            f"BB({period},{mult:g}sd,rsi{rsi_period}<{rsi_thr:g},stop{atr_stop:g}atr"
            f"{',L' if not allow_short else ''})"
        )

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        closes = _closes(bars)
        low_b, mid_b, up_b = ind.bollinger(closes, self.period, self.mult)
        r = ind.rsi(closes, self.rsi_period)
        a = ind.atr(bars, 14)
        for i in range(len(bars)):
            lb, mb, ub, rv, av = low_b[i], mid_b[i], up_b[i], r[i], a[i]
            if None in (lb, mb, ub, rv, av) or av <= 0:
                continue
            assert lb is not None and mb is not None and ub is not None
            assert rv is not None and av is not None
            if bars[i].low <= lb and rv < self.rsi_thr:
                p.entries[i] = Entry(LONG, None, bars[i].close - self.atr_stop * av, valid_bars=1)
            elif self.allow_short and bars[i].high >= ub and rv > (100.0 - self.rsi_thr):
                p.entries[i] = Entry(SHORT, None, bars[i].close + self.atr_stop * av, valid_bars=1)
            p.exit_long[i] = closes[i] >= mb
            p.exit_short[i] = closes[i] <= mb
        return p


# --------------------------------------------------------------------------
# Didi's agulhada — three simple averages through one real body
# --------------------------------------------------------------------------


class DidiAgulhada(Setup):
    """The three averages (3, 8, 20) pass through a candle's real body; the
    trade is taken when they then fan out in order.

    ``fan_within`` bounds how long after the agulhada the fan still counts —
    without it the rule would fire on an unrelated later move.
    """

    def __init__(self, fast: int = 3, mid: int = 8, slow: int = 20, fan_within: int = 3,
                 allow_short: bool = True):
        self.fast, self.mid, self.slow = fast, mid, slow
        self.fan_within = fan_within
        self.allow_short = allow_short
        self.name = f"Didi({fast},{mid},{slow},fan{fan_within}{',L' if not allow_short else ''})"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        closes = _closes(bars)
        m_f = ind.sma(closes, self.fast)
        m_m = ind.sma(closes, self.mid)
        m_s = ind.sma(closes, self.slow)
        tick = contract.tick_size
        last_needle: int | None = None
        for i in range(len(bars)):
            f, m, s = m_f[i], m_m[i], m_s[i]
            if f is None or m is None or s is None:
                continue
            body_lo = min(bars[i].open, bars[i].close)
            body_hi = max(bars[i].open, bars[i].close)
            if body_lo <= f <= body_hi and body_lo <= m <= body_hi and body_lo <= s <= body_hi:
                last_needle = i
                continue
            if last_needle is None or i - last_needle > self.fan_within:
                continue
            n = bars[last_needle]
            if f > m > s:
                p.entries[i] = Entry(LONG, max(n.high, bars[i].high) + tick, n.low, valid_bars=2)
                last_needle = None
            elif self.allow_short and f < m < s:
                p.entries[i] = Entry(SHORT, min(n.low, bars[i].low) - tick, n.high, valid_bars=2)
                last_needle = None
        return p


# --------------------------------------------------------------------------
# VWAP directional filter — applied as a wrapper, the way traders describe it
# --------------------------------------------------------------------------


class VwapFiltered(Setup):
    """Keep only the longs above session VWAP and the shorts below it.

    This is the "filtro de viés" every source describes, isolated so its
    contribution can be measured rather than assumed.
    """

    def __init__(self, inner: Setup):
        self.inner = inner
        self.name = f"{inner.name}+vwap"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = self.inner.plan(bars, contract)
        v = ind.session_vwap(bars)
        for i, e in enumerate(p.entries):
            if e is None:
                continue
            vv = v[i]
            if vv is None:
                p.entries[i] = None
            elif e.side == LONG and bars[i].close < vv:
                p.entries[i] = None
            elif e.side == SHORT and bars[i].close > vv:
                p.entries[i] = None
        return p
