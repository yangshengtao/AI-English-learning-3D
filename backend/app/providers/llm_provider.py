from __future__ import annotations

import httpx

from app.config import settings
from app.providers.base import LLMProvider

SYSTEM_PROMPT = (
    "You are a friendly, encouraging 1-on-1 English speaking tutor for a non-native adult learner. "
    "Reply in natural American English, gently correct mistakes, and end with a light follow-up "
    "question to keep the conversation going. Keep the whole reply very short: at most 2 short "
    "sentences and under 200 characters total — this will be spoken aloud, so brevity matters more "
    "than completeness. Current lesson mode: {mode}."
)

# `deepseek_model` (deepseek-v4-flash) is a reasoning model: DeepSeek bills its
# internal chain-of-thought against the same `max_tokens` budget as the
# visible reply, *before* it writes any visible content (see
# `usage.completion_tokens_details.reasoning_tokens` in the raw response).
# 200 was measured to be entirely consumed by reasoning alone on some turns,
# leaving zero tokens left for the actual reply — DeepSeek returns
# `finish_reason="length"` with completely empty `content` in that case
# (this is the "Agent 显示的字段不全" bug). 800 leaves headroom for
# reasoning *and* a full short reply; the system prompt above is what
# actually keeps the visible reply short, not this ceiling.
MAX_REPLY_TOKENS = 800


def _is_placeholder_key(api_key: str) -> bool:
    return not api_key or api_key.strip().upper().startswith("REPLACE_")


def _build_messages(*, system_prompt: str, history: list[dict[str, str]], learner_text: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for turn in history[-10:]:
        role = "assistant" if turn.get("role") == "agent" else "user"
        text = turn.get("text", "")
        if text:
            messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": learner_text})
    return messages


class DeepSeekLLMProvider(LLMProvider):
    """OpenAI-compatible client for DeepSeek chat completions.

    Docs: https://api-docs.deepseek.com/
    Set DEEPSEEK_API_KEY (or backend/.env) to enable real replies; otherwise this
    falls back to a clearly-labeled placeholder response so the rest of the
    pipeline keeps working during local development.
    """

    def __init__(self) -> None:
        # Reused across requests — see DeepgramASRProvider for why.
        self._client = httpx.AsyncClient(base_url=settings.deepseek_base_url, timeout=20.0)

    async def reply(self, *, learner_text: str, history: list[dict[str, str]], mode: str) -> str:
        api_key = settings.deepseek_api_key
        if _is_placeholder_key(api_key):
            return (
                "[DeepSeek API key not configured — set DEEPSEEK_API_KEY] "
                f"Echo: {learner_text}"
            )

        messages = _build_messages(
            system_prompt=SYSTEM_PROMPT.format(mode=mode),
            history=history,
            learner_text=learner_text,
        )

        try:
            response = await self._client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": settings.deepseek_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": MAX_REPLY_TOKENS,
                },
            )
            response.raise_for_status()
            payload = response.json()
            content = str(payload["choices"][0]["message"]["content"]).strip()
            if content:
                return content
            # Should be rare now that MAX_REPLY_TOKENS gives reasoning enough
            # room, but if the model still burns the whole budget on
            # reasoning and returns nothing, don't show a blank Agent reply.
            finish_reason = payload["choices"][0].get("finish_reason", "unknown")
            return f"[DeepSeek returned an empty reply (finish_reason={finish_reason})] Let's try again — {learner_text}"
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            return f"[DeepSeek request failed: {exc}] Let's try again — {learner_text}"


class OpenAILLMProvider(LLMProvider):
    async def reply(self, *, learner_text: str, history: list[dict[str, str]], mode: str) -> str:
        if mode == "scenario":
            return (
                "Nice try. In this situation, a natural American way is: "
                f"'I'd like to {learner_text.lower()}, please.'"
            )
        return (
            "Great effort. Let me refine that sentence in natural American English: "
            f"{learner_text}."
        )


class AnthropicLLMProvider(LLMProvider):
    async def reply(self, *, learner_text: str, history: list[dict[str, str]], mode: str) -> str:
        return f"Good attempt. Alternative phrasing: {learner_text}."
