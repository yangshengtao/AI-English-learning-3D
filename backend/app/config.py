from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "English Tutor Realtime API"
    env: str = "dev"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    asr_provider: str = "deepgram"
    tts_provider: str = "elevenlabs"
    llm_provider: str = "deepseek"

    # DeepSeek is OpenAI-compatible; see https://api-docs.deepseek.com/
    # Fill in a real key via .env or the DEEPSEEK_API_KEY environment variable.
    deepseek_api_key: str = "REPLACE_WITH_DEEPSEEK_API_KEY"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    # Deepgram prerecorded transcription; see https://developers.deepgram.com/docs/pre-recorded-audio
    # Fill in a real key via .env or the DEEPGRAM_API_KEY environment variable.
    deepgram_api_key: str = "REPLACE_WITH_DEEPGRAM_API_KEY"
    deepgram_base_url: str = "https://api.deepgram.com/v1/listen"
    deepgram_model: str = "nova-3"

    # Deepgram Aura-2 text-to-speech; see https://developers.deepgram.com/docs/text-to-speech
    # Reuses DEEPGRAM_API_KEY above (same account as ASR) — no separate key needed.
    deepgram_tts_base_url: str = "https://api.deepgram.com/v1/speak"
    deepgram_tts_model: str = "aura-2-thalia-en"
    deepgram_tts_sample_rate: int = 24000

    # Alibaba Cloud Intelligent Speech Interaction (NLS) — one-sentence recognition.
    # Docs: https://help.aliyun.com/zh/isi/developer-reference/restful-api-2
    # AccessKeyId/Secret are used to auto-fetch a short-lived X-NLS-Token; AppKey comes
    # from an NLS project created in the Intelligent Speech Interaction console.
    # Only mono audio at 8000/16000 Hz is supported — see mobile/src/services/audioRecorder.ts.
    alibaba_access_key_id: str = "REPLACE_WITH_ALIBABA_ACCESS_KEY_ID"
    alibaba_access_key_secret: str = "REPLACE_WITH_ALIBABA_ACCESS_KEY_SECRET"
    alibaba_app_key: str = "REPLACE_WITH_ALIBABA_APP_KEY"
    alibaba_region: str = "cn-shanghai"
    alibaba_asr_base_url: str = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"
    alibaba_token_base_url: str = "https://nls-meta.cn-shanghai.aliyuncs.com/"
    alibaba_sample_rate: int = 16000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
