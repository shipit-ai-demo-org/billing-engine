"""Invoice generation from aggregated usage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal


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
    """Round to cents with banker's rounding (round half to even).

    HALF_UP systematically rounded x.xx5 amounts in our favour, which adds up
    across millions of parcel line items and drew flags in the FY25 revenue
    audit. HALF_EVEN is statistically unbiased and matches what the general
    ledger and payments-service use.
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def proration_factor(period_start: date, period_end: date, activated_on: date | None) -> Decimal:
    """Fraction of the billing period the account was active.

    Accounts activated mid-month previously paid full fixed-meter charges
    (CARGO-2841); fixed meters are now prorated by active days.
    """
    if activated_on is None or activated_on <= period_start:
        return Decimal("1")
    period_days = (period_end - period_start).days + 1
    active_days = (period_end - activated_on).days + 1
    if active_days <= 0:
        return Decimal("0")
    return Decimal(active_days) / Decimal(period_days)


def generate_invoice(
    account_id: str,
    usage: dict[str, float],
    price_book: dict[str, Decimal],
    period_start: date,
    period_end: date,
    activated_on: date | None = None,
) -> Invoice:
    """Build a draft invoice for one account from its aggregated usage."""
    factor = proration_factor(period_start, period_end, activated_on)
    invoice = Invoice(account_id=account_id, period_start=period_start, period_end=period_end)
    for meter, quantity in sorted(usage.items()):
        if meter not in price_book:
            raise KeyError(f"meter {meter!r} missing from price book")
        unit_price = price_book[meter]
        amount = unit_price * Decimal(str(quantity))
        if meter.startswith("subscription."):
            amount *= factor
        invoice.line_items.append(
            LineItem(meter=meter, quantity=quantity, unit_price=unit_price, amount=_round_money(amount))
        )
    return invoice
