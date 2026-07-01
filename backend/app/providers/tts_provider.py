from __future__ import annotations

from app.providers.base import TTSProvider


class ElevenLabsTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Placeholder bytes for MVP wiring. Real impl should return PCM/WAV bytes.
        return f"ELEVENLABS_AUDIO::{text}".encode("utf-8")


class AzureTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Backup provider placeholder.
        return f"AZURE_AUDIO::{text}".encode("utf-8")

