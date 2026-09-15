"""Loading real bars, and generating a calibrated no-edge control series.

Two jobs:

1. ``load_csv`` reads the intraday exports people actually have — Profit
   (Nelogica), MetaTrader 5, or a plain ISO CSV — sniffing the delimiter,
   the decimal separator and the date layout instead of demanding one format.

2. ``synthetic_sessions`` builds a driftless random walk on the contract's tick
   grid, with WIN-like intraday volatility and a U-shaped volume curve. It
   contains **no edge by construction**. Running the whole setup family over it
   measures how much apparent performance the search procedure manufactures
   from noise alone — the empirical form of the data-snooping critique.

The control series is never a substitute for market data and no conclusion
about a setup's real-world merit may be drawn from it.
"""
from __future__ import annotations

import csv
import io
import random
import unicodedata
from datetime import date, datetime, time, timedelta
from pathlib import Path

from .bars import Bar, Session, split_sessions
from .contracts import Contract

_OPEN = {"open", "abertura", "abert"}
_HIGH = {"high", "maxima", "max", "maxima"}
_LOW = {"low", "minima", "min"}
_CLOSE = {"close", "fechamento", "fech", "ultimo", "last"}
_VOL = {"volume", "vol", "tickvol", "quantidade", "qtd", "negocios"}
_DATE = {"date", "data"}
_TIME = {"time", "hora", "horario"}
_DATETIME = {"datetime", "timestamp", "datahora"}

_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d", "%Y.%m.%d", "%d-%m-%Y", "%m/%d/%Y")
_TIME_FORMATS = ("%H:%M:%S", "%H:%M", "%H:%M:%S.%f")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())


def _to_float(raw: str) -> float:
    s = raw.strip().replace(" ", "").replace("\xa0", "")
    if not s:
        return 0.0
    if "," in s and "." in s:
        # 1.234,56 (pt-BR) vs 1,234.56 (en) — the rightmost separator decides.
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _parse_dt(date_raw: str, time_raw: str | None) -> datetime:
    d_txt = date_raw.strip()
    if time_raw is None:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                    "%d/%m/%Y %H:%M", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(d_txt, fmt)
            except ValueError:
                continue
        return datetime.fromisoformat(d_txt)
    d_val: date | None = None
    for fmt in _DATE_FORMATS:
        try:
            d_val = datetime.strptime(d_txt, fmt).date()
            break
        except ValueError:
            continue
    if d_val is None:
        raise ValueError(f"unrecognised date: {date_raw!r}")
    t_val: time | None = None
    for fmt in _TIME_FORMATS:
        try:
            t_val = datetime.strptime(time_raw.strip(), fmt).time()
            break
        except ValueError:
            continue
    if t_val is None:
        raise ValueError(f"unrecognised time: {time_raw!r}")
    return datetime.combine(d_val, t_val)


def load_csv(path: str | Path) -> list[Bar]:
    """Read an intraday OHLCV export into bars, sorted by timestamp.

    Raises ValueError naming the offending header when a required column is
    missing — a silent wrong-column read is far worse than a hard failure.
    """
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    sample = "\n".join(text.splitlines()[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        delim = dialect.delimiter
    except csv.Error:
        delim = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [r for r in reader if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise ValueError(f"{path}: fewer than two non-empty rows")

    header = [_norm(h) for h in rows[0]]
    idx: dict[str, int] = {}
    for i, h in enumerate(header):
        h = h.strip("<>")
        for key, names in (
            ("open", _OPEN), ("high", _HIGH), ("low", _LOW), ("close", _CLOSE),
            ("volume", _VOL), ("date", _DATE), ("time", _TIME), ("datetime", _DATETIME),
        ):
            if h in names and key not in idx:
                idx[key] = i

    missing = [k for k in ("open", "high", "low", "close") if k not in idx]
    if missing:
        raise ValueError(f"{path}: missing column(s) {missing}; header was {rows[0]}")
    if "datetime" not in idx and "date" not in idx:
        raise ValueError(f"{path}: no date or datetime column; header was {rows[0]}")

    bars: list[Bar] = []
    for line_no, row in enumerate(rows[1:], start=2):
        if len(row) <= max(idx.values()):
            continue
        try:
            if "datetime" in idx:
                ts = _parse_dt(row[idx["datetime"]], None)
            else:
                ts = _parse_dt(row[idx["date"]], row[idx["time"]] if "time" in idx else "00:00:00")
            bars.append(
                Bar(
                    ts=ts,
                    open=_to_float(row[idx["open"]]),
                    high=_to_float(row[idx["high"]]),
                    low=_to_float(row[idx["low"]]),
                    close=_to_float(row[idx["close"]]),
                    volume=_to_float(row[idx["volume"]]) if "volume" in idx else 0.0,
                )
            )
        except (ValueError, IndexError) as exc:
            raise ValueError(f"{path}: line {line_no}: {exc}") from exc

    bars.sort(key=lambda b: b.ts)
    return bars


def load_sessions(path: str | Path, min_bars: int = 20) -> list[Session]:
    return split_sessions(load_csv(path), min_bars=min_bars)


# --------------------------------------------------------------------------
# No-edge control series
# --------------------------------------------------------------------------


def synthetic_sessions(
    contract: Contract,
    n_sessions: int = 250,
    bars_per_session: int = 108,
    start_price: float = 130_000.0,
    bar_sd_ticks: float = 24.0,
    minutes_per_bar: int = 5,
    momentum: float = 0.0,
    substeps: int = 12,
    seed: int = 20260914,
    start_day: date = date(2026, 1, 5),
) -> list[Session]:
    """A driftless tick-grid random walk with WIN-like intraday behaviour.

    Each bar is assembled from ``substeps`` sub-moves so that OHLC is
    internally consistent and the intrabar path is realistic — an OHLC drawn
    independently would make stop and target fills meaningless.

    With ``momentum`` at zero there is no drift and no autocorrelation, so the
    true expected P&L of any strategy here is negative once costs are charged.
    That is the point of the control.

    ``momentum`` injects an AR(1) coefficient into the BAR return series — a KNOWN,
    dialled-in amount of trend persistence. It exists to answer the question
    that has to precede any "no edge" verdict: would this test detect an edge
    if one were there? A test that cannot find a planted edge cannot be trusted
    when it reports none. Variance is held constant as momentum rises, so the
    only thing changing is the predictability, not the volatility.
    """
    rng = random.Random(seed)
    step_sd = bar_sd_ticks / (substeps**0.5)
    # Hold the unconditional variance fixed while phi grows, so the comparison
    # isolates predictability from volatility.
    innov_sd = step_sd * ((1.0 - momentum**2) ** 0.5) if momentum else step_sd
    last_bar_return = 0.0
    price_ticks = contract.to_ticks(start_price)
    sessions: list[Session] = []
    day = start_day

    for _ in range(n_sessions):
        while day.weekday() >= 5:
            day += timedelta(days=1)
        bars: list[Bar] = []
        clock = datetime.combine(day, time(9, 0))
        for b in range(bars_per_session):
            # Momentum is carried BAR to BAR, not step to step. Injecting it at
            # the substep level washes out under aggregation — twelve substeps
            # of AR(1) leave almost no bar-level autocorrelation, and bars are
            # all the indicator can see. The previous bar's return becomes a
            # drift spread across this bar's substeps.
            drift = (momentum * last_bar_return / substeps) if momentum else 0.0
            path = [price_ticks]
            for _ in range(substeps):
                path.append(path[-1] + round(rng.gauss(drift, innov_sd)))
            last_bar_return = float(path[-1] - path[0])
            o, c = path[0], path[-1]
            hi, lo = max(path), min(path)
            # U-shaped session volume: heavy at the open and into the close.
            u = b / max(1, bars_per_session - 1)
            shape = 1.0 + 2.2 * ((u - 0.5) ** 2) * 4.0
            vol = max(1.0, rng.gauss(9000.0 * shape, 1800.0))
            bars.append(
                Bar(
                    ts=clock,
                    open=contract.to_price(o),
                    high=contract.to_price(hi),
                    low=contract.to_price(lo),
                    close=contract.to_price(c),
                    volume=round(vol),
                )
            )
            price_ticks = c
            clock += timedelta(minutes=minutes_per_bar)
        sessions.append(Session(day=day, bars=bars))
        day += timedelta(days=1)
    return sessions
