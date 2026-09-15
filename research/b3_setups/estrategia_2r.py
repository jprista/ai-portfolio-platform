#!/usr/bin/env python3
"""A estratégia especificada: alvo 2R, parcial em 1R, stop ao zero na parcial.

    python3 estrategia_2r.py --csv WIN_5min.csv
    python3 estrategia_2r.py --synthetic

Os três desfechos possíveis de uma POSIÇÃO, e o que cada um vale:

    stop antes de 1R          -1,0R   a posição inteira morre
    1R -> parcial -> zero     +0,5R   metade no lucro, metade no empate
    1R -> parcial -> 2R       +1,5R   metade em 1R, metade em 2R

O TESTE QUE IMPORTA está no primeiro desfecho. Sem vantagem nenhuma, a chance de
tocar 1R antes do stop é 50%, porque as duas distâncias são iguais — é cara ou
coroa. Então:

    acerto de ~50% NÃO é o indicador funcionando, é a geometria.
    acerto acima de 50% é o único lugar onde uma vantagem real apareceria.

E a expectativa fecha em zero de propósito num mercado justo:
0,50x(-1,0R) + 0,25x(+0,5R) + 0,25x(+1,5R) = 0. Qualquer resultado positivo tem
de vir de empurrar o primeiro desfecho para baixo de 50% — nada mais.

Por isso este script compara o sinal contra ENTRADA ALEATÓRIA com geometria e
gestão idênticas. Se os dois tocarem 1R na mesma proporção, o indicador não tem
informação direcional, por mais bonita que esteja a curva de capital.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from b3setups.bars import Bar, split_sessions, validate
from b3setups.contracts import CONTRACTS, CostModel, cents_to_brl
from b3setups.data import load_csv, synthetic_sessions
from b3setups.engine import ExecConfig, Trade, run
from b3setups.placebo import calibrate
from b3setups.replay import walk_forward
from b3setups.setups import LONG, SHORT, ConfluenciaSinal, Entry, Plan, Setup
from b3setups.stats import bootstrap_mean_ci, session_pnl, summarise_positions

REWARD = 2.0
PARTIAL_R = 1.0
CONTRACTS_N = 2


def strategy(min_atr: float = 1.0, threshold: float = 45.0,
             confluence_exit: bool = False) -> ConfluenciaSinal:
    """Medido: a saída antecipada por perda de confluência PIORA o resultado.

    Ela tira a posição antes de o 1R ou o stop resolverem, pagando o custo
    inteiro por um trade que nunca chegou a ser decidido. Desligá-la levou o
    verde de 41,5% para 48,3% e a sangria de -4,79 para -4,06 por posição.
    Quem decide agora é a geometria: 1R, stop, ou o fim do pregão.
    """

    return ConfluenciaSinal(
        threshold=threshold, swing_lookback=5, min_risk_ticks=2,
        max_risk_ticks=60, min_atr=min_atr, reward_r=REWARD,
        exit_on_confluence_loss=confluence_exit,
    )


def exec_cfg() -> ExecConfig:
    """Alvo 2R, metade na mesa em 1R, e o stop vai ao zero junto com a parcial."""
    return ExecConfig(
        target_r=REWARD, contracts=CONTRACTS_N,
        partial_at_r=PARTIAL_R, partial_fraction=0.5,
        breakeven_at_r=PARTIAL_R,
    )


class RandomEntry(Setup):
    """Controle: mesma geometria, mesma gestão, direção jogada na moeda.

    A frequência é casada com a do sinal para que os dois vejam o mesmo número
    de oportunidades e a comparação não dependa de tamanho de amostra.
    """

    def __init__(self, rate: float, min_atr: float = 1.0, seed: int = 4242):
        self.rate = rate
        self.min_atr = min_atr
        self.seed = seed
        self.name = f"aleatório({rate:.3f})"

    def plan(self, bars: list[Bar], contract) -> Plan:
        from b3setups import indicators as ind

        p = Plan.blank(len(bars))
        a = ind.atr(bars, 14)
        rng = random.Random(self.seed + bars[0].ts.toordinal())
        for i in range(5, len(bars)):
            av = a[i]
            if av is None or av <= 0 or rng.random() >= self.rate:
                continue
            side = LONG if rng.random() < 0.5 else SHORT
            ref = bars[i].close
            risk = max(self.min_atr * av, contract.tick_size * 2)
            stop = ref - risk if side == LONG else ref + risk
            p.entries[i] = Entry(side, None, stop, valid_bars=1)
        return p


def outcomes(trades: list[Trade]) -> dict:
    """Classifica cada POSIÇÃO pelos três desfechos possíveis."""
    groups: dict[tuple, list[Trade]] = {}
    for t in trades:
        groups.setdefault((t.session, t.position_id), []).append(t)
    reached = to_target = 0
    stopped = early_exit = timed_out = 0
    for legs in groups.values():
        if any(l.reason == "partial" for l in legs):
            reached += 1
            if any(l.reason == "target" for l in legs):
                to_target += 1
        else:
            # Never reached 1R. HOW it died matters: a full stop is -1R, while
            # a confluence exit or the closing bell is usually a scratch, and
            # folding them together would overstate the losses.
            last = legs[-1].reason
            if last in ("stop", "breakeven"):
                stopped += 1
            elif last == "signal":
                early_exit += 1
            else:
                timed_out += 1
    n = len(groups)
    return {
        "n": n,
        "reached1R": reached,
        "toTarget": to_target,
        "stopped": stopped,
        "earlyExit": early_exit,
        "timedOut": timed_out,
        "pReach": reached / n if n else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--csv", type=Path)
    g.add_argument("--synthetic", action="store_true")
    ap.add_argument("--contract", default="WIN", choices=sorted(CONTRACTS))
    ap.add_argument("--sessions", type=int, default=250)
    ap.add_argument("--seed", type=int, default=31415)
    ap.add_argument("--min-atr", type=float, default=1.0)
    ap.add_argument("--threshold", type=float, default=45.0)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--placebo", type=int, default=20)
    args = ap.parse_args()

    contract = CONTRACTS[args.contract]
    costs = CostModel()

    if args.synthetic:
        sessions = synthetic_sessions(contract, n_sessions=args.sessions, seed=args.seed,
                                      bars_per_session=108, bar_sd_ticks=24.0)
        source = f"SÉRIE DE CONTROLE SEM VANTAGEM (seed {args.seed})"
    else:
        bars = load_csv(args.csv)
        bad = validate(bars)
        if bad:
            print("Dados inconsistentes — execução recusada:", file=sys.stderr)
            for b in bad:
                print("  -", b, file=sys.stderr)
            return 2
        sessions = split_sessions(bars)
        source = str(args.csv)
    if not sessions:
        print("Nenhuma sessão utilizável.", file=sys.stderr)
        return 2

    setup = strategy(args.min_atr, args.threshold)
    cfg = exec_cfg()
    trades = run(sessions, setup, contract, costs, cfg)
    oc = outcomes(trades)
    st = summarise_positions("sinal", trades)

    print(f"\nESTRATÉGIA 2R · parcial em 1R · stop ao zero na parcial")
    print(f"{'=' * 66}")
    print(f"fonte            {source}")
    print(f"sessões          {len(sessions)}")
    print(f"config           {setup.name}  ·  {CONTRACTS_N} contratos")
    print(f"custo            {cents_to_brl(costs.total_round_trip_cents(contract, 1))}/contrato por ida e volta")

    print(f"\nDESFECHOS DAS {oc['n']} POSIÇÕES")
    print(f"{'-' * 66}")
    if oc["n"]:
        part_be = oc["reached1R"] - oc["toTarget"]
        rows = [
            ("stop antes de 1R", oc["stopped"], "-1,0R"),
            ("saiu por perder confluência", oc["earlyExit"], "parcial"),
            ("fim do pregão antes de 1R", oc["timedOut"], "parcial"),
            ("parcial e depois zero a zero", part_be, "+0,5R"),
            ("parcial e depois 2R", oc["toTarget"], "+1,5R"),
        ]
        for label, k, val in rows:
            print(f"  {label:<30} {k:>6}  {100*k/oc['n']:>5.1f}%   {val}")
        print(f"  {'-' * 52}")
        green = st.wins
        red = st.losses
        print(f"  posições no verde {green} x {red} no vermelho "
              f"({100*green/oc['n']:.1f}% contra {100*red/oc['n']:.1f}%)")

    print(f"\nO TESTE: o sinal empurra o toque em 1R acima de 50%?")
    print(f"{'-' * 66}")
    print("  gestão idêntica nos dois lados: a saída por confluência é desligada")
    print("  aqui, senão o teste mediria a saída em vez da entrada.\n")
    fair_setup = strategy(args.min_atr, args.threshold, confluence_exit=False)
    fair = outcomes(run(sessions, fair_setup, contract, costs, cfg))
    rate = fair["n"] / max(1, sum(len(s) for s in sessions))
    ctrl_all = []
    for k in range(5):
        ctrl = RandomEntry(rate, args.min_atr, seed=1000 + k * 977)
        ctrl_all.append(outcomes(run(sessions, ctrl, contract, costs, cfg)))
    cn = sum(c["n"] for c in ctrl_all)
    creach = sum(c["reached1R"] for c in ctrl_all)
    p_ctrl = creach / cn if cn else 0.0
    print(f"  sinal      {100*fair['pReach']:>5.1f}%  ({fair['reached1R']} de {fair['n']})")
    print(f"  aleatório  {100*p_ctrl:>5.1f}%  ({creach} de {cn}, 5 sementes)")
    print(f"  teoria     50.0%  — distâncias iguais, cara ou coroa")
    edge = 100 * (fair["pReach"] - p_ctrl)
    se = 100 * ((fair["pReach"] * (1 - fair["pReach"]) / max(1, fair["n"])) ** 0.5)
    print(f"  diferença  {edge:+.1f} pp   (1 erro padrão do sinal = {se:.1f} pp)")
    if abs(edge) < 2 * se:
        print("  -> dentro do ruído. O sinal NÃO demonstra informação direcional aqui.")
    else:
        print("  -> fora do ruído. Vale investigar em dado real.")

    print(f"\nDINHEIRO (por contrato, custos cobrados)")
    print(f"{'-' * 66}")
    per = [x / CONTRACTS_N for x in session_pnl(trades, sessions)]
    mean, lo, hi = bootstrap_mean_ci(per, n_boot=1500)
    print(f"  expectativa/posição   {cents_to_brl(round(st.expectancy_cents / CONTRACTS_N))}")
    print(f"  resultado total       {cents_to_brl(round(st.total_cents / CONTRACTS_N))}")
    print(f"  por sessão            {cents_to_brl(round(mean))}   "
          f"IC 95% [{cents_to_brl(round(lo))}, {cents_to_brl(round(hi))}]")
    if lo <= 0 <= hi:
        print("  -> o intervalo contém zero: não há resultado demonstrável")

    print(f"\nWALK-FORWARD ({args.folds} blocos cronológicos)")
    print(f"{'-' * 66}")
    folds = walk_forward(sessions, setup, contract, costs, args.folds, REWARD)
    pos = 0
    for f in folds:
        if f.total_cents > 0:
            pos += 1
        print(f"  {f.name:<26} {f.n_trades:>5} trades  "
              f"{cents_to_brl(round(f.total_cents / CONTRACTS_N)):>11}")
    print(f"  blocos positivos: {pos}/{len(folds)}")

    if args.placebo > 0:
        print(f"\nNULO CALIBRADO ({args.placebo} séries sem vantagem)")
        print(f"{'-' * 66}")
        fam = [strategy(args.min_atr, th) for th in (35.0, 45.0, 55.0)]
        cal = calibrate(fam, [REWARD], contract, costs,
                        n_series=args.placebo, n_sessions=len(sessions), contracts=CONTRACTS_N)
        obs = sum(session_pnl(trades, sessions)) / len(sessions)
        pv = cal.p_value(obs)
        print(f"  mediana do falso lucro  {cents_to_brl(round(cal.median / CONTRACTS_N))}/sessão")
        print(f"  observado               {cents_to_brl(round(obs / CONTRACTS_N))}/sessão")
        print(f"  p-valor                 {pv:.4f}")
        print("  " + ("-> acima do que a busca fabrica sozinha" if pv < 0.05
                      else "-> INDISTINGUÍVEL de dado sem vantagem"))

    if args.synthetic:
        print("\nRodou em random walk. O ~50% de toque em 1R é a geometria funcionando")
        print("como deve; o dinheiro negativo é o custo. Só dado real de WIN pode dizer")
        print("se o sinal empurra esse 50% para cima.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
