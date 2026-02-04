import logging
import json
import re
import hashlib
import time
import os
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from config import get_settings
from models import (
    RoastRequest,
    RoastResponse,
    ErrorResponse,
    AnimeStats,
    AnimeSearchResult,
    AnimeDetails,
    ReviewAnalysis,
)
from security import (
    SecurityManager,
    get_limiter,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RateLimitInfoMiddleware,
)
from anilist_client import get_anilist_client, close_anilist_client
from enhanced_review_analyzer import EnhancedReviewAnalyzer
from simple_context_builder import SimpleContextBuilder
from roast_cleaner import RoastCleaner


# Configure structured logging
class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Check for request_id in extra attributes
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_data["request_id"] = request_id
        return json.dumps(log_data)


# Setup logging
handler = logging.StreamHandler()
handler.setFormatter(StructuredLogFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Initialize FastAPI app with request size limit
app = FastAPI(
    title="Anime Roast Generator API",
    description="Generate witty, sarcastic roasts for your favorite anime",
    version="1.0.0",
)

# Get settings
settings = get_settings()

# Add security middleware (must be before CORS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitInfoMiddleware)

# Configure CORS - whitelist only
allowed_origins = []
if settings.frontend_url:
    allowed_origins.append(settings.frontend_url)

# Only add localhost in development
if os.getenv("ENVIRONMENT", "production") != "production":
    allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
    max_age=600,  # 10 minutes cache for preflight
)

# Configure rate limiting
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure Gemini with timeout
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
else:
    logger.error("GEMINI_API_KEY not set!")

# Simple in-memory cache for Gemini responses
_response_cache = {}
CACHE_TTL = 3600  # 1 hour


def get_cached_response(cache_key: str) -> Optional[dict]:
    """Get cached response if not expired."""
    if cache_key in _response_cache:
        cached_data, timestamp = _response_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"Cache hit for key: {cache_key[:16]}...")
            return cached_data
        else:
            del _response_cache[cache_key]
    return None


def set_cached_response(cache_key: str, data: dict):
    """Cache response with timestamp."""
    _response_cache[cache_key] = (data, time.time())
    # Clean old cache entries periodically
    if len(_response_cache) > 1000:
        current_time = time.time()
        expired_keys = [
            k for k, (_, ts) in _response_cache.items() if current_time - ts > CACHE_TTL
        ]
        for k in expired_keys:
            del _response_cache[k]


def generate_cache_key(anime_name: str, review_context: Optional[dict]) -> str:
    """Generate cache key from request data."""
    key_data = f"{anime_name}:{json.dumps(review_context, sort_keys=True) if review_context else 'none'}"
    return hashlib.sha256(key_data.encode()).hexdigest()


def generate_roast_and_stats_prompt(
    anime_name: str,
    anime_data: Optional[dict] = None,
    review_context: Optional[dict] = None,
) -> str:
    """Generate the prompt for Gemini to create a roast and stats.

    Uses simplified qualitative context for natural, witty roasts.
    """
    # Sanitize anime name for prompt
    safe_anime_name = SecurityManager.sanitize_for_prompt(anime_name)

    # Build simplified qualitative context
    if anime_data:
        data_context = SimpleContextBuilder.build_context(anime_data, review_context)
        constraints = SimpleContextBuilder.build_constraints()
    else:
        data_context = f"Anime: {safe_anime_name}\nNo detailed data available."
        constraints = "=== ROASTING RULES ===\n1. Keep it generic but funny\n2. Focus on common anime tropes\n3. Don't make specific claims about quality"

    prompt = f"""You are a witty anime critic writing a satirical roast. Write like a sarcastic friend roasting a buddy's questionable taste.

=== CONTEXT (use as background, don't quote directly) ===
{data_context}

{constraints}

=== WRITING STYLE ===
- Conversational and natural, not robotic
- Witty and sarcastic but playful
- Mock tropes and expectations, not data points
- Use irony and hyperbole
- Reference community sentiment without quoting statistics
- The roast should be quotable and funny, not a data report

Return in this format:

ROAST:
[Your natural, conversational roast here - 100-150 words]

STATS:
{{
  "horniness_level": 0-100,
  "plot_armor_thickness": 0-100,
  "filler_hell": 0-100,
  "power_creep": 0-100,
  "cringe_factor": 0-100,
  "fan_toxicity": 0-100
}}"""

    return prompt


def parse_roast_response(response_text: str) -> tuple[str, dict]:
    """Parse the Gemini response to extract roast and stats."""
    try:
        # Split on STATS: marker
        if "STATS:" in response_text:
            parts = response_text.split("STATS:", 1)
            roast_part = parts[0].strip()
            stats_part = parts[1].strip()

            # Remove ROAST: prefix if present
            if roast_part.startswith("ROAST:"):
                roast_part = roast_part[6:].strip()

            # Extract JSON from stats part
            json_match = re.search(r"\{[^}]+\}", stats_part, re.DOTALL)
            if json_match:
                stats_json = json_match.group(0)
                stats = json.loads(stats_json)
                return roast_part, stats

        logger.warning("Could not parse stats from response, using defaults")
        return response_text.strip(), _get_default_stats()
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return response_text.strip(), _get_default_stats()


def _get_default_stats() -> dict:
    """Get default stats."""
    return {
        "horniness_level": 50,
        "plot_armor_thickness": 50,
        "filler_hell": 50,
        "power_creep": 50,
        "cringe_factor": 50,
        "fan_toxicity": 50,
    }


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Anime Roast Generator API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.get("/api/search-anime")
@limiter.limit("30/minute")
async def search_anime(request: Request, q: str = ""):
    """
    Search for anime titles as user types.
    Rate limited to 30 requests per minute per IP.
    """
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}

    try:
        client = get_anilist_client()
        results = await client.search_anime(q.strip(), per_page=10)
        anime_results = [AnimeSearchResult(**result) for result in results]

        return {
            "results": [result.dict() for result in anime_results],
            "query": q.strip(),
            "count": len(anime_results),
        }

    except Exception as e:
        logger.error(f"Error searching anime: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to search anime. Please try again later."
        )


@app.get("/api/anime/{anime_id}")
@limiter.limit("30/minute")
async def get_anime_details(request: Request, anime_id: int):
    """Get detailed information about a specific anime by AniList ID."""
    try:
        client = get_anilist_client()
        anime = await client.get_anime_by_id(anime_id)

        if not anime:
            raise HTTPException(
                status_code=404, detail=f"Anime with ID {anime_id} not found"
            )

        anime_details = AnimeDetails(**anime)
        return anime_details.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching anime details: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch anime details. Please try again later.",
        )


@app.post("/api/generate-roast", response_model=RoastResponse)
@limiter.limit("10/minute")
async def generate_roast(request: Request, roast_request: RoastRequest):
    """
    Generate a roast and stats for the specified anime.
    Rate limited to 10 requests per minute per IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # Validate input
        anime_name = SecurityManager.validate_anime_name(roast_request.anime_name)
        logger.info(f"[{request_id}] Generating roast for: {anime_name}")

        # Fetch anime details and reviews
        cover_image = None
        anime_id = None
        anime_details = None
        anime_data = None
        enhanced_context = None
        reviews_used = 0

        if roast_request.anime_id:
            try:
                client = get_anilist_client()
                anime_data = await client.get_anime_by_id(roast_request.anime_id)
                if anime_data:
                    anime_id = roast_request.anime_id
                    cover_image = anime_data.get("coverImage", {}).get("large")
                    anime_details = AnimeDetails(**anime_data)

                reviews = await client.get_anime_reviews(
                    roast_request.anime_id, per_page=25
                )
                if reviews and anime_data:
                    # Use enhanced analyzer with anime data context
                    enhanced_context = (
                        EnhancedReviewAnalyzer.format_enhanced_review_context(
                            reviews, anime_data
                        )
                    )
                    reviews_used = len(reviews)
                    logger.info(
                        f"[{request_id}] Fetched {reviews_used} reviews, found {len(enhanced_context.get('verified_complaints', []))} verified complaints"
                    )
                else:
                    enhanced_context = None
            except Exception as e:
                logger.warning(f"[{request_id}] Could not fetch details: {e}")

        # Check cache first
        cache_key = generate_cache_key(anime_name, enhanced_context)
        cached_response = get_cached_response(cache_key)

        if cached_response:
            logger.info(f"[{request_id}] Returning cached response")
            SecurityManager.log_request(request, anime_name, success=True)
            return RoastResponse(
                anime_name=cached_response["anime_name"],
                roast=cached_response["roast"],
                stats=AnimeStats(**cached_response["stats"]),
                cover_image=cover_image,
                anime_id=anime_id,
                anime_details=anime_details,
                success=True,
            )

        # Generate roast with validation and retry
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = generate_roast_and_stats_prompt(
            anime_name, anime_data, enhanced_context
        )

        max_retries = 2
        roast_text = None
        stats_data = None
        validation_issues = []

        for attempt in range(max_retries + 1):
            try:
                # Add 30 second timeout for Gemini API
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt), timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"[{request_id}] Gemini API timeout (attempt {attempt + 1})"
                )
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=504,
                        detail="AI generation timed out. Please try again.",
                    )
                continue

            if not response or not response.text:
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to generate roast - empty response from AI",
                    )
                continue

            current_roast, current_stats = parse_roast_response(response.text)

            # Clean statistical language from roast
            current_roast = RoastCleaner.clean_roast(current_roast)

            # Check if still has statistics after cleaning
            if RoastCleaner.has_statistics(current_roast) and attempt < max_retries:
                logger.warning(
                    f"[{request_id}] Roast still has statistics after cleaning, retrying (attempt {attempt + 1})"
                )
                # Add stronger constraint for retry
                prompt += "\n\nIMPORTANT: Remove all percentages, review counts, and exact scores. Write naturally without statistics."
                continue

            roast_text = current_roast
            stats_data = current_stats
            break

        # Ensure we have valid roast data
        if roast_text is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate a valid roast after multiple attempts",
            )

        # Ensure we have valid stats
        if stats_data is None:
            stats_data = _get_default_stats()

        stats = AnimeStats(
            horniness_level=stats_data.get("horniness_level", 50),
            plot_armor_thickness=stats_data.get("plot_armor_thickness", 50),
            filler_hell=stats_data.get("filler_hell", 50),
            power_creep=stats_data.get("power_creep", 50),
            cringe_factor=stats_data.get("cringe_factor", 50),
            fan_toxicity=stats_data.get("fan_toxicity", 50),
        )

        # Cache successful response
        response_data = {
            "anime_name": anime_name,
            "roast": roast_text,
            "stats": stats.dict(),
        }
        set_cached_response(cache_key, response_data)

        SecurityManager.log_request(request, anime_name, success=True)

        return RoastResponse(
            anime_name=anime_name,
            roast=roast_text,
            stats=stats,
            cover_image=cover_image,
            anime_id=anime_id,
            anime_details=anime_details,
            success=True,
        )

    except HTTPException:
        SecurityManager.log_request(
            request, roast_request.anime_name, success=False, error_message="HTTP error"
        )
        raise
    except google_exceptions.ResourceExhausted:
        logger.error(f"[{request_id}] Gemini API quota exceeded")
        SecurityManager.log_request(
            request,
            roast_request.anime_name,
            success=False,
            error_message="Quota exceeded",
        )
        raise HTTPException(
            status_code=429,
            detail="API rate limit reached. Please wait a minute before trying again.",
        )
    except google_exceptions.InvalidArgument as e:
        logger.error(f"[{request_id}] Invalid request to Gemini: {e}")
        SecurityManager.log_request(
            request,
            roast_request.anime_name,
            success=False,
            error_message="Invalid argument",
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid request. Please check your input and try again.",
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{request_id}] Error generating roast: {error_msg}")
        SecurityManager.log_request(
            request, roast_request.anime_name, success=False, error_message=error_msg
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate roast. Please try again later.",
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail, error_code="HTTP_ERROR").dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An unexpected error occurred", error_code="INTERNAL_ERROR"
        ).dict(),
    )


if __name__ == "__main__":
    import uvicorn
    import os
    import asyncio

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        limit_max_requests=10000,  # Restart worker after 10k requests
        timeout_keep_alive=30,
    )
