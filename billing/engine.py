"""Monthly billing run orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from billing.invoice import Invoice, generate_invoice
from billing.usage import UsageRecord, aggregate_usage

logger = logging.getLogger(__name__)


@dataclass
class BillingRunResult:
    period_start: date
    period_end: date
    invoices: list[Invoice]
    skipped_accounts: list[str]


class BillingEngine:
    """Runs the monthly billing cycle for all active accounts.

    Usage events arrive from the data-pipeline warehouse export; prices come
    from the account's contracted price book.
    """

    def __init__(self, price_books: dict[str, dict[str, Decimal]], minimum_invoice: Decimal = Decimal("1.00")):
        self._price_books = price_books
        self._minimum_invoice = minimum_invoice

    def run_monthly(self, records: list[UsageRecord], period_start: date, period_end: date) -> BillingRunResult:
        usage_by_account = aggregate_usage(records, period_start, period_end)
        invoices: list[Invoice] = []
        skipped: list[str] = []

        for account_id, usage in sorted(usage_by_account.items()):
            price_book = self._price_books.get(account_id) or self._price_books.get("default")
            if price_book is None:
                logger.warning("no price book for account %s, skipping", account_id)
                skipped.append(account_id)
                continue
            invoice = generate_invoice(account_id, usage, price_book, period_start, period_end)
            if invoice.total < self._minimum_invoice:
                logger.info("invoice below minimum for %s (%s), carrying over", account_id, invoice.total)
                skipped.append(account_id)
                continue
            invoices.append(invoice)

        logger.info("billing run complete: %d invoices, %d skipped", len(invoices), len(skipped))
        return BillingRunResult(period_start, period_end, invoices, skipped)
