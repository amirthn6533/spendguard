"""
Latency and error-rate circuit breaker for LLM services.
"""

import time
import threading
from typing import Optional, Callable, Any


class CircuitBreakerOpenError(Exception):
    """Raised when an LLM call is rejected because the circuit breaker is open."""

    def __init__(self, service_name: str, cooldown_remaining: float):
        self.service_name = service_name
        self.cooldown_remaining = cooldown_remaining
        super().__init__(
            f"SpendGuard Circuit Breaker: [{service_name}] is OPEN. "
            f"Cooling down ({cooldown_remaining:.1f}s remaining) to protect latency & budget."
        )


class CircuitBreaker:
    """
    Standard 3-state circuit breaker: CLOSED (normal), OPEN (tripped), HALF_OPEN (trial).
    Protects applications from runaway retries and cascading latency stalls.
    """

    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        name: str = "default_llm",
        failure_threshold: int = 5,
        recovery_cooldown_seconds: float = 30.0,
        max_latency_seconds: float = 15.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_cooldown_seconds = recovery_cooldown_seconds
        self.max_latency_seconds = max_latency_seconds

        self._state = self.STATE_CLOSED
        self._consecutive_failures = 0
        self._last_state_change = time.time()
        self._lock = threading.RLock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.STATE_OPEN:
                elapsed = time.time() - self._last_state_change
                if elapsed >= self.recovery_cooldown_seconds:
                    self._state = self.STATE_HALF_OPEN
            return self._state

    def check_can_execute(self) -> None:
        """Verify if execution is permitted; raises CircuitBreakerOpenError if tripped."""
        current = self.state
        if current == self.STATE_OPEN:
            elapsed = time.time() - self._last_state_change
            remaining = max(0.0, self.recovery_cooldown_seconds - elapsed)
            raise CircuitBreakerOpenError(self.name, remaining)

    def record_success(self, duration_seconds: float = 0.0) -> None:
        """Record successful invocation."""
        with self._lock:
            if duration_seconds > self.max_latency_seconds:
                # High latency treated as soft degradation
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.failure_threshold:
                    self._trip()
                return

            self._consecutive_failures = 0
            if self._state == self.STATE_HALF_OPEN:
                self._state = self.STATE_CLOSED

    def record_failure(self) -> None:
        """Record failed execution (e.g. timeout, 5xx server error)."""
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._trip()

    def _trip(self) -> None:
        self._state = self.STATE_OPEN
        self._last_state_change = time.time()

    def reset(self) -> None:
        with self._lock:
            self._state = self.STATE_CLOSED
            self._consecutive_failures = 0
            self._last_state_change = time.time()
