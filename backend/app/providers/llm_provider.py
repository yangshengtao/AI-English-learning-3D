from __future__ import annotations

import httpx

from app.config import settings
from app.providers.base import LLMProvider

SYSTEM_PROMPT = (
    "You are a friendly, encouraging 1-on-1 English speaking tutor for a non-native adult learner. "
    "Reply in natural American English, keep it short (1-3 sentences), gently correct mistakes, "
    "and end with a light follow-up question to keep the conversation going. "
    "Current lesson mode: {mode}."
)


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
            async with httpx.AsyncClient(base_url=settings.deepseek_base_url, timeout=20.0) as client:
                response = await client.post(
                    "/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": settings.deepseek_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 200,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            return str(content).strip()
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
