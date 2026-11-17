from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Claude API
    anthropic_api_key: str

    # Databases
    postgres_url: str
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"

    # Mem0
    mem0_qdrant_url: str = "http://localhost:6333"
    mem0_collection: str = "ema_memories"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Model routing thresholds
    haiku_arousal_threshold: float = 0.3
    opus_complexity_threshold: float = 0.8

    # Canary
    canary_prefix: str = "EMA"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
