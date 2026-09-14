"""Contract specifications and the B3 day-trade cost model.

Money never touches a float here. Prices are carried as integer *tick indices*
(price / tick_size, rounded to the grid) and P&L is computed in integer
centavos, following ENGINEERING_PRINCIPLES.md §4.1 ("inteiro em centavos").

Cost defaults are declared assumptions, not quotes. B3 emolumentos change by
circular and brokerage varies by broker; both are constructor arguments so a
run can state exactly what it assumed. Slippage is the dominant term for
short-horizon setups and is expressed in ticks per side.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Contract:
    """A B3 mini futures contract.

    Attributes:
        symbol: Root ticker, e.g. "WIN" or "WDO".
        tick_size: Minimum price increment, in index points (WIN) or
            BRL-per-USD1000 points (WDO).
        tick_cents: Financial value of one tick, per contract, in centavos.
            WIN: 5 points x R$0.20 = R$1.00 = 100 centavos.
            WDO: 0.5 points x R$10.00 = R$5.00 = 500 centavos.
    """

    symbol: str
    tick_size: float
    tick_cents: int

    def to_ticks(self, price: float) -> int:
        """Snap a quoted price onto the integer tick grid."""
        return round(price / self.tick_size)

    def to_price(self, ticks: int) -> float:
        """Inverse of :meth:`to_ticks`, for display only."""
        return ticks * self.tick_size

    def points(self, ticks: int) -> float:
        """Convert a tick delta to index points."""
        return ticks * self.tick_size


WIN = Contract(symbol="WIN", tick_size=5.0, tick_cents=100)
WDO = Contract(symbol="WDO", tick_size=0.5, tick_cents=500)

CONTRACTS: dict[str, Contract] = {"WIN": WIN, "WDO": WDO}


@dataclass(frozen=True)
class CostModel:
    """Round-trip friction, in centavos per contract unless noted.

    Attributes:
        brokerage_cents_per_side: Corretagem. Several Brazilian brokers charge
            zero on minis; default reflects that, deliberately favourable.
        exchange_cents_per_side: Emolumentos + registro, day-trade rate.
        slippage_ticks_per_side: Execution shortfall. One tick per side is the
            realistic floor for a market or stop order in WIN; this term
            usually dwarfs the explicit fees.
    """

    brokerage_cents_per_side: int = 0
    exchange_cents_per_side: int = 27
    slippage_ticks_per_side: int = 1

    def fixed_round_trip_cents(self, contracts: int) -> int:
        """Fees that do not depend on the contract's tick value."""
        per_side = self.brokerage_cents_per_side + self.exchange_cents_per_side
        return 2 * per_side * contracts

    def slippage_round_trip_cents(self, contract: Contract, contracts: int) -> int:
        """Slippage expressed in money, via the contract's tick value."""
        return 2 * self.slippage_ticks_per_side * contract.tick_cents * contracts

    def total_round_trip_cents(self, contract: Contract, contracts: int) -> int:
        return self.fixed_round_trip_cents(contracts) + self.slippage_round_trip_cents(
            contract, contracts
        )


def cents_to_brl(cents: int) -> Decimal:
    """Render integer centavos as BRL with two decimals."""
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
