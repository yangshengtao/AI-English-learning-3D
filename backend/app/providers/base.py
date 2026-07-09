from __future__ import annotations

from abc import ABC, abstractmethod


class ASRProvider(ABC):
    @abstractmethod
    async def transcribe_chunk(
        self, audio_base64: str, *, is_final: bool = False, audio_format: str = "wav"
    ) -> tuple[str, float]:
        raise NotImplementedError


class TTSProvider(ABC):
    # Sample rate (Hz) of the PCM16 bytes `synthesize()` returns. Session
    # orchestration reports this in the `agent.audio` event's `sampleRate`
    # field so the mobile client's WAV header always matches the real audio.
    sample_rate: int = 24000

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    async def reply(self, *, learner_text: str, history: list[dict[str, str]], mode: str) -> str:
        raise NotImplementedError

