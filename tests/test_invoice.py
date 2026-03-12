from datetime import date
from decimal import Decimal

from billing.invoice import generate_invoice

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 1, 31)

PRICE_BOOK = {
    "parcel.standard": Decimal("4.90"),
    "parcel.express": Decimal("9.50"),
    "storage.day": Decimal("0.35"),
}


def test_invoice_totals_line_items():
    usage = {"parcel.standard": 120, "parcel.express": 8}
    invoice = generate_invoice("acct_001", usage, PRICE_BOOK, PERIOD_START, PERIOD_END)
    assert len(invoice.line_items) == 2
    assert invoice.total == Decimal("664.00")


def test_invoice_rounds_half_up():
    usage = {"storage.day": 3.5}  # 3.5 * 0.35 = 1.225 -> 1.23
    invoice = generate_invoice("acct_002", usage, PRICE_BOOK, PERIOD_START, PERIOD_END)
    assert invoice.line_items[0].amount == Decimal("1.23")


def test_unknown_meter_raises():
    try:
        generate_invoice("acct_003", {"parcel.drone": 1}, PRICE_BOOK, PERIOD_START, PERIOD_END)
    except KeyError as exc:
        assert "parcel.drone" in str(exc)
    else:
        raise AssertionError("expected KeyError for unknown meter")
