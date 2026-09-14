#!/usr/bin/env python3
"""Replay validation for the Confluencia entry signal.

    python3 run_replay.py --csv WIN_5min.csv --contract WIN
    python3 run_replay.py --synthetic --sessions 250

Three reports: the stop-size sweep, the chronological walk-forward, and the
placebo null. The first is arithmetic and holds on any data; the second and
third only mean something on real market data.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from b3setups.bars import split_sessions, validate  # noqa: E402
from b3setups.contracts import CONTRACTS, CostModel, cents_to_brl  # noqa: E402
from b3setups.data import load_csv, synthetic_sessions  # noqa: E402
from b3setups.engine import ExecConfig, run  # noqa: E402
from b3setups.placebo import calibrate  # noqa: E402
from b3setups.replay import fair_win_rate, session_curve, stop_sweep, walk_forward  # noqa: E402
from b3setups.setups import ConfluenciaSinal  # noqa: E402
from b3setups.stats import session_pnl  # noqa: E402

RISK_CAPS = [4, 6, 8, 10, 14, 18, 24, 30, 40, 56, 80]


def bar(title: str) -> str:
    return f"\n{title}\n{'=' * max(len(title), 40)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=Path)
    src.add_argument("--synthetic", action="store_true")
    ap.add_argument("--contract", default="WIN", choices=sorted(CONTRACTS))
    ap.add_argument("--sessions", type=int, default=250)
    ap.add_argument("--seed", type=int, default=20260914)
    ap.add_argument("--reward", type=float, default=2.5)
    ap.add_argument("--threshold", type=float, default=45.0)
    ap.add_argument("--swing", type=int, default=5)
    ap.add_argument("--min-risk", type=int, default=2)
    ap.add_argument("--cost-points", type=float, default=11.0)
    ap.add_argument("--slippage-ticks", type=int, default=1)
    ap.add_argument("--exchange-cents", type=int, default=27)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--placebo", type=int, default=20)
    ap.add_argument("--plausible-hit", type=float, default=0.35,
                    help="acerto que você considera alcançável no alvo escolhido; "
                         "o teto recomendado é o stop mais apertado que ainda cabe nele")
    args = ap.parse_args()

    contract = CONTRACTS[args.contract]
    costs = CostModel(
        brokerage_cents_per_side=0,
        exchange_cents_per_side=args.exchange_cents,
        slippage_ticks_per_side=args.slippage_ticks,
    )

    if args.synthetic:
        sessions = synthetic_sessions(contract, n_sessions=args.sessions, seed=args.seed)
        source = f"SÉRIE DE CONTROLE SEM EDGE (seed {args.seed}) — não é dado de mercado"
    else:
        bars = load_csv(args.csv)
        problems = validate(bars)
        if problems:
            print("Dados inconsistentes — execução recusada:", file=sys.stderr)
            for p in problems:
                print("  -", p, file=sys.stderr)
            return 2
        sessions = split_sessions(bars)
        source = str(args.csv)
    if not sessions:
        print("Nenhuma sessão utilizável.", file=sys.stderr)
        return 2

    rt = cents_to_brl(costs.total_round_trip_cents(contract, 1))
    print(bar(f"REPLAY — {contract.symbol} — {source}"))
    print(f"sessões              {len(sessions)}")
    print(f"barras               {sum(len(s) for s in sessions)}")
    print(f"alvo                 {args.reward:g}R")
    print(f"custo ida e volta    {rt}/contrato  ({args.cost_points:g} pontos)")

    def make(cap: int) -> ConfluenciaSinal:
        # The cap is the knob: how tight the structural stop may be pulled.
        return ConfluenciaSinal(
            threshold=args.threshold, swing_lookback=args.swing,
            min_risk_ticks=args.min_risk, max_risk_ticks=cap,
            reward_r=args.reward, cost_points_round_trip=args.cost_points,
        )

    # --- 1. stop sweep
    print(bar("1. TAMANHO DO STOP — qual o menor stop que ainda paga"))
    print(f"a geometria de um alvo {args.reward:g}R entrega {fair_win_rate(args.reward):.1%} de acerto.")
    print("abaixo, o que o custo exige a mais em cada tamanho de stop.\n")
    head = (f"{'stop máx':>9} {'risco méd':>10} {'trades':>7} {'acerto':>8} "
            f"{'precisa':>8} {'folga':>7} {'exp/trade':>11} {'total':>12} {'custo/bruto':>12}")
    print(head)
    print("-" * len(head))
    rows = stop_sweep(sessions, make, contract, costs, RISK_CAPS, args.reward, args.cost_points)
    best = None
    for r in rows:
        if r.n_trades == 0:
            print(f"{r.param_ticks:>7}t {'—':>10} {0:>7}")
            continue
        drag = (100.0 * r.cost_cents / r.gross_cents) if r.gross_cents > 0 else float("nan")
        drag_s = f"{drag:>11.0f}%" if drag == drag else f"{'—':>12}"
        print(
            f"{r.param_ticks:>7}t {r.avg_risk_points:>9.0f}p {r.n_trades:>7} "
            f"{100 * r.win_rate:>7.1f}% {100 * r.required_win_rate:>7.1f}% "
            f"{100 * r.edge_gap:>+6.1f}p {cents_to_brl(round(r.expectancy_cents)):>11} "
            f"{cents_to_brl(r.total_cents):>12} {drag_s}"
        )
        if best is None or r.expectancy_cents > best.expectancy_cents:
            best = r

    # The recommendation is arithmetic, not empirical. "precisa" is exact:
    # (R + custo) / (R * (1 + alvo)). The realised columns carry the
    # simulator's intrabar residual and cannot be trusted at this resolution,
    # so the tightest stop is chosen as the tightest one whose REQUIRED hit
    # rate still falls inside what the operator considers reachable.
    viable = [r for r in rows if r.n_trades > 0 and r.required_win_rate <= args.plausible_hit]
    rec = min(viable, key=lambda r: r.param_ticks) if viable else None
    print("\n'precisa' é aritmética exata: (R + custo) / (R x (1 + alvo)). Não depende do dado.")
    print("'acerto' e 'exp/trade' carregam o resíduo intrabarra do simulador — use com o placebo.")
    if rec:
        print(f"\nMENOR STOP QUE AINDA CABE EM {100 * args.plausible_hit:.0f}% DE ACERTO:")
        print(f"  teto de {rec.param_ticks} ticks = {contract.points(rec.param_ticks):.0f} pontos "
              f"(risco médio realizado {rec.avg_risk_points:.0f} pontos)")
        print(f"  exige {100 * rec.required_win_rate:.1f}% de acerto; a geometria dá "
              f"{100 * fair_win_rate(args.reward):.1f}%")
        tighter = [r for r in rows if r.param_ticks < rec.param_ticks and r.n_trades > 0]
        if tighter:
            t0 = max(tighter, key=lambda r: r.param_ticks)
            print(f"  apertar para {t0.param_ticks} ticks ({contract.points(t0.param_ticks):.0f} pts) "
                  f"já exigiria {100 * t0.required_win_rate:.1f}%")
    else:
        print(f"\nNENHUM teto testado cabe em {100 * args.plausible_hit:.0f}% de acerto "
              f"com alvo {args.reward:g}R e custo de {args.cost_points:g} pontos.")
        print("  ou o alvo sobe, ou o custo cai (slippage), ou a meta de acerto sobe.")
    if best:
        print(f"\n(maior expectativa observada foi no teto de {best.param_ticks} ticks — "
              "em dado sem edge isso é o artefato, não vantagem)")

    cap = rec.param_ticks if rec else (best.param_ticks if best else 24)
    setup = make(cap)

    # --- 2. walk-forward
    print(bar(f"2. WALK-FORWARD — {args.folds} blocos em ordem cronológica"))
    print(f"config: {setup.name}\n")
    head2 = f"{'bloco':<26} {'trades':>7} {'acerto':>8} {'exp/trade':>11} {'total':>12} {'maxDD':>11}"
    print(head2)
    print("-" * len(head2))
    folds = walk_forward(sessions, setup, contract, costs, args.folds, args.reward)
    pos = 0
    for st in folds:
        if st.total_cents > 0:
            pos += 1
        print(f"{st.name:<26} {st.n_trades:>7} {100 * st.win_rate:>7.1f}% "
              f"{cents_to_brl(round(st.expectancy_cents)):>11} "
              f"{cents_to_brl(st.total_cents):>12} {cents_to_brl(st.max_drawdown_cents):>11}")
    print(f"\nblocos positivos: {pos}/{len(folds)}"
          + ("  — resultado concentrado, não sustentado" if pos <= len(folds) // 2 else ""))

    per, equity = session_curve(sessions, setup, contract, costs, args.reward)
    if equity:
        peak = 0
        dd = 0
        for e in equity:
            peak = max(peak, e)
            dd = max(dd, peak - e)
        print(f"equity final {cents_to_brl(equity[-1])}   drawdown máximo {cents_to_brl(dd)}")
        best_s = sorted(per, reverse=True)[:3]
        share = (sum(best_s) / equity[-1] * 100) if equity[-1] > 0 else float("nan")
        if share == share:
            print(f"as 3 melhores sessões respondem por {share:.0f}% do resultado")

    # --- 3. placebo
    if args.placebo > 0:
        print(bar("3. NULO CALIBRADO — o mesmo sinal sobre séries sem edge"))
        family = [make(c) for c in (cap, max(4, cap // 2), cap * 2)]
        cal = calibrate(family, [args.reward], contract, costs,
                        n_series=args.placebo, n_sessions=len(sessions))
        trades = run(sessions, setup, contract, costs, ExecConfig(target_r=args.reward))
        obs = sum(session_pnl(trades, sessions)) / len(sessions)
        p = cal.p_value(obs)
        print(f"mediana do falso lucro     {cents_to_brl(round(cal.median))}/sessão")
        print(f"percentil 90               {cents_to_brl(round(cal.percentile(0.90)))}/sessão")
        print(f"observado neste dado       {cents_to_brl(round(obs))}/sessão")
        print(f"p-valor do placebo         {p:.4f}")
        print("  " + ("acima do que a busca fabrica sozinha" if p < 0.05
                      else "INDISTINGUÍVEL de dado sem vantagem nenhuma"))

    if args.synthetic:
        print("\nLEMBRETE: rodou sobre random walk sem drift. A tabela 1 é aritmética de custo\n"
              "e vale em qualquer dado; as tabelas 2 e 3 só significam algo com WIN real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
