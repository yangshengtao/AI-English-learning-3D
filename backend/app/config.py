from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "English Tutor Realtime API"
    env: str = "dev"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    asr_provider: str = "deepgram"
    tts_provider: str = "elevenlabs"
    llm_provider: str = "openai"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
