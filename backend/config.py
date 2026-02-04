from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-lite"

    # CORS
    frontend_url: str = "http://localhost:3000"
    allowed_origins: list = ["http://localhost:3000"]

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # Redis (optional, for distributed rate limiting)
    redis_url: str = "redis://redis:6379/0"
    use_redis: bool = False

    # Logging
    log_requests: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
