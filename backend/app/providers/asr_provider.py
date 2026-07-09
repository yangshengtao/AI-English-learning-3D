from __future__ import annotations

import base64
import binascii

import httpx

from app.config import settings
from app.providers.alibaba_auth import AlibabaTokenManager, alibaba_credentials_configured, is_placeholder_key
from app.providers.base import ASRProvider

# Maps the `format` field sent by clients (see docs/realtime-protocol.md) to the
# Content-Type Deepgram expects for the raw audio bytes in the request body.
FORMAT_CONTENT_TYPES: dict[str, str] = {
    "m4a": "audio/mp4",
    "mp4": "audio/mp4",
    "aac": "audio/aac",
    "wav": "audio/wav",
    "webm": "audio/webm",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
}
DEFAULT_CONTENT_TYPE = "audio/mp4"


class DeepgramASRProvider(ASRProvider):
    """Real Deepgram prerecorded transcription.

    Docs: https://developers.deepgram.com/docs/pre-recorded-audio
    Set DEEPGRAM_API_KEY (or backend/.env) to enable real transcription; otherwise
    this returns a clearly-labeled placeholder so the rest of the pipeline keeps
    working during local development.

    Partial chunks (`is_final=False`) are not sent to Deepgram to avoid billing
    the same audio twice — the mobile client currently uploads the full
    recording as a single chunk followed by `audio.commit`, so only the final
    call needs a real transcription.
    """

    def __init__(self) -> None:
        # Reused across requests so repeat calls hit Deepgram over a warm
        # keep-alive connection instead of paying a fresh TCP+TLS handshake
        # (~200-500ms round trip to Deepgram) on every turn.
        self._client = httpx.AsyncClient(timeout=20.0)

    async def transcribe_chunk(
        self, audio_base64: str, *, is_final: bool = False, audio_format: str = "wav"
    ) -> tuple[str, float]:
        if not audio_base64:
            return "", 0.0

        if not is_final:
            return "", 0.0

        api_key = settings.deepgram_api_key
        if is_placeholder_key(api_key):
            return "[Deepgram API key not configured — set DEEPGRAM_API_KEY]", 0.0

        try:
            audio_bytes = base64.b64decode(audio_base64)
        except (ValueError, binascii.Error) as exc:
            return f"[Deepgram invalid audio payload: {exc}]", 0.0

        content_type = FORMAT_CONTENT_TYPES.get(audio_format.lower(), DEFAULT_CONTENT_TYPE)
        params = {"model": settings.deepgram_model, "smart_format": "true", "language": "en"}

        try:
            response = await self._client.post(
                settings.deepgram_base_url,
                params=params,
                headers={"Authorization": f"Token {api_key}", "Content-Type": content_type},
                content=audio_bytes,
            )
            response.raise_for_status()
            payload = response.json()
            alternative = payload["results"]["channels"][0]["alternatives"][0]
            transcript = str(alternative.get("transcript", "")).strip()
            confidence = float(alternative.get("confidence", 0.0))
            return transcript, confidence
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            return f"[Deepgram request failed: {exc}]", 0.0


# Maps the `format` field sent by clients to the `format` query param Alibaba's
# one-sentence recognition API expects. m4a/mp4 containers hold AAC audio, which
# Alibaba accepts directly under the "aac" format.
ALIBABA_FORMAT_MAP: dict[str, str] = {
    "m4a": "aac",
    "mp4": "aac",
    "aac": "aac",
    "wav": "wav",
    "pcm": "pcm",
    "mp3": "mp3",
    "amr": "amr",
    "opus": "opus",
}
ALIBABA_SUCCESS_STATUS = 20000000


class AlibabaASRProvider(ASRProvider):
    """Alibaba Cloud Intelligent Speech Interaction (NLS) — one-sentence recognition.

    Docs: https://help.aliyun.com/zh/isi/developer-reference/restful-api-2
    Requires ALIBABA_ACCESS_KEY_ID / ALIBABA_ACCESS_KEY_SECRET (used to auto-fetch and
    cache a short-lived X-NLS-Token via the CreateToken OpenAPI, see
    https://help.aliyun.com/zh/isi/getting-started/use-http-or-https-to-obtain-an-access-token)
    and ALIBABA_APP_KEY (created in the Intelligent Speech Interaction console).

    Only mono audio at 8000 Hz or 16000 Hz is supported by this API, so the mobile
    client's recorder is configured to match (see mobile/src/services/audioRecorder.ts).

    Partial chunks (`is_final=False`) are skipped for the same reason as Deepgram:
    avoid spending quota transcribing audio that will be re-sent on commit.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=20.0)
        self._tokens = AlibabaTokenManager(self._client)

    async def transcribe_chunk(
        self, audio_base64: str, *, is_final: bool = False, audio_format: str = "wav"
    ) -> tuple[str, float]:
        if not audio_base64:
            return "", 0.0

        if not is_final:
            return "", 0.0

        if not alibaba_credentials_configured():
            return (
                "[Alibaba Cloud NLS credentials not configured — set "
                "ALIBABA_ACCESS_KEY_ID/ALIBABA_ACCESS_KEY_SECRET/ALIBABA_APP_KEY]",
                0.0,
            )

        try:
            audio_bytes = base64.b64decode(audio_base64)
        except (ValueError, binascii.Error) as exc:
            return f"[Alibaba invalid audio payload: {exc}]", 0.0

        nls_format = ALIBABA_FORMAT_MAP.get(audio_format.lower(), "aac")

        try:
            token = await self._tokens.get_token()
            response = await self._client.post(
                settings.alibaba_asr_base_url,
                params={
                    "appkey": settings.alibaba_app_key,
                    "format": nls_format,
                    "sample_rate": settings.alibaba_sample_rate,
                    "enable_punctuation_prediction": "true",
                    "enable_inverse_text_normalization": "true",
                },
                headers={"X-NLS-Token": token, "Content-Type": "application/octet-stream"},
                content=audio_bytes,
            )
            response.raise_for_status()
            payload = response.json()

            if int(payload.get("status", 0)) != ALIBABA_SUCCESS_STATUS:
                return f"[Alibaba NLS error: {payload.get('message', payload)}]", 0.0

            transcript = str(payload.get("result", "")).strip()
            # One-sentence recognition does not return a confidence score.
            return transcript, 0.9
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            return f"[Alibaba NLS request failed: {exc}]", 0.0


class GoogleASRProvider(ASRProvider):
    async def transcribe_chunk(
        self, audio_base64: str, *, is_final: bool = False, audio_format: str = "wav"
    ) -> tuple[str, float]:
        # Backup provider placeholder. Keep same return contract for easy routing.
        if not audio_base64:
            return "", 0.0
        text = "google partial transcript" if not is_final else "google final transcript"
        confidence = 0.79 if not is_final else 0.89
        return text, confidence
