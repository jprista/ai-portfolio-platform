"""Golden tests for execution. Every expected P&L is derived by hand below.

WIN arithmetic used throughout: 1 tick = 5 index points = R$1.00 = 100 centavos.
Cost model: exchange 27 c/side + slippage 1 tick/side
  => fixed 2 x 27 = 54 c, slippage 2 x 100 = 200 c, round trip = 254 c.
Run:  python3 tests/engine_test.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups.bars import Bar, Session  # noqa: E402
from b3setups.contracts import WIN, CostModel  # noqa: E402
from b3setups.engine import ExecConfig, run_session  # noqa: E402
from b3setups.setups import LONG, SHORT, Entry, Plan, Setup  # noqa: E402

FAILURES: list[str] = []
COSTS = CostModel(brokerage_cents_per_side=0, exchange_cents_per_side=27, slippage_ticks_per_side=1)
ROUND_TRIP = 254


def check(name: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


T0 = datetime(2026, 3, 2, 9, 5)


def mk(seq: list[tuple[float, float, float, float]]) -> Session:
    bars = [Bar(T0 + timedelta(minutes=5 * i), o, h, lo, c, 100.0) for i, (o, h, lo, c) in enumerate(seq)]
    return Session(day=T0.date(), bars=bars)


class Stub(Setup):
    """Emits one fixed Entry at a chosen bar index."""

    name = "stub"

    def __init__(self, index: int, entry: Entry):
        self.index = index
        self.entry = entry

    def plan(self, bars, contract):
        p = Plan.blank(len(bars))
        p.entries[self.index] = self.entry
        return p


cfg = ExecConfig(target_r=2.0, contracts=1, no_entry_last_frac=0.10)

# --- (a) market long, target hit.
# Entry 130000 at bar1 open, stop 129900 -> risk 100 pts; target_r 2 -> 130200.
# Exit 130200: (26040 - 26000) = 40 ticks x 100 c = 4000 c gross; net 4000 - 254 = 3746.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130000, 130250, 129980, 130200),
    (130200, 130210, 130190, 130200),
])
t = run_session(s, Stub(0, Entry(LONG, None, 129900.0, valid_bars=1)), WIN, COSTS, cfg)
check("(a) one trade", len(t), 1)
if t:
    check("(a) reason", t[0].reason, "target")
    check("(a) tick delta", t[0].tick_delta, 40)
    check("(a) gross cents", t[0].gross_cents, 4000)
    check("(a) cost cents", t[0].cost_cents, ROUND_TRIP)
    check("(a) net cents", t[0].net_cents, 3746)

# --- (b) market long, stop hit. Exit 129900: -20 ticks -> -2000 c gross; net -2254.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129850, 129900),
    (129900, 129910, 129890, 129900),
])
t = run_session(s, Stub(0, Entry(LONG, None, 129900.0, valid_bars=1)), WIN, COSTS, cfg)
check("(b) one trade", len(t), 1)
if t:
    check("(b) reason", t[0].reason, "stop")
    check("(b) net cents", t[0].net_cents, -2254)

# --- (c) bar contains BOTH stop and target -> stop must win (conservative).
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130250, 129850, 130000),
    (130000, 130010, 129990, 130000),
])
t = run_session(s, Stub(0, Entry(LONG, None, 129900.0, valid_bars=1)), WIN, COSTS, cfg)
check("(c) one trade", len(t), 1)
if t:
    check("(c) stop wins over target", t[0].reason, "stop")

# --- (d) gap through a stop-entry trigger fills at the OPEN, not the trigger.
# Trigger 130100, bar1 opens 130200 -> fill 130200 (= 26040 ticks).
s = mk([
    (130000, 130010, 129990, 130000),
    (130200, 130260, 130150, 130200),
    (130200, 130210, 130190, 130200),
])
t = run_session(s, Stub(0, Entry(LONG, 130100.0, 130000.0, valid_bars=2)), WIN, COSTS, cfg)
check("(d) one trade", len(t), 1)
if t:
    check("(d) filled at open not trigger", t[0].entry_ticks, WIN.to_ticks(130200))

# --- (e) no lookahead: bar0's own range straddles the trigger, yet the fill
#     must land on bar1. Entry is emitted from bar0's close.
s = mk([
    (130000, 130500, 129500, 130000),
    (130050, 130060, 130040, 130050),
    (130050, 130060, 130040, 130050),
])
t = run_session(s, Stub(0, Entry(LONG, 130100.0, 129000.0, valid_bars=3)), WIN, COSTS, cfg)
check("(e) no same-bar fill", len(t), 0)

# --- (f) unfilled position is force-closed at the session close.
# Entry 130000 at bar1 open; never reaches stop 129000 or target 132000.
# Last bar closes 130100 -> (26020-26000) = 20 ticks -> 2000 c gross, net 1746.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130050, 130120, 130040, 130100),
])
t = run_session(s, Stub(0, Entry(LONG, None, 129000.0, valid_bars=1)), WIN, COSTS, cfg)
check("(f) one trade", len(t), 1)
if t:
    check("(f) reason", t[0].reason, "session_close")
    check("(f) net cents", t[0].net_cents, 1746)

# --- (g) degenerate geometry: a long whose stop sits ABOVE the fill is refused.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130000, 130010, 129990, 130000),
])
t = run_session(s, Stub(0, Entry(LONG, None, 130100.0, valid_bars=1)), WIN, COSTS, cfg)
check("(g) refused", len(t), 0)

# --- (h) short side mirrors. Entry 130000, stop 130100 (risk 100), target 129800.
# Exit 129800: (25960 - 26000) = -40 ticks x side -1 = +40 -> 4000 c; net 3746.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130000, 130020, 129750, 129800),
    (129800, 129810, 129790, 129800),
])
t = run_session(s, Stub(0, Entry(SHORT, None, 130100.0, valid_bars=1)), WIN, COSTS, cfg)
check("(h) one trade", len(t), 1)
if t:
    check("(h) reason", t[0].reason, "target")
    check("(h) tick delta", t[0].tick_delta, 40)
    check("(h) net cents", t[0].net_cents, 3746)

# --- (i) costs scale with contracts: 5 contracts -> 5 x 254 = 1270 c.
cfg5 = ExecConfig(target_r=2.0, contracts=5, no_entry_last_frac=0.10)
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130000, 130250, 129980, 130200),
    (130200, 130210, 130190, 130200),
])
t = run_session(s, Stub(0, Entry(LONG, None, 129900.0, valid_bars=1)), WIN, COSTS, cfg5)
if t:
    check("(i) cost x5", t[0].cost_cents, 1270)
    check("(i) gross x5", t[0].gross_cents, 20000)

# --- (j) an expired trigger never fills. valid_bars=1 means bar1 only.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130010, 129990, 130000),
    (130000, 130500, 129990, 130400),
    (130400, 130410, 130390, 130400),
])
t = run_session(s, Stub(0, Entry(LONG, 130100.0, 129900.0, valid_bars=1)), WIN, COSTS, cfg)
check("(j) expired trigger", len(t), 0)

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("engine_test: all golden checks passed")
