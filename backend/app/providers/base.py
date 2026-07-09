from __future__ import annotations

from abc import ABC, abstractmethod


class ASRProvider(ABC):
    @abstractmethod
    async def transcribe_chunk(
        self, audio_base64: str, *, is_final: bool = False, audio_format: str = "wav"
    ) -> tuple[str, float]:
        raise NotImplementedError


class TTSProvider(ABC):
    # Sample rate (Hz) of PCM16 bytes returned by `synthesize()`. Only
    # meaningful when audio_format == "pcm16" — compressed formats carry
    # their own sample rate in the file header. Session orchestration reports
    # this in the `agent.audio` event's `sampleRate` field so the mobile
    # client's WAV header always matches the real audio.
    sample_rate: int = 24000

    # Container/encoding of the bytes `synthesize()` returns — "pcm16" (raw,
    # needs a WAV header wrapped on before playback) or a self-describing
    # compressed format like "mp3" the client can play directly. Reported in
    # the `agent.audio` event's `format` field.
    audio_format: str = "pcm16"

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    async def reply(self, *, learner_text: str, history: list[dict[str, str]], mode: str) -> str:
        raise NotImplementedError

