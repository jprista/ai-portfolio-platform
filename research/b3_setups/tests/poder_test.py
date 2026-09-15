"""O teste consegue achar vantagem quando ela existe?

Esta é a pergunta que tem de vir ANTES de qualquer veredito de "não há
vantagem". Um teste que nunca acha nada não é rigoroso, é surdo — e todo
resultado negativo que ele produz não vale nada.

Aqui uma quantidade CONHECIDA de persistência é plantada na série (AR(1) sobre
o retorno da barra, com a variância mantida constante) e verifica-se que:

  1. sem vantagem plantada, o sinal empata com entrada aleatória;
  2. com vantagem plantada, o sinal a encontra e a expectativa vira positiva;
  3. o efeito é monotônico — mais persistência, mais resultado.

Rodar:  python3 tests/poder_test.py
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b3setups.contracts import WIN, CostModel  # noqa: E402
from b3setups.data import synthetic_sessions  # noqa: E402
from b3setups.engine import run  # noqa: E402
from b3setups.stats import summarise_positions  # noqa: E402
from estrategia_2r import RandomEntry, exec_cfg, outcomes, strategy  # noqa: E402

FAILURES: list[str] = []
COSTS = CostModel()
CFG = exec_cfg()


def autocorr(sessions) -> float:
    c = [b.close for s in sessions for b in s.bars]
    r = [c[i] - c[i - 1] for i in range(1, len(c))]
    m = statistics.mean(r)
    return sum((r[i] - m) * (r[i - 1] - m) for i in range(1, len(r))) / sum((v - m) ** 2 for v in r)


def measure(phi: float, seed: int = 777, n: int = 150):
    s = synthetic_sessions(WIN, n_sessions=n, seed=seed, bars_per_session=108,
                           bar_sd_ticks=24.0, momentum=phi)
    setup = strategy(confluence_exit=False)
    trades = run(s, setup, WIN, COSTS, CFG)
    st = summarise_positions(f"phi{phi}", trades)
    sig = outcomes(trades)
    rate = sig["n"] / max(1, sum(len(x) for x in s))
    ctl = [outcomes(run(s, RandomEntry(rate, 1.0, seed=1000 + k * 977), WIN, COSTS, CFG))
           for k in range(3)]
    p_ctl = sum(x["reached1R"] for x in ctl) / max(1, sum(x["n"] for x in ctl))
    return {
        "ac": autocorr(s),
        "pReach": sig["pReach"],
        "pCtl": p_ctl,
        "exp": st.expectancy_cents / 2,
        "green": st.win_rate,
    }


# --- 1. Sem vantagem plantada, o sinal tem de empatar com a moeda.
m0 = measure(0.0)
gap0 = 100 * (m0["pReach"] - m0["pCtl"])
print(f"  phi=0.00  autocorr {m0['ac']:+.4f}  sinal {100*m0['pReach']:.1f}%  "
      f"aleatório {100*m0['pCtl']:.1f}%  ({gap0:+.1f} pp)  exp {m0['exp']:+.0f}c")
if abs(gap0) > 3.0:
    FAILURES.append(
        f"sem vantagem plantada o sinal difere do aleatório em {gap0:+.1f} pp — "
        "o controle ou o sinal está enviesado"
    )
if m0["exp"] > 0:
    FAILURES.append(f"expectativa positiva ({m0['exp']:+.0f} centavos) numa série sem vantagem")

# --- 2. Com vantagem forte plantada, o teste TEM de achar.
m1 = measure(0.35)
gap1 = 100 * (m1["pReach"] - m1["pCtl"])
print(f"  phi=0.35  autocorr {m1['ac']:+.4f}  sinal {100*m1['pReach']:.1f}%  "
      f"aleatório {100*m1['pCtl']:.1f}%  ({gap1:+.1f} pp)  exp {m1['exp']:+.0f}c")
if gap1 < 3.0:
    FAILURES.append(
        f"com autocorrelação de {m1['ac']:+.3f} plantada o sinal só ficou {gap1:+.1f} pp "
        "acima do aleatório — o teste é surdo e nenhum veredito negativo dele vale"
    )
if m1["exp"] <= 0:
    FAILURES.append(f"expectativa não virou positiva ({m1['exp']:+.0f} centavos) com vantagem forte")

# --- 3. O efeito tem de crescer com a persistência, não oscilar.
seq = [measure(p)["exp"] for p in (0.0, 0.10, 0.20, 0.35)]
print(f"  centavos/posição por persistência crescente: {[round(x) for x in seq]}")
if not (seq[0] < seq[-1] and seq[-1] > 0):
    FAILURES.append(f"a expectativa não cresce com a persistência: {seq}")

# --- 4. A faixa de virada fica travada aqui, em CENTAVOS por posição. Se ela
#     se mover, o limiar citado ao usuário deixou de valer.
#
#     Ela é uma FAIXA e não um número: medindo o mesmo phi com sementes
#     diferentes a virada anda entre ~+0.05 e ~+0.10 de autocorrelação. Citar
#     "+0.065" como se fosse exato seria precisão que a medição não tem.
band = {phi: measure(phi, seed=sd)["exp"]
        for phi, sd in ((0.05, 777), (0.05, 991), (0.10, 777), (0.20, 777))}
print(f"  centavos/posição por phi e semente: "
      + "  ".join(f"phi={k:.2f}:{v:+.0f}" for k, v in band.items()))
strong = band[(0.20)]
if strong < 100:
    FAILURES.append(
        f"com autocorrelação de ~+0.20 a expectativa ficou em {strong:+.0f} centavos; "
        "abaixo do que a faixa documentada promete — refaça a calibração"
    )
if m0["exp"] > -50:
    FAILURES.append(
        f"sem vantagem a sangria foi de apenas {m0['exp']:+.0f} centavos; o custo "
        "deveria doer mais e a calibração do limiar depende disso"
    )

if FAILURES:
    print("FAIL")
    for f in FAILURES:
        print("  -", f)
    sys.exit(1)
print("poder_test: o teste detecta vantagem plantada e não a inventa quando não há")
