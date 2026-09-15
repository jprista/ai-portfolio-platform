"""Golden tests for the breakeven move, scaling out, and position grouping.

Run:  python3 tests/saidas_test.py
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
from b3setups.setups import LONG, Entry, Plan, Setup  # noqa: E402
from b3setups.stats import by_position, summarise_positions  # noqa: E402

FAILURES: list[str] = []
COSTS = CostModel(brokerage_cents_per_side=0, exchange_cents_per_side=27, slippage_ticks_per_side=1)
T0 = datetime(2026, 3, 2, 9, 5)


def check(name: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


def mk(seq):
    return Session(day=T0.date(),
                   bars=[Bar(T0 + timedelta(minutes=5 * i), o, h, l, c, 100.0)
                         for i, (o, h, l, c) in enumerate(seq)])


class Stub(Setup):
    name = "stub"

    def __init__(self, i, entry):
        self.i, self.entry = i, entry

    def plan(self, bars, contract):
        p = Plan.blank(len(bars))
        p.entries[self.i] = self.entry
        return p


# Entry 130000 at bar1 open, stop 129900 -> risk 100 pts = 20 ticks.
ENTRY = Entry(LONG, None, 129900.0, valid_bars=1)

# --- Breakeven: price reaches 1R (130100), comes back to the entry.
# The stop is now at 130000, so the position scratches instead of losing 100 pts.
# Gross 0; cost 254 -> net -254.
s = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130000, 130120, 129980, 130100),   # touches 1R -> stop moves to entry
    (130100, 130110, 129880, 129900),   # comes all the way back through the entry
])
t = run_session(s, Stub(0, ENTRY), WIN, COSTS, ExecConfig(target_r=2.5, breakeven_at_r=1.0))
check("(be) one leg", len(t), 1)
if t:
    check("(be) exited at the entry", t[0].exit_ticks, WIN.to_ticks(130000.0))
    check("(be) gross is zero", t[0].gross_cents, 0)
    check("(be) net is minus the cost", t[0].net_cents, -254)
    check("(be) reason", t[0].reason, "breakeven")

# --- Without the breakeven the SAME path is a full stop: the bar reaches
#     129880, below the original 129900, so it fills there: -20 ticks = -2000.
t2 = run_session(s, Stub(0, ENTRY), WIN, COSTS, ExecConfig(target_r=2.5))
check("(no-be) full stop", t2[0].reason if t2 else None, "stop")
check("(no-be) loses the full R", t2[0].gross_cents if t2 else None, -2000)
print(f"  mesma barra, com zero a zero: {t[0].net_cents} c | sem: {t2[0].net_cents} c")

# --- Scaling out: 2 contracts, half booked at 1R, rest runs to 2.5R (130250).
# Leg 1: +20 ticks x 1 contrato = 2000 c gross, cost 254  -> 1746
# Leg 2: +50 ticks x 1 contrato = 5000 c gross, cost 254  -> 4746
s2 = mk([
    (130000, 130010, 129990, 130000),
    (130000, 130050, 129950, 130000),
    (130000, 130120, 129980, 130100),   # 1R -> partial
    (130100, 130260, 130080, 130250),   # 2.5R -> the rest
])
t3 = run_session(s2, Stub(0, ENTRY), WIN, COSTS,
                 ExecConfig(target_r=2.5, contracts=2, partial_at_r=1.0, partial_fraction=0.5))
check("(part) two legs", len(t3), 2)
if len(t3) == 2:
    check("(part) first is the partial", t3[0].reason, "partial")
    check("(part) partial size", t3[0].contracts, 1)
    check("(part) partial net", t3[0].net_cents, 1746)
    check("(part) runner is the target", t3[1].reason, "target")
    check("(part) runner net", t3[1].net_cents, 4746)
    check("(part) same position", t3[0].position_id, t3[1].position_id)

# --- THE POINT OF position_id: two legs, ONE decision.
nets = by_position(t3)
check("(pos) one position", len(nets), 1)
check("(pos) recombined net", nets[0], 1746 + 4746)
st = summarise_positions("x", t3)
check("(pos) counted once", st.n_positions, 1)
check("(pos) hit rate is 100% of ONE position", st.wins, 1)
print(f"  saída parcial: 2 pernas, {st.n_positions} posição — acerto contado uma vez, não duas")

# --- A partial must never close the whole position.
t4 = run_session(s2, Stub(0, ENTRY), WIN, COSTS,
                 ExecConfig(target_r=2.5, contracts=2, partial_at_r=1.0, partial_fraction=1.0))
if t4 and t4[0].reason == "partial" and t4[0].contracts >= 2:
    FAILURES.append("a parcial fechou a posição inteira")

# --- With a single contract there is nothing to scale out of.
t5 = run_session(s2, Stub(0, ENTRY), WIN, COSTS,
                 ExecConfig(target_r=2.5, contracts=1, partial_at_r=1.0))
check("(part-1) no partial with one contract", sum(1 for x in t5 if x.reason == "partial"), 0)

# --- The flat band must classify a breakeven exit as flat, not as a loss.
stf = summarise_positions("y", t, flat_band_cents=300)
check("(flat) breakeven counts as flat", stf.flats, 1)
check("(flat) not a loss", stf.losses, 0)

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("saidas_test: all checks passed")
