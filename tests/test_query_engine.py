from __future__ import annotations

from types import SimpleNamespace

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
