import pytest
from spendguard.core import PrecisionSpendAccount, SpendGuard


def test_float_underflow_clamped_to_zero():
    account = PrecisionSpendAccount("test_key")
    account.record_usage(0.0001)
    # Subtract slightly more or exact amount to test floating point underflow
    account.reset_spend(decrement_by=0.0001000000000000001)
    assert account.spend == 0.0
    assert account.spend >= 0.0


def test_epsilon_zero_clamp():
    account = PrecisionSpendAccount("epsilon_key")
    account.record_usage(0.000000000001)
    account.reset_spend(decrement_by=0.000000000001)
    assert account.spend == 0.0


def test_precision_accumulation():
    account = PrecisionSpendAccount("accum_key")
    # 100 small transactions of $0.000035
    for _ in range(100):
        account.record_usage(0.000035)

    assert round(account.spend, 6) == 0.0035
