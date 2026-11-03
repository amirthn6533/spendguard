"""
Interceptor decorator and client wrappers for seamless LLM tracking.
"""

from functools import wraps
import time
from typing import Any, Callable, Optional
from .core import SpendGuard
from .pricing import calculate_cost
from .circuit_breaker import CircuitBreaker


def watch_llm(
    guard: SpendGuard,
    entity_id: str = "default",
    model: str = "gpt-4o",
    circuit_breaker: Optional[CircuitBreaker] = None,
):
    """
    Decorator to automatically guard an LLM invocation function.
    Checks circuit breaker, runs function, extracts token usage, and tracks spend.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cb = circuit_breaker
            if cb is not None:
                cb.check_can_execute()

            start_t = time.perf_counter()
            try:
                response = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_t
                if cb is not None:
                    cb.record_success(elapsed)

                # Extract usage from OpenAI/LiteLLM standard response objects or dicts
                prompt_tokens = 0
                completion_tokens = 0
                used_model = model

                if hasattr(response, "usage") and response.usage:
                    prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
                elif isinstance(response, dict) and "usage" in response:
                    u = response["usage"]
                    prompt_tokens = u.get("prompt_tokens", 0)
                    completion_tokens = u.get("completion_tokens", 0)

                if hasattr(response, "model") and response.model:
                    used_model = response.model
                elif isinstance(response, dict) and "model" in response:
                    used_model = response["model"]

                if prompt_tokens > 0 or completion_tokens > 0:
                    cost = calculate_cost(used_model, prompt_tokens, completion_tokens)
                    guard.record(entity_id, cost=cost, tokens=prompt_tokens + completion_tokens)

                return response
            except Exception as e:
                if cb is not None:
                    cb.record_failure()
                raise e

        return wrapper
    return decorator


def wrap_client(client: Any, guard: SpendGuard, entity_id: str = "default") -> Any:
    """Wrap standard OpenAI or LiteLLM client chat completions."""
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        orig_create = client.chat.completions.create

        @wraps(orig_create)
        def guarded_create(*args, **kwargs):
            model = kwargs.get("model", "gpt-4o")
            wrapped = watch_llm(guard=guard, entity_id=entity_id, model=model)(orig_create)
            return wrapped(*args, **kwargs)

        client.chat.completions.create = guarded_create
    return client
