"""
SpendGuard - High-precision token budget guard, spend tracking, and circuit breakers for LLM apps.
Author: Amir Tahani <amirthn653381@gmail.com>
License: Apache-2.0
"""

from .core import SpendGuard, BudgetExceededError, PrecisionSpendAccount
from .pricing import ModelPricing, calculate_cost
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .interceptor import watch_llm, wrap_client

__version__ = "0.1.0"
__all__ = [
    "SpendGuard",
    "BudgetExceededError",
    "PrecisionSpendAccount",
    "ModelPricing",
    "calculate_cost",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "watch_llm",
    "wrap_client",
]
