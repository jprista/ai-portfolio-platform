"""Brazilian business-day calendar — ANBIMA national holidays.

Implements ENGINE_METHODOLOGY §2: DU/252 day counting. Movable feasts via
the anonymous Gregorian Easter algorithm.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def easter(year: int) -> date:
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


@lru_cache(maxsize=None)
def holidays(year: int) -> frozenset[date]:
    e = easter(year)
    hs = {
        date(year, 1, 1),    # Confraternização Universal
        e - timedelta(days=48),  # Carnaval (segunda)
        e - timedelta(days=47),  # Carnaval (terça)
        e - timedelta(days=2),   # Sexta-feira Santa
        date(year, 4, 21),   # Tiradentes
        date(year, 5, 1),    # Dia do Trabalho
        e + timedelta(days=60),  # Corpus Christi
        date(year, 9, 7),    # Independência
        date(year, 10, 12),  # Nossa Senhora Aparecida
        date(year, 11, 2),   # Finados
        date(year, 11, 15),  # Proclamação da República
        date(year, 12, 25),  # Natal
    }
    if year >= 2024:
        hs.add(date(year, 11, 20))  # Consciência Negra (nacional desde 2024)
    return frozenset(hs)


def is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in holidays(d.year)


def business_days_between(start: date, end: date) -> int:
    """Count business days in (start, end] — accrual convention (§2)."""
    if end <= start:
        return 0
    n = 0
    d = start
    while d < end:
        d += timedelta(days=1)
        if is_business_day(d):
            n += 1
    return n


def next_business_day(d: date) -> date:
    while not is_business_day(d):
        d += timedelta(days=1)
    return d
