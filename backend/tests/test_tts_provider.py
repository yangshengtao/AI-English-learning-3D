from __future__ import annotations

import pytest

from app.config import settings
from app.providers.tts_provider import (
    ALIBABA_TTS_MAX_CHARS,
    AlibabaTTSProvider,
    DeepgramTTSProvider,
    _truncate_for_alibaba_tts,
)


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


def test_truncate_for_alibaba_tts_leaves_short_text_untouched() -> None:
    text = "This is a short reply."

    assert _truncate_for_alibaba_tts(text) == text


def test_truncate_for_alibaba_tts_cuts_at_sentence_boundary() -> None:
    # Two clean sentences that together exceed the cap, with the first
    # sentence ending well past the halfway point of the limit.
    first_sentence = "A" * 200 + "."
    second_sentence = " " + "B" * 150 + "."
    text = first_sentence + second_sentence
    assert len(text) > ALIBABA_TTS_MAX_CHARS

    clipped = _truncate_for_alibaba_tts(text)

    assert clipped == first_sentence
    assert len(clipped) <= ALIBABA_TTS_MAX_CHARS


def test_truncate_for_alibaba_tts_hard_cuts_when_no_late_sentence_boundary() -> None:
    # No punctuation anywhere near the limit, so there's nothing sensible to
    # cut on — falls back to a hard cut with an ellipsis marker.
    text = "word " * 100
    assert len(text) > ALIBABA_TTS_MAX_CHARS

    clipped = _truncate_for_alibaba_tts(text)

    assert len(clipped) <= ALIBABA_TTS_MAX_CHARS + 1
    assert clipped.endswith("…")
