from __future__ import annotations

import httpx

from app.config import settings
from app.providers.base import TTSProvider


def _is_placeholder_key(api_key: str) -> bool:
    return not api_key or api_key.strip().upper().startswith("REPLACE_")


class DeepgramTTSProvider(TTSProvider):
    """Deepgram Aura-2 text-to-speech.

    Docs: https://developers.deepgram.com/docs/text-to-speech
    Reuses DEEPGRAM_API_KEY — same Deepgram account already used for ASR, no
    extra credential needed. Requests raw 16-bit PCM with no container
    (`encoding=linear16&container=none`) so the response body can be sent
    straight through as the `agent.audio` payload; the mobile client wraps it
    in its own WAV header before playback (see
    mobile/src/services/audioPlayer.ts).
    """

    def __init__(self) -> None:
        self.sample_rate = settings.deepgram_tts_sample_rate
        # Reused across requests — see DeepgramASRProvider for why.
        self._client = httpx.AsyncClient(timeout=20.0)

    async def synthesize(self, text: str) -> bytes:
        trimmed = text.strip()
        if not trimmed:
            return b""

        api_key = settings.deepgram_api_key
        if _is_placeholder_key(api_key):
            return f"DEEPGRAM_TTS_PLACEHOLDER::{text}".encode("utf-8")

        params = {
            "model": settings.deepgram_tts_model,
            "encoding": "linear16",
            "container": "none",
            "sample_rate": str(self.sample_rate),
        }
        try:
            response = await self._client.post(
                settings.deepgram_tts_base_url,
                params=params,
                headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
                json={"text": trimmed},
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as exc:
            return f"DEEPGRAM_TTS_ERROR::{exc}".encode("utf-8")


class ElevenLabsTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Placeholder bytes for MVP wiring. Real impl should return PCM/WAV bytes.
        return f"ELEVENLABS_AUDIO::{text}".encode("utf-8")


class AzureTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Backup provider placeholder.
        return f"AZURE_AUDIO::{text}".encode("utf-8")
