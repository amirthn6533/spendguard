# SpendGuard ⚡

[![PyPI](https://img.shields.io/pypi/v/spendguard-ai.svg)](https://pypi.org/project/spendguard-ai/)
[![CI](https://github.com/amirthn6533/spendguard/actions/workflows/ci.yml/badge.svg)](https://github.com/amirthn6533/spendguard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://pypi.org/project/spendguard-ai/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Zero-Dependency](https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg)](#)

**SpendGuard** (`spendguard-ai`) is a zero-dependency, microsecond-latency budget guard, floating-point spend tracker, and latency circuit breaker for modern LLM applications (OpenAI, LiteLLM, Anthropic, LangChain, DeepSeek).

---

## 🎯 The Problem

In high-concurrency LLM services, standard floating-point subtraction (`pre_spend - decrement`) suffers from IEEE-754 precision drift, frequently creating micro-negative values (e.g. `-2.7e-17`). In production environments using PostgreSQL or Pydantic schemas with `ge=0.0` constraints, this causes unexpected API validation crashes during periodic budget resets.

Furthermore, runaway agent loops and slow provider endpoints can drain budgets or stall user requests before rate-limits kick in.

**SpendGuard solves this with:**
1. **IEEE 754 Epsilon Clamping**: Guaranteed non-negative, precision-safe spend accounting.
2. **Hard Multi-Tenant Ceilings**: Thread-safe budget limits for keys, users, and teams.
3. **Latency Circuit Breakers**: Fast-fail protection when upstream LLMs experience degradation.
4. **Zero External Dependencies**: Pure Python standard library implementation with sub-microsecond overhead (<0.5μs per check).

---

## 📦 Installation

```bash
pip install spendguard-ai
```

*(or install from source)*
```bash
git clone https://github.com/amirthn6533/spendguard.git
cd spendguard
pip install -e .
```

---

## 🚀 Quickstart

### 1. Basic Budget Guard

```python
from spendguard import SpendGuard, BudgetExceededError

# Initialize with a $10.00 daily budget limit
guard = SpendGuard(global_budget=10.00)
account = guard.get_account("user_tenant_42")

try:
    # Record usage ($0.015 cost, 3000 tokens)
    account.record_usage(cost=0.015, tokens=3000)
    print(f"Current Spend: ${account.spend:.6f}")
except BudgetExceededError as e:
    print(f"Request blocked: {e}")
```

### 2. Auto-Guarding OpenAI / LiteLLM Calls

```python
from openai import OpenAI
from spendguard import SpendGuard, watch_llm

guard = SpendGuard(global_budget=5.00)
client = OpenAI()

@watch_llm(guard=guard, entity_id="user_tenant_42", model="gpt-4o")
def call_agent(prompt: str):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

response = call_agent("Explain quantum computing in one sentence.")
```

### 3. Latency Circuit Breaker

```python
from spendguard import CircuitBreaker, CircuitBreakerOpenError

breaker = CircuitBreaker(
    name="anthropic_service",
    failure_threshold=3,
    recovery_cooldown_seconds=30.0,
    max_latency_seconds=10.0
)

breaker.check_can_execute()  # Raises CircuitBreakerOpenError if tripped
```

---

## 💻 Command Line Interface (CLI)

SpendGuard includes an interactive CLI for quick cost calculations and simulations:

### Estimate Model Cost:
```bash
spendguard cost --model gpt-4o --prompt 2500 --completion 800
```
```text
=== SpendGuard Cost Estimate ===
  Model             : gpt-4o
  Prompt Tokens     : 2,500
  Completion Tokens : 800
  Total Cost        : $0.014250 USD
```

### View Built-in Rates:
```bash
spendguard models
```

### Run Budget Enforcement Demo:
```bash
spendguard demo
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```
All 8 test suites pass across Python 3.9–3.13 in <0.05 seconds.

---

## 📄 License

Apache License 2.0. Authored by [Amir Tahani](https://github.com/amirthn6533).
