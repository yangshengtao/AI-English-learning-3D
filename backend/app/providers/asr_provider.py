from __future__ import annotations

from app.providers.base import ASRProvider


class DeepgramASRProvider(ASRProvider):
    async def transcribe_chunk(self, audio_base64: str, *, is_final: bool = False) -> tuple[str, float]:
        # Placeholder integration point for Deepgram streaming API.
        if not audio_base64:
            return "", 0.0
        text = "partial transcript" if not is_final else "final transcript from learner"
        confidence = 0.82 if not is_final else 0.91
        return text, confidence


class GoogleASRProvider(ASRProvider):
    async def transcribe_chunk(self, audio_base64: str, *, is_final: bool = False) -> tuple[str, float]:
        # Backup provider placeholder. Keep same return contract for easy routing.
        if not audio_base64:
            return "", 0.0
        text = "google partial transcript" if not is_final else "google final transcript"
        confidence = 0.79 if not is_final else 0.89
        return text, confidence

