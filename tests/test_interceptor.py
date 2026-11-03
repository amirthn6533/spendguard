import pytest
from spendguard import SpendGuard, watch_llm, calculate_cost


class MockUsage:
    prompt_tokens = 1000
    completion_tokens = 500


class MockResponse:
    model = "gpt-4o"
    usage = MockUsage()


def test_watch_llm_decorator():
    guard = SpendGuard(global_budget=1.0)

    @watch_llm(guard=guard, entity_id="agent_1", model="gpt-4o")
    def call_ai():
        return MockResponse()

    res = call_ai()
    assert res.model == "gpt-4o"
    expected_cost = calculate_cost("gpt-4o", 1000, 500)
    assert guard.get_account("agent_1").spend == expected_cost
    assert guard.get_account("agent_1").total_tokens == 1500
