from datetime import date

from billing.dunning import DunningSchedule, evaluate_invoice, stage_for

DUE = date(2026, 1, 15)

ENTERPRISE = DunningSchedule.from_pairs(
    [
        (14, "reminder"),
        (30, "formal_notice"),
        (60, "suspend_account"),
    ]
)


def test_default_schedule_unchanged():
    assert stage_for(6) is None
    assert stage_for(7) == "reminder"
    assert stage_for(21) == "formal_notice"
    assert stage_for(45) == "suspend_account"


def test_custom_schedule_shifts_thresholds():
    assert stage_for(7, ENTERPRISE) is None
    assert stage_for(14, ENTERPRISE) == "reminder"
    assert stage_for(59, ENTERPRISE) == "formal_notice"
    assert stage_for(60, ENTERPRISE) == "suspend_account"


def test_evaluate_invoice_uses_schedule():
    action = evaluate_invoice("acct_007", "120.00", DUE, date(2026, 1, 30), paid=False, schedule=ENTERPRISE)
    assert action is not None
    assert action.stage == "reminder"
    assert action.days_overdue == 15


def test_paid_invoice_never_escalates():
    assert evaluate_invoice("acct_007", "120.00", DUE, date(2026, 3, 30), paid=True, schedule=ENTERPRISE) is None


def test_schedule_validation():
    for bad in ([], [(0, "reminder")], [(21, "a"), (7, "b")], [(7, "a"), (7, "b")]):
        try:
            DunningSchedule.from_pairs(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")
