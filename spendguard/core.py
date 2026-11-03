"""
High-precision spend accounting and budget enforcement.
"""

from decimal import Decimal, ROUND_HALF_UP
import threading
import time
from typing import Dict, Optional, Any, Callable


class BudgetExceededError(Exception):
    """Raised when an operation would exceed the configured budget limit."""

    def __init__(self, current_spend: float, budget_limit: float, requested_cost: float, entity_id: str):
        self.current_spend = current_spend
        self.budget_limit = budget_limit
        self.requested_cost = requested_cost
        self.entity_id = entity_id
        super().__init__(
            f"SpendGuard: Budget ceiling of ${budget_limit:.4f} exceeded for [{entity_id}]. "
            f"Current spend: ${current_spend:.6f}, attempted: +${requested_cost:.6f}"
        )


class PrecisionSpendAccount:
    """Thread-safe, high-precision spend tracker that prevents IEEE 754 precision underflow."""

    EPSILON = 1e-12

    def __init__(self, entity_id: str, budget_limit: Optional[float] = None):
        self.entity_id = entity_id
        self.budget_limit = budget_limit
        self._spend = Decimal("0.0")
        self._total_tokens = 0
        self._total_requests = 0
        self._last_reset_time = time.time()
        self._lock = threading.RLock()

    @property
    def spend(self) -> float:
        """Return current spend as float, guaranteed non-negative."""
        with self._lock:
            val = float(self._spend)
            if val < 0.0 or abs(val) < self.EPSILON:
                return 0.0
            return val

    @property
    def total_tokens(self) -> int:
        with self._lock:
            return self._total_tokens

    @property
    def total_requests(self) -> int:
        with self._lock:
            return self._total_requests

    def record_usage(self, cost: float, tokens: int = 0) -> float:
        """Record usage and cost thread-safely with precision clamping."""
        with self._lock:
            dec_cost = Decimal(str(max(0.0, cost)))
            new_spend = self._spend + dec_cost

            # Check budget limit if set
            if self.budget_limit is not None and float(new_spend) > self.budget_limit:
                raise BudgetExceededError(
                    current_spend=float(self._spend),
                    budget_limit=self.budget_limit,
                    requested_cost=cost,
                    entity_id=self.entity_id,
                )

            self._spend = new_spend
            self._total_tokens += tokens
            self._total_requests += 1
            return self.spend

    def reset_spend(self, decrement_by: Optional[float] = None) -> float:
        """
        Reset spend either completely to 0 or by subtracting a decrement amount.
        Prevents IEEE 754 precision underflow (e.g. -2.7e-17) after subtraction.
        """
        with self._lock:
            if decrement_by is None:
                self._spend = Decimal("0.0")
            else:
                dec_decrement = Decimal(str(decrement_by))
                self._spend = max(Decimal("0.0"), self._spend - dec_decrement)
                # Precision guard against floating point artifacts
                if self._spend < Decimal(str(self.EPSILON)):
                    self._spend = Decimal("0.0")

            self._last_reset_time = time.time()
            return self.spend


class SpendGuard:
    """Master registry and coordinator for budget enforcement across users, teams, and keys."""

    def __init__(self, global_budget: Optional[float] = None):
        self.global_budget = global_budget
        self._accounts: Dict[str, PrecisionSpendAccount] = {}
        self._lock = threading.RLock()

    def get_account(self, entity_id: str, budget_limit: Optional[float] = None) -> PrecisionSpendAccount:
        """Get or initialize a precision spend account."""
        with self._lock:
            if entity_id not in self._accounts:
                limit = budget_limit if budget_limit is not None else self.global_budget
                self._accounts[entity_id] = PrecisionSpendAccount(entity_id=entity_id, budget_limit=limit)
            return self._accounts[entity_id]

    def record(self, entity_id: str, cost: float, tokens: int = 0) -> float:
        """Record usage for a specific entity ID."""
        acc = self.get_account(entity_id)
        return acc.record_usage(cost, tokens)

    def total_spend(self) -> float:
        """Return aggregate spend across all accounts."""
        with self._lock:
            return sum(acc.spend for acc in self._accounts.values())

    def reset_all(self) -> None:
        """Reset all accounts to zero."""
        with self._lock:
            for acc in self._accounts.values():
                acc.reset_spend()

    def summary(self) -> Dict[str, Any]:
        """Return a structured summary of all monitored entities."""
        with self._lock:
            return {
                "total_entities": len(self._accounts),
                "total_spend_usd": round(self.total_spend(), 6),
                "entities": {
                    k: {
                        "spend": round(v.spend, 6),
                        "tokens": v.total_tokens,
                        "requests": v.total_requests,
                        "budget": v.budget_limit,
                    }
                    for k, v in self._accounts.items()
                },
            }
