from __future__ import annotations

import httpx

from app.config import settings
from app.providers.alibaba_auth import AlibabaTokenManager, alibaba_credentials_configured, is_placeholder_key
from app.providers.base import TTSProvider


class DeepgramTTSProvider(TTSProvider):
    """Deepgram Aura-2 text-to-speech.

    Docs: https://developers.deepgram.com/docs/text-to-speech
    Reuses DEEPGRAM_API_KEY — same Deepgram account already used for ASR, no
    extra credential needed. Defaults to `encoding=mp3` rather than raw
    linear16 PCM: measured from the deployed server, a short reply came back
    as ~245KB of raw PCM vs. ~30KB as mp3, and on a slow/lossy cross-border
    network path (mainland China -> Deepgram) that made the download itself
    the dominant and most variable chunk of turn latency (5-20s+ observed),
    far more than the ASR/LLM calls. The mobile client (audioPlayer.ts) reads
    `audio_format` off this class to decide whether to wrap the bytes in a
    WAV header (linear16) or hand them straight to the player as-is (mp3).
    """

    def __init__(self) -> None:
        self.sample_rate = settings.deepgram_tts_sample_rate
        self.audio_format = settings.deepgram_tts_encoding
        # Reused across requests — see DeepgramASRProvider for why.
        self._client = httpx.AsyncClient(timeout=20.0)

    async def synthesize(self, text: str) -> bytes:
        trimmed = text.strip()
        if not trimmed:
            return b""

        api_key = settings.deepgram_api_key
        if is_placeholder_key(api_key):
            return f"DEEPGRAM_TTS_PLACEHOLDER::{text}".encode("utf-8")

        params = {"model": settings.deepgram_tts_model, "encoding": self.audio_format}
        if self.audio_format == "linear16":
            # Raw PCM has no self-describing header, so container/sample_rate
            # must be pinned explicitly; compressed formats (mp3/opus/...)
            # carry their own and don't take these params.
            params["container"] = "none"
            params["sample_rate"] = str(self.sample_rate)
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


class AlibabaTTSProvider(TTSProvider):
    """Alibaba Cloud Intelligent Speech Interaction (NLS) — speech synthesis.

    Docs: https://help.aliyun.com/zh/isi/developer-reference/restful-api-3
    Reuses the same ALIBABA_ACCESS_KEY_ID/SECRET/APP_KEY as AlibabaASRProvider
    (see alibaba_auth.py for the shared X-NLS-Token logic) — no extra
    credentials needed if ASR is already configured for Alibaba.

    Default voice ("abby") is 美式英文 (American English); set
    ALIBABA_TTS_VOICE to try others — see the voice list doc linked above
    (e.g. "andy" for a male American voice, "cindy"/"donna"/"eva"/"brian"/
    "david" for more American options, or "emily"/"eric"/"luna"/"wendy" for
    British ones).
    """

    def __init__(self) -> None:
        self.audio_format = settings.alibaba_tts_format
        self.sample_rate = settings.alibaba_tts_sample_rate
        self._client = httpx.AsyncClient(timeout=20.0)
        self._tokens = AlibabaTokenManager(self._client)

    async def synthesize(self, text: str) -> bytes:
        trimmed = text.strip()
        if not trimmed:
            return b""

        if not alibaba_credentials_configured():
            return f"ALIBABA_TTS_PLACEHOLDER::{text}".encode("utf-8")

        try:
            token = await self._tokens.get_token()
            response = await self._client.post(
                settings.alibaba_tts_base_url,
                headers={"Content-Type": "application/json"},
                json={
                    "appkey": settings.alibaba_app_key,
                    "token": token,
                    "text": trimmed,
                    "voice": settings.alibaba_tts_voice,
                    "format": self.audio_format,
                    "sample_rate": self.sample_rate,
                },
            )
            # Alibaba signals success/failure via Content-Type rather than
            # HTTP status: audio/* means the body is the synthesized audio;
            # anything else (usually application/json) means the body is a
            # JSON error payload instead, even though the HTTP status is 200.
            content_type = response.headers.get("content-type", "")
            if response.status_code == 200 and content_type.startswith("audio/"):
                return response.content

            try:
                error_payload = response.json()
            except ValueError:
                error_payload = response.text
            return f"ALIBABA_TTS_ERROR::{error_payload}".encode("utf-8")
        except httpx.HTTPError as exc:
            return f"ALIBABA_TTS_ERROR::{exc}".encode("utf-8")


class ElevenLabsTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Placeholder bytes for MVP wiring. Real impl should return PCM/WAV bytes.
        return f"ELEVENLABS_AUDIO::{text}".encode("utf-8")


class AzureTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Backup provider placeholder.
        return f"AZURE_AUDIO::{text}".encode("utf-8")
