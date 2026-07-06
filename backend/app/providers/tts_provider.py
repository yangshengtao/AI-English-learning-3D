from __future__ import annotations

import struct

from app.providers.base import TTSProvider


def _build_test_wav(duration_sec: float = 0.35, sample_rate: int = 24000) -> bytes:
    # Build a short silent PCM16 WAV so iOS playback path can be tested end-to-end.
    samples = int(duration_sec * sample_rate)
    pcm_data = b"".join(struct.pack("<h", 0) for _ in range(samples))

    channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_data)
    riff_size = 36 + data_size

    return (
        b"RIFF"
        + struct.pack("<I", riff_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        + b"data"
        + struct.pack("<I", data_size)
        + pcm_data
    )


class ElevenLabsTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Placeholder WAV bytes for MVP wiring. Replace with real ElevenLabs API output.
        return _build_test_wav()


class AzureTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Placeholder WAV bytes for backup provider path.
        return _build_test_wav()

