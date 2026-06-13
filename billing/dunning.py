"""Dunning workflow for overdue invoices.

Default escalation ladder:
  day 0   -> invoice issued
  day 7   -> friendly reminder email
  day 21  -> formal notice + finance CC
  day 45  -> account suspended, shipments held at depot

Enterprise accounts negotiate softer cadences (e.g. 14/30/60) in their
freight contracts, so the ladder is configurable per evaluation via
``DunningSchedule``; the module-level default keeps existing callers
unchanged.
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
class DunningSchedule:
    """An escalation ladder of (days_overdue, stage) pairs.

    Stages must be strictly ascending in days; the highest threshold at or
    below the invoice's overdue age wins.
    """

    stages: tuple[tuple[int, str], ...]

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("dunning schedule needs at least one stage")
        days = [threshold for threshold, _ in self.stages]
        if any(d <= 0 for d in days):
            raise ValueError("dunning thresholds must be positive")
        if days != sorted(set(days)):
            raise ValueError("dunning thresholds must be strictly ascending")

    @classmethod
    def from_pairs(cls, pairs: list[tuple[int, str]]) -> DunningSchedule:
        return cls(stages=tuple(pairs))


DEFAULT_SCHEDULE = DunningSchedule.from_pairs(DUNNING_STAGES)


@dataclass(frozen=True)
class DunningAction:
    account_id: str
    invoice_total: str
    stage: str
    days_overdue: int


def stage_for(days_overdue: int, schedule: DunningSchedule = DEFAULT_SCHEDULE) -> str | None:
    """Return the current dunning stage for an overdue age, if any."""
    stage = None
    for threshold, name in schedule.stages:
        if days_overdue >= threshold:
            stage = name
    return stage


def evaluate_invoice(
    account_id: str,
    total: str,
    due_date: date,
    today: date,
    paid: bool,
    schedule: DunningSchedule = DEFAULT_SCHEDULE,
) -> DunningAction | None:
    """Decide the dunning action for one invoice as of *today*."""
    if paid or today <= due_date:
        return None
    days_overdue = (today - due_date).days
    stage = stage_for(days_overdue, schedule)
    if stage is None:
        return None
    return DunningAction(account_id=account_id, invoice_total=total, stage=stage, days_overdue=days_overdue)
