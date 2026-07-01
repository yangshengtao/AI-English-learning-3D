from app.config import settings
from app.providers.asr_provider import DeepgramASRProvider, GoogleASRProvider
from app.providers.base import ASRProvider, LLMProvider, TTSProvider
from app.providers.llm_provider import AnthropicLLMProvider, OpenAILLMProvider
from app.providers.tts_provider import AzureTTSProvider, ElevenLabsTTSProvider


def build_asr_provider() -> ASRProvider:
    if settings.asr_provider == "google":
        return GoogleASRProvider()
    return DeepgramASRProvider()


def build_tts_provider() -> TTSProvider:
    if settings.tts_provider == "azure":
        return AzureTTSProvider()
    return ElevenLabsTTSProvider()


def build_llm_provider() -> LLMProvider:
    if settings.llm_provider == "anthropic":
        return AnthropicLLMProvider()
    return OpenAILLMProvider()

