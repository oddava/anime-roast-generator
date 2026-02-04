"""Security middleware and utilities for the Anime Roast Generator API."""

import re
import logging
import os
import secrets
import hashlib
import time
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(
        self,
        app: ASGIApp,
        csp_policy: Optional[str] = None,
    ):
        super().__init__(app)
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://graphql.anilist.co; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = self.csp_policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Remove server header if present
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next):
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", secrets.token_hex(16))
        request.state.request_id = request_id

        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class RateLimitInfoMiddleware(BaseHTTPMiddleware):
    """Add rate limit information to responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add rate limit headers if available
        try:
            limit_info = getattr(request.state, "view_rate_limit", None)
            if limit_info is not None:
                # slowapi may store this as an object or a tuple
                limit_val = remaining = reset = None

                # Object style (has attributes)
                if hasattr(limit_info, "limit") or hasattr(limit_info, "remaining"):
                    limit_val = getattr(limit_info, "limit", None)
                    remaining = getattr(limit_info, "remaining", None)
                    reset = getattr(limit_info, "reset", None) or getattr(
                        limit_info, "reset_at", None
                    )
                # Tuple/list style: (limit, remaining, reset)
                elif isinstance(limit_info, (tuple, list)):
                    if len(limit_info) >= 1:
                        limit_val = limit_info[0]
                    if len(limit_info) >= 2:
                        remaining = limit_info[1]
                    if len(limit_info) >= 3:
                        reset = limit_info[2]

                if limit_val is not None:
                    response.headers["X-RateLimit-Limit"] = str(limit_val)
                if remaining is not None:
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                if reset is not None:
                    response.headers["X-RateLimit-Reset"] = str(reset)
        except Exception:
            # Never let header enrichment break the request
            pass

        return response


class SecurityManager:
    """Handles security concerns: validation, rate limiting, logging."""

    # Regex patterns for input validation
    # Allow alphanumeric, spaces, and common punctuation used in anime titles
    # Includes Unicode smart quotes (U+2018, U+2019) that AniList uses
    # Use explicit space character instead of \s to avoid allowing tabs/newlines
    # Includes forward slash for titles like "Fate/stay night"
    ANIME_NAME_PATTERN = re.compile(r"^[\w '\u2018\u2019\-:!?.;,()/\[\]{}\"]{1,100}$")

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

    # Prompt injection patterns for AI sanitization
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+(instructions|prompt)",
        r"disregard\s+(previous|above|all)",
        r"system\s*:",
        r"user\s*:",
        r"assistant\s*:",
        r"you\s+are\s+now",
        r"new\s+instructions",
        r"forget\s+(everything|all|previous)",
        r"act\s+as\s+(if\s+)?you\s+(are|were)",
        r"pretend\s+(to\s+be|you\s+are)",
        r"roleplay\s+as",
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
    def sanitize_for_prompt(cls, text: str, max_length: int = 2000) -> str:
        """
        Sanitize text for use in AI prompts to prevent prompt injection.

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text safe for AI prompts
        """
        if not text:
            return ""

        # Truncate to prevent token abuse
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Remove control characters except newlines
        text = "".join(
            char
            for char in text
            if char == "\n" or (ord(char) >= 32 and ord(char) <= 126) or ord(char) > 127
        )

        # Check for prompt injection attempts
        lower_text = text.lower()
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lower_text):
                logger.warning("Potential prompt injection attempt detected")
                # Remove the suspicious text section
                text = re.sub(pattern, "[REMOVED]", text, flags=re.IGNORECASE)

        # Escape special characters that could be used for injection
        text = text.replace("{", "{{").replace("}", "}}")

        return text.strip()

    @classmethod
    def sanitize_review_context(cls, review_context: Optional[dict]) -> Optional[dict]:
        """
        Sanitize review context data before passing to AI.

        Args:
            review_context: Dictionary containing review analysis data

        Returns:
            Sanitized review context or None if input is None
        """
        if not review_context:
            return None

        sanitized = {}

        # Sanitize simple fields
        if "review_count" in review_context:
            sanitized["review_count"] = min(int(review_context["review_count"]), 100)

        if "average_rating" in review_context:
            try:
                rating = float(review_context["average_rating"])
                sanitized["average_rating"] = max(0, min(rating, 10))
            except (ValueError, TypeError):
                sanitized["average_rating"] = None

        # Sanitize text lists
        if "top_criticisms" in review_context:
            criticisms = review_context["top_criticisms"]
            if isinstance(criticisms, list):
                sanitized["top_criticisms"] = [
                    cls.sanitize_for_prompt(str(c), max_length=100)
                    for c in criticisms[:5]
                ]
            else:
                sanitized["top_criticisms"] = []

        if "summary" in review_context:
            sanitized["summary"] = cls.sanitize_for_prompt(
                str(review_context["summary"]), max_length=500
            )

        if "spicy_quotes" in review_context:
            quotes = review_context.get("spicy_quotes", [])
            if isinstance(quotes, list):
                sanitized["spicy_quotes"] = [
                    cls.sanitize_for_prompt(str(q), max_length=200) for q in quotes[:2]
                ]
            else:
                sanitized["spicy_quotes"] = []

        return sanitized

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
        request_id = getattr(request.state, "request_id", "unknown")
        timestamp = datetime.utcnow().isoformat()

        # Hash IP for privacy
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

        log_data = {
            "timestamp": timestamp,
            "request_id": request_id,
            "ip_hash": ip_hash,
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
        # Use Redis storage for distributed rate limiting
        return Limiter(
            key_func=get_remote_address,
            default_limits=["10 per minute"],
            storage_uri=os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL"),
        )
    else:
        # Fallback to in-memory storage (local development)
        logger.warning("Using in-memory rate limiting - deploy Redis for production")
        return Limiter(key_func=get_remote_address, default_limits=["10 per minute"])
