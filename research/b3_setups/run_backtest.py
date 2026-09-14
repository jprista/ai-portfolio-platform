#!/usr/bin/env python3
"""Sweep the published setups over WIN/WDO bars and correct for the search.

Usage
-----
Real data (an intraday OHLCV export from Profit, MetaTrader or any CSV):
    python3 run_backtest.py --csv WIN_5min.csv --contract WIN

No-edge control series (no market data required):
    python3 run_backtest.py --synthetic --sessions 250

The control run answers one question only: how much apparent performance does
this search procedure manufacture from a series that has no edge by
construction? It says nothing about whether these setups work on real WIN.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from b3setups import placebo as placebo_mod  # noqa: E402
from b3setups import report  # noqa: E402
from b3setups.bars import validate  # noqa: E402
from b3setups.contracts import CONTRACTS, CostModel  # noqa: E402
from b3setups.data import load_csv, synthetic_sessions  # noqa: E402
from b3setups.bars import split_sessions  # noqa: E402
from b3setups.engine import ExecConfig, run  # noqa: E402
from b3setups.setups import (  # noqa: E402
    BollingerReversion,
    Confluencia,
    DidiAgulhada,
    IFR2,
    Setup91,
    Setup92,
    Setup93,
    VwapFiltered,
)
from b3setups.stats import (  # noqa: E402
    bootstrap_mean_ci,
    deflated_sharpe,
    reality_check,
    session_pnl,
    summarise,
)

TARGET_RS: list[float | None] = [1.0, 2.0, 3.0, None]


def build_family() -> list:
    """The variant grid. Its SIZE is an input to the correction, so every
    variant added here raises the bar the winner has to clear."""
    base: list = []
    for period in (9, 21):
        base.append(Setup91(period=period))
        base.append(Setup92(period=period))
        base.append(Setup93(period=period))
    for entry_thr in (10.0, 25.0):
        for trend in (49, 100):
            base.append(IFR2(entry_thr=entry_thr, trend_period=trend))
    for mult in (2.0, 2.5):
        base.append(BollingerReversion(mult=mult))
    base.append(DidiAgulhada())
    # Confluencia already carries its own VWAP layer and cost gate, so it is
    # added after the wrapper rather than being wrapped a second time.
    combos = base + [VwapFiltered(s) for s in base]
    for threshold in (35.0, 45.0, 55.0):
        combos.append(Confluencia(threshold=threshold))
    combos.append(Confluencia(use_cost_gate=False))
    return combos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=Path, help="intraday OHLCV export")
    src.add_argument("--synthetic", action="store_true", help="no-edge control series")
    ap.add_argument("--contract", default="WIN", choices=sorted(CONTRACTS))
    ap.add_argument("--sessions", type=int, default=250, help="synthetic only")
    ap.add_argument("--seed", type=int, default=20260914, help="synthetic only")
    ap.add_argument("--contracts", type=int, default=1)
    ap.add_argument("--brokerage-cents", type=int, default=0)
    ap.add_argument("--exchange-cents", type=int, default=27)
    ap.add_argument("--slippage-ticks", type=int, default=1)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--placebo", type=int, default=30,
                    help="no-edge control series for the placebo null (0 disables)")
    args = ap.parse_args()

    contract = CONTRACTS[args.contract]
    costs = CostModel(
        brokerage_cents_per_side=args.brokerage_cents,
        exchange_cents_per_side=args.exchange_cents,
        slippage_ticks_per_side=args.slippage_ticks,
    )

    if args.synthetic:
        sessions = synthetic_sessions(contract, n_sessions=args.sessions, seed=args.seed)
        source = f"NO-EDGE CONTROL SERIES (seed {args.seed}) — not market data"
    else:
        bars = load_csv(args.csv)
        problems = validate(bars)
        if problems:
            print("Data quality problems — refusing to run:", file=sys.stderr)
            for p in problems:
                print("  -", p, file=sys.stderr)
            return 2
        sessions = split_sessions(bars)
        source = str(args.csv)

    if not sessions:
        print("No usable sessions in the input.", file=sys.stderr)
        return 2

    family = build_family()
    variants: list[tuple[str, object, ExecConfig]] = []
    for setup in family:
        for tr in TARGET_RS:
            label = f"{setup.name} r={tr if tr is not None else 'none'}"
            variants.append((label, setup, ExecConfig(target_r=tr, contracts=args.contracts)))

    n_bars = sum(len(s) for s in sessions)
    print(report.header(source, contract, costs, len(sessions), n_bars, len(variants)))
    print(f"\nrunning {len(variants)} variants ...", flush=True)

    rows = []
    matrix_cols = []
    for label, setup, cfg in variants:
        trades = run(sessions, setup, contract, costs, cfg)
        rows.append(summarise(label, trades, sessions))
        matrix_cols.append(session_pnl(trades, sessions))

    print(report.table(rows, contract, limit=args.top))
    print(report.cost_analysis(rows, contract))

    names = [r.name for r in rows]
    matrix = [[col[s] for col in matrix_cols] for s in range(len(sessions))]
    best_name, _, p_value, means = reality_check(matrix, names, n_boot=args.boot)

    naive_best = max(rows, key=lambda r: r.total_cents).name
    best_idx = names.index(best_name)
    best_series = matrix_cols[best_idx]
    sr, sr0, dsr_prob = deflated_sharpe(best_series, n_trials=len(variants))
    boot = bootstrap_mean_ci(best_series, n_boot=min(args.boot, 2000))

    print(report.significance(best_name, p_value, len(variants), sr, sr0, dsr_prob, boot, naive_best))

    if args.placebo > 0:
        print(f"\ncalibrating placebo null over {args.placebo} no-edge series ...", flush=True)
        cal = placebo_mod.calibrate(
            family, TARGET_RS, contract, costs,
            n_series=args.placebo, n_sessions=len(sessions), contracts=args.contracts,
        )
        observed = max(sum(col) / len(col) for col in matrix_cols)
        print(report.placebo_block(cal, observed))

    if args.synthetic:
        print(
            "\nREMINDER: this ran on a driftless random walk. Any variant showing a\n"
            "profit here is showing noise plus survivorship of the search, nothing else."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
