"""Golden tests for the indicators — hand-derived values, literal arithmetic.

Every expectation below is computed by hand in the docstring of its check and
written as a literal. Nothing here calls the module under test to produce its
own expectation. Run:  python3 tests/indicators_test.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups import indicators as ind  # noqa: E402
from b3setups.bars import Bar, split_sessions, validate  # noqa: E402

FAILURES: list[str] = []
TOL = 1e-9


def check(name: str, got, want, tol: float = TOL) -> None:
    if want is None or got is None:
        ok = got is want
    else:
        ok = abs(got - want) <= tol
    if not ok:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


def bar(ts: str, o: float, h: float, lo: float, c: float, v: float = 100.0) -> Bar:
    return Bar(datetime.fromisoformat(ts), o, h, lo, c, v)


# --- SMA: [1,2,3,4,5] period 3 -> (1+2+3)/3=2, (2+3+4)/3=3, (3+4+5)/3=4
s = ind.sma([1, 2, 3, 4, 5], 3)
check("sma warmup 0", s[0], None)
check("sma warmup 1", s[1], None)
check("sma[2]", s[2], 2.0)
check("sma[3]", s[3], 3.0)
check("sma[4]", s[4], 4.0)

# --- EMA: [1,2,3,4,5] period 3. Seed = SMA(1,2,3) = 2 at index 2. k = 2/(3+1) = 0.5
#     i3: (4-2)*0.5 + 2 = 3.0     i4: (5-3)*0.5 + 3 = 4.0
e = ind.ema([1, 2, 3, 4, 5], 3)
check("ema warmup", e[1], None)
check("ema seed", e[2], 2.0)
check("ema[3]", e[3], 3.0)
check("ema[4]", e[4], 4.0)

# --- RSI(2) on [10, 11, 10, 12, 11]; deltas +1, -1, +2, -1
#     seed over first 2 deltas: avg_gain = 1/2 = 0.5, avg_loss = 1/2 = 0.5
#       -> rs = 1, rsi = 100 - 100/2 = 50
#     i3 (delta +2): gain = (0.5*1 + 2)/2 = 1.25, loss = (0.5*1 + 0)/2 = 0.25
#       -> rs = 5, rsi = 100 - 100/6 = 83.333333...
#     i4 (delta -1): gain = (1.25*1 + 0)/2 = 0.625, loss = (0.25*1 + 1)/2 = 0.625
#       -> rs = 1, rsi = 50
r = ind.rsi([10, 11, 10, 12, 11], 2)
check("rsi warmup", r[1], None)
check("rsi[2]", r[2], 50.0)
check("rsi[3]", r[3], 100.0 - 100.0 / 6.0, 1e-9)
check("rsi[4]", r[4], 50.0)

# --- RSI edge: monotonic rise has no losses -> 100
check("rsi all gains", ind.rsi([1, 2, 3, 4, 5], 2)[4], 100.0)

# --- Population stdev: [2,4,4,4,5,5,7,9] period 8. mean = 40/8 = 5.
#     squared devs = 9+1+1+1+0+0+4+16 = 32; var = 32/8 = 4; sd = 2
sd = ind.stdev_pop([2, 4, 4, 4, 5, 5, 7, 9], 8)
check("stdev_pop", sd[7], 2.0)

# --- Bollinger on the same window: mid 5, lower 5-2*2 = 1, upper 5+2*2 = 9
low, mid, up = ind.bollinger([2, 4, 4, 4, 5, 5, 7, 9], 8, 2.0)
check("bb mid", mid[7], 5.0)
check("bb lower", low[7], 1.0)
check("bb upper", up[7], 9.0)

# --- True Range / ATR. Bars rise one point a bar with a 2-point range.
#     b1: max(12-10, |12-10|, |10-10|) = 2 ; b2 and b3 likewise = 2
bars = [
    bar("2026-03-02T09:05", 10, 11, 9, 10),
    bar("2026-03-02T09:10", 10, 12, 10, 11),
    bar("2026-03-02T09:15", 11, 13, 11, 12),
    bar("2026-03-02T09:20", 12, 14, 12, 13),
]
tr = ind.true_range(bars)
check("tr[0] undefined", tr[0], None)
check("tr[1]", tr[1], 2.0)
a = ind.atr(bars, 2)
check("atr warmup", a[1], None)
check("atr seed", a[2], 2.0)
check("atr[3]", a[3], 2.0)

# --- Session VWAP. typical(b0) = (11+9+10)/3 = 10 ; typical(b1) = (12+10+11)/3 = 11
#     after b1 with equal volume: (10*100 + 11*100)/200 = 10.5
v = ind.session_vwap(bars)
check("vwap[0]", v[0], 10.0)
check("vwap[1]", v[1], 10.5)

# --- VWAP with zero volume falls back to the running mean of typical price
zero_vol = [bar("2026-03-02T09:05", 10, 11, 9, 10, 0.0), bar("2026-03-02T09:10", 10, 12, 10, 11, 0.0)]
vz = ind.session_vwap(zero_vol)
check("vwap zero-vol[1]", vz[1], 10.5)

# --- ADX on a clean uptrend: +DI must dominate -DI once defined
up_bars = [bar(f"2026-03-02T{9 + i // 12:02d}:{(i * 5) % 60:02d}", 100 + i, 102 + i, 99 + i, 101 + i) for i in range(60)]
pdi, mdi, adx_v = ind.adx(up_bars, 14)
last_pdi = [x for x in pdi if x is not None][-1]
last_mdi = [x for x in mdi if x is not None][-1]
if not last_pdi > last_mdi:
    FAILURES.append(f"adx uptrend: +DI {last_pdi} should exceed -DI {last_mdi}")
if not any(x is not None for x in adx_v):
    FAILURES.append("adx: never produced a value on 60 bars")

# --- Session splitting drops stubs below min_bars
mixed = [bar(f"2026-03-02T09:{i * 5:02d}", 10, 11, 9, 10) for i in range(0, 6)] + [
    bar(f"2026-03-03T09:{i * 5:02d}", 10, 11, 9, 10) for i in range(0, 3)
]
sessions = split_sessions(mixed, min_bars=5)
check("sessions kept", float(len(sessions)), 1.0)
check("session length", float(len(sessions[0])), 6.0)

# --- Validation catches an impossible bar
bad = [Bar(datetime(2026, 3, 2, 9, 5), 10, 9, 11, 10, 100)]
if not validate(bad):
    FAILURES.append("validate: failed to flag inverted high/low")
if validate(bars):
    FAILURES.append("validate: false positive on clean bars")

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("indicators_test: all golden checks passed")
