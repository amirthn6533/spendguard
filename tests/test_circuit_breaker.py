import pytest
from spendguard.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_trips_on_failures():
    cb = CircuitBreaker("openai_test", failure_threshold=3, recovery_cooldown_seconds=10.0)
    assert cb.state == CircuitBreaker.STATE_CLOSED

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitBreaker.STATE_CLOSED

    cb.record_failure()
    assert cb.state == CircuitBreaker.STATE_OPEN

    with pytest.raises(CircuitBreakerOpenError):
        cb.check_can_execute()


def test_circuit_breaker_recovers_after_success():
    cb = CircuitBreaker("openai_test", failure_threshold=2)
    cb.record_failure()
    cb.record_success(duration_seconds=0.2)
    assert cb.state == CircuitBreaker.STATE_CLOSED
