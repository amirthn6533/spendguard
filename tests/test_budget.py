import pytest
from spendguard.core import SpendGuard, BudgetExceededError


def test_budget_exceeded_error_thrown():
    guard = SpendGuard(global_budget=0.01)  # $0.01 limit
    acc = guard.get_account("user_1")

    # $0.008 is allowed
    acc.record_usage(0.008)
    assert acc.spend == 0.008

    # Another $0.005 would push it to $0.013 > $0.01
    with pytest.raises(BudgetExceededError) as exc_info:
        acc.record_usage(0.005)

    assert "Budget ceiling of $0.0100 exceeded" in str(exc_info.value)
    # Ensure current spend was preserved and not corrupted
    assert acc.spend == 0.008


def test_multi_account_tracking():
    guard = SpendGuard()
    guard.record("user_a", cost=0.05, tokens=1000)
    guard.record("user_b", cost=0.03, tokens=600)

    assert guard.total_spend() == 0.08
    summary = guard.summary()
    assert summary["total_entities"] == 2
    assert summary["entities"]["user_a"]["tokens"] == 1000
    assert summary["entities"]["user_b"]["tokens"] == 600
