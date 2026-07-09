from __future__ import annotations

import pytest

from app.config import settings
from app.providers.tts_provider import AlibabaTTSProvider, DeepgramTTSProvider


@pytest.mark.anyio
async def test_deepgram_tts_falls_back_to_placeholder_without_key() -> None:
    provider = DeepgramTTSProvider()

    audio = await provider.synthesize("Hello there")

    assert audio.startswith(b"DEEPGRAM_TTS_PLACEHOLDER::")
    assert b"Hello there" in audio


@pytest.mark.anyio
async def test_deepgram_tts_returns_empty_bytes_for_blank_text() -> None:
    provider = DeepgramTTSProvider()

    audio = await provider.synthesize("   ")

    assert audio == b""


def test_deepgram_tts_sample_rate_matches_settings() -> None:
    provider = DeepgramTTSProvider()

    assert provider.sample_rate == settings.deepgram_tts_sample_rate


def test_deepgram_tts_audio_format_matches_settings() -> None:
    provider = DeepgramTTSProvider()

    assert provider.audio_format == settings.deepgram_tts_encoding


@pytest.mark.anyio
async def test_alibaba_tts_falls_back_to_placeholder_without_credentials() -> None:
    provider = AlibabaTTSProvider()

    audio = await provider.synthesize("Hello there")

    assert audio.startswith(b"ALIBABA_TTS_PLACEHOLDER::")
    assert b"Hello there" in audio


@pytest.mark.anyio
async def test_alibaba_tts_returns_empty_bytes_for_blank_text() -> None:
    provider = AlibabaTTSProvider()

    audio = await provider.synthesize("   ")

    assert audio == b""


def test_alibaba_tts_audio_format_and_sample_rate_match_settings() -> None:
    provider = AlibabaTTSProvider()

    assert provider.audio_format == settings.alibaba_tts_format
    assert provider.sample_rate == settings.alibaba_tts_sample_rate
