"""Dunning workflow for overdue invoices.

Escalation ladder:
  day 0   -> invoice issued
  day 7   -> friendly reminder email
  day 21  -> formal notice + finance CC
  day 45  -> account suspended, shipments held at depot
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

DUNNING_STAGES: list[tuple[int, str]] = [
    (7, "reminder"),
    (21, "formal_notice"),
    (45, "suspend_account"),
]


@dataclass(frozen=True)
class DunningAction:
    account_id: str
    invoice_total: str
    stage: str
    days_overdue: int


def stage_for(days_overdue: int) -> str | None:
    """Return the current dunning stage for an overdue age, if any."""
    stage = None
    for threshold, name in DUNNING_STAGES:
        if days_overdue >= threshold:
            stage = name
    return stage


def evaluate_invoice(account_id: str, total: str, due_date: date, today: date, paid: bool) -> DunningAction | None:
    """Decide the dunning action for one invoice as of *today*."""
    if paid or today <= due_date:
        return None
    days_overdue = (today - due_date).days
    stage = stage_for(days_overdue)
    if stage is None:
        return None
    return DunningAction(account_id=account_id, invoice_total=total, stage=stage, days_overdue=days_overdue)
