from app.config import settings
from app.providers.asr_provider import AlibabaASRProvider, DeepgramASRProvider, GoogleASRProvider
from app.providers.base import ASRProvider, LLMProvider, TTSProvider
from app.providers.llm_provider import AnthropicLLMProvider, DeepSeekLLMProvider, OpenAILLMProvider
from app.providers.tts_provider import AlibabaTTSProvider, AzureTTSProvider, DeepgramTTSProvider, ElevenLabsTTSProvider


def build_asr_provider() -> ASRProvider:
    if settings.asr_provider == "google":
        return GoogleASRProvider()
    if settings.asr_provider == "alibaba":
        return AlibabaASRProvider()
    return DeepgramASRProvider()


def build_tts_provider() -> TTSProvider:
    if settings.tts_provider == "azure":
        return AzureTTSProvider()
    if settings.tts_provider == "deepgram":
        return DeepgramTTSProvider()
    if settings.tts_provider == "alibaba":
        return AlibabaTTSProvider()
    return ElevenLabsTTSProvider()


def build_llm_provider() -> LLMProvider:
    if settings.llm_provider == "deepseek":
        return DeepSeekLLMProvider()
    if settings.llm_provider == "anthropic":
        return AnthropicLLMProvider()
    return OpenAILLMProvider()

