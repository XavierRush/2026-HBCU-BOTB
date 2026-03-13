from __future__ import annotations

from types import SimpleNamespace

from core import anthropic_rate_limit
from core import query_engine


def test_query_llm_sends_direct_web_search_tool(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeMessagesAPI:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type="text", text="ok")])

    fake_client = SimpleNamespace(messages=FakeMessagesAPI())

    monkeypatch.setattr(query_engine.anthropic, "Anthropic", lambda api_key: fake_client)

    response = query_engine.query_llm("best collapsible dog crates")

    assert response == "ok"
    assert len(calls) == 1
    assert calls[0]["tools"] == [
        {
            "type": query_engine.WEB_SEARCH_TOOL_TYPE,
            "name": query_engine.WEB_SEARCH_TOOL_NAME,
            "allowed_callers": query_engine.WEB_SEARCH_ALLOWED_CALLERS,
        }
    ]


def test_query_llm_uses_rate_limited_message_wrapper(monkeypatch) -> None:
    fake_client = SimpleNamespace()
    captured: dict[str, object] = {}

    monkeypatch.setattr(query_engine.anthropic, "Anthropic", lambda api_key: fake_client)

    def fake_create_rate_limited_message(client, **kwargs):
        captured["client"] = client
        captured["kwargs"] = kwargs
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="limited")])

    monkeypatch.setattr(
        query_engine,
        "create_rate_limited_message",
        fake_create_rate_limited_message,
    )

    response = query_engine.query_llm("best collapsible dog crates")

    assert response == "limited"
    assert captured["client"] is fake_client
    assert captured["kwargs"]["messages"] == [
        {"role": "user", "content": "best collapsible dog crates"}
    ]


def test_input_token_rate_limiter_waits_for_window_reset() -> None:
    now = 0.0
    sleep_calls: list[float] = []

    def time_fn() -> float:
        return now

    def sleep_fn(seconds: float) -> None:
        nonlocal now
        sleep_calls.append(seconds)
        now += seconds

    limiter = anthropic_rate_limit.InputTokenRateLimiter(
        10,
        window_seconds=60.0,
        time_fn=time_fn,
        sleep_fn=sleep_fn,
    )

    limiter.acquire(6)
    limiter.acquire(4)
    limiter.acquire(1)

    assert sleep_calls == [60.0]


def test_input_token_rate_limiter_rejects_oversized_prompt() -> None:
    limiter = anthropic_rate_limit.InputTokenRateLimiter(10)

    try:
        limiter.acquire(11)
    except ValueError as exc:
        assert "input token budget" in str(exc)
    else:
        raise AssertionError("Expected oversized prompts to be rejected.")


def test_estimate_input_tokens_is_stricter_than_raw_text_ratio() -> None:
    estimated = anthropic_rate_limit.estimate_input_tokens(
        [{"role": "user", "content": "abcdefghij"}]
    )

    assert estimated == (
        anthropic_rate_limit.REQUEST_TOKEN_OVERHEAD
        + anthropic_rate_limit.MESSAGE_TOKEN_OVERHEAD
        + 5
    )


def test_effective_input_budget_applies_safety_margin() -> None:
    assert anthropic_rate_limit.EFFECTIVE_INPUT_TOKEN_BUDGET == 18000
