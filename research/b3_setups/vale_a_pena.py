#!/usr/bin/env python3
"""Vale a pena? A condição que o mercado precisa satisfazer, medida no seu dado.

    python3 vale_a_pena.py --csv WIN_5min.csv

Este indicador é seguidor de tendência. Ele só ganha dinheiro se o preço tiver
PERSISTÊNCIA de uma barra para a seguinte — se uma barra de alta tornar a
próxima um pouco mais provável de ser de alta. Isso é medível numa linha:
a autocorrelação de defasagem 1 dos retornos de barra.

A calibração ficou assim, plantando persistência conhecida numa série sintética
e medindo o resultado (tests/poder_test.py trava esses números):

    autocorrelação  ~+0.00   ->  perde  (só o custo)
    autocorrelação  ~+0.05   ->  na fronteira
    autocorrelação  ~+0.10   ->  começa a pagar
    autocorrelação  ~+0.20   ->  paga bem

Então a pergunta "vale a pena" vira uma pergunta objetiva e barata: o SEU WIN,
no SEU tempo gráfico, tem autocorrelação acima de ~+0.05?

Ela é medida DENTRO de cada pregão. O salto da noite não é uma barra e
incluí-lo inventaria persistência que o operador não pode capturar.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from b3setups.bars import Session, split_sessions, validate
from b3setups.contracts import CONTRACTS
from b3setups.data import load_csv, synthetic_sessions
from b3setups.resample import resample, sessions_from

FRONTEIRA = 0.05
PAGA = 0.10


def autocorr_intraday(sessions: list[Session], lag: int = 1) -> tuple[float, float, int]:
    """(autocorrelação, erro padrão, n) dos retornos, sem cruzar o pregão."""
    rets: list[float] = []
    for s in sessions:
        c = [b.close for b in s.bars]
        rets.extend(c[i] - c[i - 1] for i in range(1, len(c)))
    n = len(rets)
    if n <= lag + 2:
        return 0.0, 1.0, n
    m = statistics.mean(rets)
    den = sum((v - m) ** 2 for v in rets)
    if den == 0:
        return 0.0, 1.0, n
    num = sum((rets[i] - m) * (rets[i - lag] - m) for i in range(lag, n))
    return num / den, 1.0 / (n**0.5), n


def veredito(ac: float, se: float) -> tuple[str, str]:
    if ac - 2 * se > PAGA:
        return "VALE", "persistência acima do limiar com folga estatística"
    if ac + 2 * se < FRONTEIRA:
        return "NÃO VALE", "persistência abaixo da fronteira com folga estatística"
    return "INCONCLUSIVO", "o intervalo cruza a fronteira — mais histórico decide"


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--csv", type=Path)
    g.add_argument("--synthetic", action="store_true")
    ap.add_argument("--contract", default="WIN", choices=sorted(CONTRACTS))
    ap.add_argument("--momentum", type=float, default=0.0, help="apenas sintético")
    ap.add_argument("--sessions", type=int, default=200)
    args = ap.parse_args()

    contract = CONTRACTS[args.contract]
    if args.synthetic:
        base = synthetic_sessions(contract, n_sessions=args.sessions, bars_per_session=540,
                                  bar_sd_ticks=10.7, minutes_per_bar=1, seed=606061,
                                  momentum=args.momentum)
        flat = [b for s in base for b in s.bars]
        origem = f"sintético (momentum plantado = {args.momentum:g})"
    else:
        bars = load_csv(args.csv)
        bad = validate(bars)
        if bad:
            print("Dados inconsistentes — execução recusada:", file=sys.stderr)
            for b in bad[:10]:
                print("  -", b, file=sys.stderr)
            return 2
        flat = bars
        origem = str(args.csv)

    sessions_all = split_sessions(flat)
    span = ""
    if sessions_all:
        span = f"  ·  {sessions_all[0].day} a {sessions_all[-1].day}"

    print(f"\nVALE A PENA? — {contract.symbol}")
    print("=" * 68)
    print(f"fonte      {origem}")
    print(f"sessões    {len(sessions_all)}{span}")
    print(f"\nA condição: autocorrelação de defasagem 1, medida dentro do pregão.")
    print(f"fronteira ~{FRONTEIRA:+.2f}   começa a pagar ~{PAGA:+.2f}\n")

    head = f"{'tempo gráfico':<16} {'barras':>9} {'autocorr':>10} {'±2 erros':>18} {'veredito':>14}"
    print(head)
    print("-" * len(head))
    best = None
    for minutes in (1, 2, 3, 5, 10, 15):
        sess = sessions_from(resample(flat, minutes))
        if not sess:
            continue
        ac, se, n = autocorr_intraday(sess)
        v, _ = veredito(ac, se)
        lo, hi = ac - 2 * se, ac + 2 * se
        print(f"{minutes:>2} min{'':<10} {n:>9} {ac:>+10.4f}   [{lo:>+7.4f},{hi:>+7.4f}] {v:>14}")
        if best is None or ac > best[1]:
            best = (minutes, ac, se)

    if best:
        minutes, ac, se = best
        v, porque = veredito(ac, se)
        print(f"\n{'=' * 68}")
        print(f"MELHOR TEMPO GRÁFICO PARA ESTE INDICADOR: {minutes} min  (autocorr {ac:+.4f})")
        print(f"VEREDITO: {v} — {porque}")
        if v == "NÃO VALE":
            print("\n  O indicador é seguidor de tendência e este mercado, neste horizonte,")
            print("  não entrega persistência suficiente para pagar o custo. Nenhum ajuste")
            print("  de peso ou de limiar conserta isso — a matéria-prima não está lá.")
        elif v == "VALE":
            print("\n  Condição necessária satisfeita. NÃO é suficiente: rode agora")
            print("  estrategia_2r.py --csv no mesmo arquivo e exija que o toque em 1R")
            print("  supere o controle aleatório e que o placebo devolva p < 0,05.")
        else:
            print("\n  Sem histórico bastante para decidir. Junte mais pregões — o erro")
            print("  padrão cai com a raiz do número de barras.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
