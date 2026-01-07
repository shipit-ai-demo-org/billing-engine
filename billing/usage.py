"""Usage aggregation for billable shipment events."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class UsageRecord:
    """A single billable event emitted by the order pipeline."""

    account_id: str
    meter: str  # e.g. "parcel.standard", "parcel.express", "storage.day"
    quantity: float
    occurred_on: date


def aggregate_usage(records: list[UsageRecord], period_start: date, period_end: date) -> dict[str, dict[str, float]]:
    """Sum usage per account and meter within a billing period.

    Records outside [period_start, period_end] are ignored; the data-pipeline
    export occasionally replays a few days either side of the boundary.
    """
    totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for record in records:
        if not period_start <= record.occurred_on <= period_end:
            continue
        if record.quantity < 0:
            raise ValueError(f"negative quantity for {record.account_id}/{record.meter}")
        totals[record.account_id][record.meter] += record.quantity
    return {account: dict(meters) for account, meters in totals.items()}
