"""Invoice generation from aggregated usage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class LineItem:
    meter: str
    quantity: float
    unit_price: Decimal
    amount: Decimal


@dataclass
class Invoice:
    account_id: str
    period_start: date
    period_end: date
    currency: str = "EUR"
    line_items: list[LineItem] = field(default_factory=list)
    status: str = "draft"

    @property
    def total(self) -> Decimal:
        return sum((item.amount for item in self.line_items), Decimal("0.00"))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_invoice(
    account_id: str,
    usage: dict[str, float],
    price_book: dict[str, Decimal],
    period_start: date,
    period_end: date,
) -> Invoice:
    """Build a draft invoice for one account from its aggregated usage."""
    invoice = Invoice(account_id=account_id, period_start=period_start, period_end=period_end)
    for meter, quantity in sorted(usage.items()):
        if meter not in price_book:
            raise KeyError(f"meter {meter!r} missing from price book")
        unit_price = price_book[meter]
        amount = _round_money(unit_price * Decimal(str(quantity)))
        invoice.line_items.append(
            LineItem(meter=meter, quantity=quantity, unit_price=unit_price, amount=amount)
        )
    return invoice
