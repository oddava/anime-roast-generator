from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-lite"

    # CORS - Updated for Vercel deployment
    frontend_url: str = "http://localhost:3000"

    @property
    def allowed_origins(self) -> list:
        """Get allowed CORS origins based on environment."""
        origins = ["http://localhost:3000"]

        # Add production URL from env
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)

        # Add Vercel preview deployments
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            preview_url = f"https://{vercel_url}"
            if preview_url not in origins:
                origins.append(preview_url)

        # Add additional origins from env (comma-separated)
        additional_origins = os.getenv("ADDITIONAL_ORIGINS", "")
        if additional_origins:
            for origin in additional_origins.split(","):
                origin = origin.strip()
                if origin and origin not in origins:
                    origins.append(origin)

        return origins

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # Redis (optional, for distributed rate limiting)
    redis_url: str = "redis://redis:6379/0"
    use_redis: bool = False

    # Upstash Redis for Vercel
    upstash_redis_url: str = ""

    # Logging
    log_requests: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
