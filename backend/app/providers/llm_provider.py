from __future__ import annotations

from app.providers.base import LLMProvider


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

