import re
import logging
import os
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecurityManager:
    """Handles security concerns: validation, rate limiting, logging."""

    # Regex patterns for input validation
    # Allow alphanumeric, spaces, and common punctuation used in anime titles
    ANIME_NAME_PATTERN = re.compile(r"^[\w\s\-':!?.(),\[\]{}\"]{1,100}$")

    # Forbidden patterns (potential injection attempts)
    # These patterns must be standalone SQL keywords, not part of normal words
    FORBIDDEN_PATTERNS = [
        r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)",  # SQL after semicolon
        r"'\s*(OR|AND)\s*['\"\d]",  # SQL injection with quotes
        r"--\s*$",  # SQL comment at end
        r"/\*.*\*/",  # SQL block comments
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
    ]

    # Redis client for distributed rate limiting (Vercel/Upstash)
    _redis_client = None

    @classmethod
    def get_redis_client(cls):
        """Get or create Redis client for rate limiting."""
        if cls._redis_client is None:
            redis_url = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")
            if redis_url:
                try:
                    import redis

                    cls._redis_client = redis.from_url(redis_url)
                    logger.info("Redis client initialized for rate limiting")
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis: {e}")
        return cls._redis_client

    @classmethod
    def validate_anime_name(cls, name: str) -> str:
        """
        Validate and sanitize anime name.

        Args:
            name: Raw anime name input

        Returns:
            Sanitized anime name

        Raises:
            HTTPException: If validation fails
        """
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Anime name cannot be empty")

        # Strip whitespace
        name = name.strip()

        # Check length
        if len(name) > 100:
            raise HTTPException(
                status_code=400, detail="Anime name too long (max 100 characters)"
            )

        # Check for forbidden patterns (potential injection)
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                logger.warning(f"Potential injection attempt detected: {name[:50]}...")
                raise HTTPException(
                    status_code=400, detail="Invalid characters in anime name"
                )

        # Validate against allowed pattern
        if not cls.ANIME_NAME_PATTERN.match(name):
            raise HTTPException(
                status_code=400, detail="Anime name contains invalid characters"
            )

        return name

    @classmethod
    def log_request(
        cls,
        request: Request,
        anime_name: str,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """
        Log request details for monitoring.

        Args:
            request: FastAPI request object
            anime_name: The anime name being roasted
            success: Whether the request succeeded
            error_message: Optional error message
        """
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")
        timestamp = datetime.utcnow().isoformat()

        log_data = {
            "timestamp": timestamp,
            "ip": client_ip,
            "anime": anime_name[:50],  # Truncate for privacy
            "success": success,
            "user_agent": user_agent[:100],  # Truncate
        }

        if error_message:
            log_data["error"] = error_message[:200]

        if success:
            logger.info(f"Request processed: {log_data}")
        else:
            logger.warning(f"Request failed: {log_data}")


def get_limiter() -> Limiter:
    """Create and configure rate limiter with Redis storage if available."""
    redis_client = SecurityManager.get_redis_client()

    if redis_client:
        # Use Redis storage for distributed rate limiting (Vercel)
        return Limiter(
            key_func=get_remote_address,
            default_limits=["10 per minute"],
            storage_uri=os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL"),
        )
    else:
        # Fallback to in-memory storage (local development)
        return Limiter(key_func=get_remote_address, default_limits=["10 per minute"])
