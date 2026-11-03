"""
Pricing directory and token cost calculation.
"""

from typing import Dict, Tuple

# Rates per 1M tokens: (prompt_rate_usd, completion_rate_usd)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "o1": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
    "gpt-4-turbo": (10.00, 30.00),
    # Anthropic
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    # DeepSeek
    "deepseek-chat": (0.14, 0.28),
    "deepseek-reasoner": (0.55, 2.19),
    # Meta / Open-Source hosted
    "meta-llama/llama-3.3-70b-instruct": (0.60, 0.60),
    "meta-llama/llama-3.1-8b-instruct": (0.05, 0.05),
}


class ModelPricing:
    """Registry for model pricing and rate lookup."""

    @classmethod
    def get_rate(cls, model_name: str) -> Tuple[float, float]:
        """Normalize model name and return (prompt_rate_per_m, completion_rate_per_m)."""
        clean_name = model_name.lower().strip()
        for key, rates in MODEL_PRICING.items():
            if key in clean_name or clean_name in key:
                return rates
        # Default fallback: $1 / 1M prompt, $3 / 1M completion
        return (1.00, 3.00)


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate the precise cost in USD for a given token usage."""
    prompt_rate, completion_rate = ModelPricing.get_rate(model)
    prompt_cost = (prompt_tokens / 1_000_000.0) * prompt_rate
    completion_cost = (completion_tokens / 1_000_000.0) * completion_rate
    total = prompt_cost + completion_cost
    # Clamp negative floating point epsilon
    return max(0.0, round(total, 8))
