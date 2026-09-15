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


# --------------------------------------------------------------------------
# Confluencia B3 — the Python twin of profit/ConfluenciaB3.ntsl
# --------------------------------------------------------------------------


def confluence_score(
    bars: list[Bar],
    fast: int = 9,
    mid: int = 21,
    slow: int = 50,
    di_period: int = 14,
    adx_period: int = 14,
    adx_min: float = 20.0,
    adx_full: float = 40.0,
    rsi_period: int = 14,
    rsi_high: float = 70.0,
    rsi_low: float = 30.0,
    vol_period: int = 20,
    atr_period: int = 14,
    w_trend: float = 30.0,
    w_vwap: float = 25.0,
    w_force: float = 20.0,
    w_rsi: float = 15.0,
    w_volume: float = 10.0,
    return_components: bool = False,
) -> tuple:
    """Score in [-100, +100] plus the ATR series, mirroring the NTSL indicator.

    Five complementary layers, weighted as they appear in the sources — trend,
    day bias, strength, exhaustion, participation. The RSI is deliberately a
    brake, never a trigger: it only deducts from a score that is already
    stretched in its own direction.

    Kept byte-for-byte equivalent in behaviour to the NTSL version so the
    indicator a trader watches and the rules a backtest scores are the same
    thing. If one changes, change both.

    With ``return_components`` a third list is returned carrying each bar's
    per-layer contribution, so an explanation of the score is derived from the
    same arithmetic that produces it rather than restated alongside it.
    """
    n = len(bars)
    closes = _closes(bars)
    volumes = [b.volume for b in bars]

    e_fast = ind.ema(closes, fast)
    e_mid = ind.ema(closes, mid)
    e_slow = ind.ema(closes, slow)
    vwap = ind.session_vwap(bars)
    a = ind.atr(bars, atr_period)
    r = ind.rsi(closes, rsi_period)
    v_avg = ind.sma(volumes, vol_period)
    di_p, di_m, adx_v = ind.adx(bars, di_period)

    scores: list[float | None] = [None] * n
    parts: list[dict[str, float] | None] = [None] * n
    for i in range(1, n):
        ef, em, es = e_fast[i], e_mid[i], e_slow[i]
        av, rv, vm = a[i], r[i], v_avg[i]
        vw = vwap[i]
        if None in (ef, em, es, av, rv, vm, vw) or ef is None or e_fast[i - 1] is None:
            continue
        assert ef is not None and em is not None and es is not None
        assert av is not None and rv is not None and vm is not None and vw is not None
        prev_fast = e_fast[i - 1]
        assert prev_fast is not None

        # 1. Trend: three horizons agreeing, plus the fast average's slope.
        s_trend = 0.0
        if ef > em:
            s_trend += 0.4
        elif ef < em:
            s_trend -= 0.4
        if em > es:
            s_trend += 0.3
        elif em < es:
            s_trend -= 0.3
        if ef > prev_fast:
            s_trend += 0.3
        elif ef < prev_fast:
            s_trend -= 0.3

        # 2. Day bias: distance to VWAP measured in ATR, clipped.
        s_vwap = ((closes[i] - vw) / av) if av > 0 else 0.0
        s_vwap = max(-1.0, min(1.0, s_vwap))

        # 3. Strength: ADX gives magnitude, DI gives sign. Below adx_min the
        #    market is ranging and the component contributes nothing.
        s_force = 0.0
        adx_i, dip, dim = adx_v[i], di_p[i], di_m[i]
        if adx_i is not None and dip is not None and dim is not None:
            if adx_i > adx_min and adx_full > adx_min:
                s_force = min(1.0, (adx_i - adx_min) / (adx_full - adx_min))
                if dim > dip:
                    s_force = -s_force

        score = w_trend * s_trend + w_vwap * s_vwap + w_force * s_force

        # 4/5. Exhaustion brake and volume confirmation.
        ifr_delta = 0.0
        vol_delta = 0.0
        if score > 0:
            if rv > rsi_high:
                ifr_delta = -w_rsi
            if volumes[i] > vm:
                vol_delta = w_volume
        elif score < 0:
            if rv < rsi_low:
                ifr_delta = w_rsi
            if volumes[i] > vm:
                vol_delta = -w_volume
        score += ifr_delta + vol_delta

        scores[i] = score
        parts[i] = {
            "tendencia": w_trend * s_trend,
            "vwap": w_vwap * s_vwap,
            "forca": w_force * s_force,
            "ifr": ifr_delta,
            "volume": vol_delta,
        }
    if return_components:
        return scores, a, parts
    return scores, a


class Confluencia(Setup):
    """Trades the confluence score: enter when it crosses the threshold, with
    the cost gate vetoing sessions too quiet to pay the round trip.

    ``cost_points_round_trip`` is the friction in index points — for WIN, one
    tick of slippage per side plus emolumentos is about 11 points. The gate
    refuses a signal whenever ATR is below ``atr_multiple`` times that, because
    below it there is no move on the chart large enough to cover the ticket.
    """

    def __init__(
        self,
        threshold: float = 45.0,
        atr_stop: float = 1.5,
        cost_points_round_trip: float = 11.0,
        atr_multiple: float = 4.0,
        use_cost_gate: bool = True,
        allow_short: bool = True,
    ):
        self.threshold = threshold
        self.atr_stop = atr_stop
        self.cost_points_round_trip = cost_points_round_trip
        self.atr_multiple = atr_multiple
        self.use_cost_gate = use_cost_gate
        self.allow_short = allow_short
        gate = f",gate{atr_multiple:g}x" if use_cost_gate else ",nogate"
        self.name = f"Confluencia(lim{threshold:g},stop{atr_stop:g}atr{gate}{',L' if not allow_short else ''})"

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        scores, a = confluence_score(bars)
        atr_min = self.atr_multiple * self.cost_points_round_trip
        half = self.threshold / 2.0

        for i in range(1, len(bars)):
            s, prev_s, av = scores[i], scores[i - 1], a[i]
            if s is None or av is None or av <= 0:
                continue

            # Losing confluence closes the position, independently of the gate.
            p.exit_long[i] = s < half
            p.exit_short[i] = s > -half

            if self.use_cost_gate and av < atr_min:
                continue  # the market is not paying the toll today
            if prev_s is None:
                continue

            # Cross of the threshold, not merely sitting above it: entering on
            # a level already held for twenty bars is entering late.
            if s >= self.threshold and prev_s < self.threshold:
                p.entries[i] = Entry(LONG, None, bars[i].close - self.atr_stop * av, valid_bars=1)
            elif self.allow_short and s <= -self.threshold and prev_s > -self.threshold:
                p.entries[i] = Entry(SHORT, None, bars[i].close + self.atr_stop * av, valid_bars=1)
        return p


class ConfluenciaSinal(Setup):
    """Confluence score as an explicit entry signal, with a structural stop.

    Answers "where do I buy, where do I sell" rather than "what is the market
    doing". Three decisions define it:

    **Where.** A cross of the score threshold, with the cost gate passing. A
    cross rather than a level: entering on a threshold already held for twenty
    bars is entering late.

    **The stop.** The nearest structural invalidation — the swing low under a
    long, the swing high over a short, one tick beyond — rather than a fixed
    ATR multiple. That is the smallest stop the chart actually justifies: below
    the swing, the reason for the trade is gone.

    **The clamp.** The structural stop is then held inside
    ``[min_risk_ticks, max_risk_ticks]``. The floor is not risk aversion, it is
    arithmetic: round-trip friction is a fixed ~11 points in WIN, so as the
    stop shrinks the cost eats a rising share of a target that shrinks with it.
    At a 2.5R target the break-even hit rate is ``(R + cost) / (3.5 * R)`` —
    31.7% at R=100 points but 60% at R=10, against the ~28.6% that the geometry
    alone gives. Shrinking the stop does not make the trade cheaper; it makes
    the edge you need larger. ``min_risk_ticks`` is where that stops being
    worth it, and ``replay.py`` measures it rather than assuming it.

    The engine derives the target from the realised fill, so the reward really
    is ``reward_r`` times the risk actually taken, not the risk hoped for.
    """

    def __init__(
        self,
        threshold: float = 45.0,
        swing_lookback: int = 5,
        min_risk_ticks: int = 8,
        max_risk_ticks: int = 40,
        min_atr: float = 0.0,
        reward_r: float = 2.5,
        cost_points_round_trip: float = 11.0,
        atr_multiple: float = 4.0,
        use_cost_gate: bool = True,
        allow_short: bool = True,
        exit_on_confluence_loss: bool = True,
    ):
        self.exit_on_confluence_loss = exit_on_confluence_loss
        self.threshold = threshold
        self.swing_lookback = swing_lookback
        self.min_risk_ticks = min_risk_ticks
        self.max_risk_ticks = max_risk_ticks
        self.min_atr = min_atr
        self.reward_r = reward_r
        self.cost_points_round_trip = cost_points_round_trip
        self.atr_multiple = atr_multiple
        self.use_cost_gate = use_cost_gate
        self.allow_short = allow_short
        gate = f",gate{atr_multiple:g}x" if use_cost_gate else ",nogate"
        atrs = f",min{min_atr:g}atr" if min_atr > 0 else ""
        self.name = (
            f"Sinal(lim{threshold:g},sw{swing_lookback},"
            f"R{min_risk_ticks}-{max_risk_ticks}t{atrs},alvo{reward_r:g}R{gate}"
            f"{',L' if not allow_short else ''})"
        )

    def plan(self, bars: list[Bar], contract: Contract) -> Plan:
        p = Plan.blank(len(bars))
        scores, a = confluence_score(bars)
        atr_min = self.atr_multiple * self.cost_points_round_trip
        tick = contract.tick_size
        half = self.threshold / 2.0
        lb = self.swing_lookback

        for i in range(1, len(bars)):
            s, prev_s, av = scores[i], scores[i - 1], a[i]
            if s is None or av is None or av <= 0:
                continue

            # Losing the confluence closes the position regardless of the gate.
            # Switchable because comparing entry quality against a control
            # demands identical management on both sides; an exit the control
            # cannot have would make the comparison measure the exit instead.
            if self.exit_on_confluence_loss:
                p.exit_long[i] = s < half
                p.exit_short[i] = s > -half

            if self.use_cost_gate and av < atr_min:
                continue
            if prev_s is None or i < lb:
                continue

            ref = bars[i].close
            window = bars[i - lb + 1 : i + 1]

            # The stop must clear one bar's own noise, otherwise the ordinary
            # oscillation of a single candle takes the trade out before the
            # idea has had a chance to be wrong. ATR is the adaptive way to
            # say "one bar": it rescales with the timeframe and with the day.
            floor_price = self.min_atr * av if self.min_atr > 0 else 0.0

            if s >= self.threshold and prev_s < self.threshold:
                stop = min(b.low for b in window) - tick
                stop = min(stop, ref - floor_price) if floor_price else stop
                stop = self._clamp(ref, stop, tick, LONG)
                if stop < ref:
                    p.entries[i] = Entry(LONG, None, stop, valid_bars=1)
            elif self.allow_short and s <= -self.threshold and prev_s > -self.threshold:
                stop = max(b.high for b in window) + tick
                stop = max(stop, ref + floor_price) if floor_price else stop
                stop = self._clamp(ref, stop, tick, SHORT)
                if stop > ref:
                    p.entries[i] = Entry(SHORT, None, stop, valid_bars=1)
        return p

    def _clamp(self, ref: float, stop: float, tick: float, side: int) -> float:
        """Hold the structural stop inside the viable risk band."""
        risk_ticks = abs(ref - stop) / tick
        if risk_ticks < self.min_risk_ticks:
            risk_ticks = self.min_risk_ticks
        elif risk_ticks > self.max_risk_ticks:
            risk_ticks = self.max_risk_ticks
        else:
            return stop
        return ref - risk_ticks * tick if side == LONG else ref + risk_ticks * tick
