from __future__ import annotations

import json

import httpx
import pytest

from app.providers.llm_provider import MAX_REPLY_TOKENS, DeepSeekLLMProvider


def _provider_with_mock_response(response_json: dict, *, capture: dict | None = None) -> DeepSeekLLMProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture["request_json"] = json.loads(request.content)
        return httpx.Response(200, json=response_json)

    provider = DeepSeekLLMProvider()
    provider._client = httpx.AsyncClient(
        base_url="https://mock.test", transport=httpx.MockTransport(handler)
    )
    return provider


@pytest.mark.anyio
async def test_deepseek_reply_falls_back_when_content_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "deepseek_api_key", "sk-real-looking-key")
    capture: dict = {}
    provider = _provider_with_mock_response(
        {
            "choices": [
                {
                    "message": {"content": ""},
                    "finish_reason": "length",
                }
            ]
        },
        capture=capture,
    )

    reply = await provider.reply(learner_text="Tell me a long story", history=[], mode="free_talk")

    assert "empty reply" in reply
    assert "finish_reason=length" in reply
    assert capture["request_json"]["max_tokens"] == MAX_REPLY_TOKENS


@pytest.mark.anyio
async def test_deepseek_reply_returns_content_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "deepseek_api_key", "sk-real-looking-key")
    provider = _provider_with_mock_response(
        {"choices": [{"message": {"content": "Nice to meet you!"}, "finish_reason": "stop"}]}
    )

    reply = await provider.reply(learner_text="Hello", history=[], mode="free_talk")

    assert reply == "Nice to meet you!"
