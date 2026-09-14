"""Text rendering of a sweep. Money is always shown via Decimal centavos."""
from __future__ import annotations

from .contracts import Contract, CostModel, cents_to_brl
from .stats import Stats


def _bar_title(text: str, width: int = 96) -> str:
    return f"\n{text}\n{'=' * min(width, max(len(text), 40))}"


def header(
    source: str,
    contract: Contract,
    costs: CostModel,
    n_sessions: int,
    n_bars: int,
    n_variants: int,
) -> str:
    rt = cents_to_brl(costs.total_round_trip_cents(contract, 1))
    lines = [
        _bar_title(f"BACKTEST — {contract.symbol} — {source}"),
        f"sessions           {n_sessions}",
        f"bars               {n_bars}",
        f"variants tested    {n_variants}",
        f"tick               {contract.tick_size:g} pts = {cents_to_brl(contract.tick_cents)}",
        f"cost round trip    {rt}/contract "
        f"(corretagem {cents_to_brl(costs.brokerage_cents_per_side)}/side, "
        f"emolumentos {cents_to_brl(costs.exchange_cents_per_side)}/side, "
        f"slippage {costs.slippage_ticks_per_side} tick/side)",
    ]
    return "\n".join(lines)


def table(rows: list[Stats], contract: Contract, limit: int = 15) -> str:
    ordered = sorted(rows, key=lambda s: s.total_cents, reverse=True)[:limit]
    head = (
        f"{'variant':<40} {'trades':>7} {'win%':>6} {'exp/trade':>11} "
        f"{'total':>13} {'PF':>6} {'maxDD':>12} {'Sharpe':>7}"
    )
    out = [head, "-" * len(head)]
    for s in ordered:
        pf = "inf" if s.profit_factor == float("inf") else f"{s.profit_factor:.2f}"
        out.append(
            f"{s.name[:40]:<40} {s.n_trades:>7} {100 * s.win_rate:>5.1f}% "
            f"{cents_to_brl(round(s.expectancy_cents)):>11} "
            f"{cents_to_brl(s.total_cents):>13} {pf:>6} "
            f"{cents_to_brl(s.max_drawdown_cents):>12} {s.sharpe_sessions:>7.2f}"
        )
    return "\n".join(out)


def cost_analysis(rows: list[Stats], contract: Contract) -> str:
    """How much of the gross the friction ate — usually the real story."""
    gross = sum(s.gross_cents for s in rows)
    cost = sum(s.cost_cents for s in rows)
    trades = sum(s.n_trades for s in rows)
    lines = [_bar_title("COST DRAG (all variants pooled)")]
    lines.append(f"trades                 {trades}")
    lines.append(f"gross P&L              {cents_to_brl(gross)}")
    lines.append(f"costs                  {cents_to_brl(cost)}")
    lines.append(f"net P&L                {cents_to_brl(gross - cost)}")
    if trades:
        lines.append(f"cost per trade         {cents_to_brl(round(cost / trades))}")
    profitable_gross = sum(1 for s in rows if s.gross_cents > 0)
    profitable_net = sum(1 for s in rows if s.total_cents > 0)
    lines.append(
        f"variants positive      {profitable_gross}/{len(rows)} before costs, "
        f"{profitable_net}/{len(rows)} after costs"
    )
    return "\n".join(lines)


def significance(
    best_name: str,
    p_value: float,
    n_variants: int,
    sr: float,
    sr0: float,
    dsr_prob: float,
    boot: tuple[float, float, float],
    naive_best: str,
) -> str:
    mean, lo, hi = boot
    lines = [_bar_title("MULTIPLE-TESTING CORRECTION")]
    lines.append(f"naive winner                  {naive_best}")
    lines.append(f"variants searched             {n_variants}")
    lines.append("")
    lines.append("White's Reality Check — H0: no variant in the family has positive expected P&L")
    lines.append(f"  best variant                {best_name}")
    lines.append(f"  family p-value              {p_value:.4f}")
    verdict = (
        "REJECT H0 — the family contains something that is not noise"
        if p_value < 0.05
        else "CANNOT REJECT H0 — the best result is consistent with pure search luck"
    )
    lines.append(f"  verdict                     {verdict}")
    lines.append("")
    lines.append("Deflated Sharpe Ratio (Bailey & Lopez de Prado)")
    lines.append(f"  observed SR (per session)   {sr:.4f}")
    lines.append(f"  expected max SR under H0    {sr0:.4f}   (from {n_variants} trials)")
    lines.append(f"  P(true SR > 0)              {dsr_prob:.4f}")
    lines.append("")
    lines.append("Stationary block bootstrap on the best variant's per-session P&L")
    lines.append(
        f"  mean/session                {cents_to_brl(round(mean))}   "
        f"95% CI [{cents_to_brl(round(lo))}, {cents_to_brl(round(hi))}]"
    )
    if lo <= 0 <= hi:
        lines.append("  the interval contains zero — no demonstrable edge")
    return "\n".join(lines)


def placebo_block(cal, observed_cents: float) -> str:
    """Render the placebo null and where the real result falls inside it."""
    from .contracts import cents_to_brl
    from .placebo import PlaceboResult

    assert isinstance(cal, PlaceboResult)
    p = cal.p_value(observed_cents)
    lines = [_bar_title("PLACEBO NULL — the benchmark that actually matters")]
    lines.append(
        f"identical family ({cal.family_size} variants), engine and costs, run over "
        f"{cal.n_series} series"
    )
    lines.append(f"of {cal.n_sessions} sessions each that contain NO EDGE by construction.")
    lines.append("")
    lines.append("best-variant mean P&L per session on the no-edge series:")
    lines.append(f"  median                      {cents_to_brl(round(cal.median))}")
    lines.append(f"  90th percentile             {cents_to_brl(round(cal.percentile(0.90)))}")
    lines.append(f"  max                         {cents_to_brl(round(max(cal.best_means)))}")
    lines.append("")
    lines.append(f"observed best on this data    {cents_to_brl(round(observed_cents))}")
    lines.append(f"placebo p-value               {p:.4f}")
    if p < 0.05:
        lines.append("  the result is beyond what the search and the simulator")
        lines.append("  manufacture on their own — worth investigating further")
    else:
        lines.append("  INDISTINGUISHABLE from what this same search produces on")
        lines.append("  data with no edge at all. No evidence of an edge here.")
    return "\n".join(lines)
