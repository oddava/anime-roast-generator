import logging
import json
import re
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import google.generativeai as genai

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
from security import SecurityManager, get_limiter
from anilist_client import get_anilist_client, close_anilist_client
from review_analyzer import ReviewAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Anime Roast Generator API",
    description="Generate witty, sarcastic roasts for your favorite anime",
    version="1.0.0",
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Configure rate limiting
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
else:
    logger.error("GEMINI_API_KEY not set!")


def generate_roast_and_stats_prompt(
    anime_name: str, review_context: dict | None = None
) -> str:
    """Generate the prompt for Gemini to create a roast and stats."""
    base_prompt = f"""Generate a witty, sarcastic roast for the anime "{anime_name}" AND provide humorous statistics."""

    if review_context and review_context.get("review_count", 0) > 0:
        base_prompt += f"""

COMMUNITY DATA FROM ANILIST REVIEWS:
- Reviews Analyzed: {review_context["review_count"]}
- Average Rating: {review_context.get("average_rating", "N/A")}/10
- Top Criticisms: {", ".join(review_context.get("top_criticisms", [])[:5])}
- Community Sentiment: {review_context.get("summary", "Mixed reviews")}

Use this community data to make your roast more accurate and specific. Reference actual complaints fans have made."""

    base_prompt += """

Return your response in this exact format:

ROAST:
[Your 100-150 word roast here - funny, playful and chaotic NOT mean-spirited. Focus on anime tropes, fanbase stereotypes, plot inconsistencies, overused clichés. Written in a comedic, roasting style."""

    if review_context and review_context.get("review_count", 0) > 0:
        base_prompt += """ Use current anime community slang like "mid", "cope", "carried by", "fell off", "peaked", etc. Reference specific criticisms from the community data above."""

    base_prompt += """]

STATS:
{
  "horniness_level": [0-100, fan service/ecchi content],
  "plot_armor_thickness": [0-100, protagonist invincibility],
  "filler_hell": [0-100, percentage of filler episodes],
  "power_creep": [0-100, power scaling absurdity],
  "cringe_factor": [0-100, awkward moments and tropes],
  "fan_toxicity": [0-100, fanbase intensity level]
}

Make the stats exaggerated and funny based on real anime tropes. All values must be integers between 0 and 100."""

    return base_prompt


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
            # Look for JSON object pattern
            json_match = re.search(r"\{[^}]+\}", stats_part, re.DOTALL)
            if json_match:
                stats_json = json_match.group(0)
                stats = json.loads(stats_json)
                return roast_part, stats

        # Fallback: return entire text as roast, default stats
        logger.warning("Could not parse stats from response, using defaults")
        return response_text.strip(), {
            "horniness_level": 50,
            "plot_armor_thickness": 50,
            "filler_hell": 50,
            "power_creep": 50,
            "cringe_factor": 50,
            "fan_toxicity": 50,
        }
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return response_text.strip(), {
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
    Returns up to 10 anime suggestions.
    """
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}

    try:
        client = get_anilist_client()
        results = await client.search_anime(q.strip(), per_page=10)

        # Convert to Pydantic models for validation
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
    """
    Get detailed information about a specific anime by AniList ID.

    Rate limited to 30 requests per minute per IP.
    """
    try:
        client = get_anilist_client()
        anime = await client.get_anime_by_id(anime_id)

        if not anime:
            raise HTTPException(
                status_code=404, detail=f"Anime with ID {anime_id} not found"
            )

        # Convert to Pydantic model
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
    try:
        # Validate input
        anime_name = SecurityManager.validate_anime_name(roast_request.anime_name)

        logger.info(f"Generating roast and stats for: {anime_name}")

        # Fetch anime details and reviews if ID provided
        cover_image = None
        anime_id = None
        anime_details = None
        review_analysis = None
        reviews_used = 0

        if roast_request.anime_id:
            try:
                client = get_anilist_client()
                anime_data = await client.get_anime_by_id(roast_request.anime_id)
                if anime_data:
                    anime_id = roast_request.anime_id
                    cover_image = anime_data.get("coverImage", {}).get("large")
                    anime_details = AnimeDetails(**anime_data)

                # Fetch reviews for this anime
                reviews = await client.get_anime_reviews(
                    roast_request.anime_id, per_page=25
                )
                if reviews:
                    analysis_data = ReviewAnalyzer.create_review_summary(reviews)
                    review_analysis = ReviewAnalysis(**analysis_data)
                    reviews_used = len(reviews)
                    logger.info(
                        f"Fetched {reviews_used} reviews for anime {anime_name}"
                    )
            except Exception as e:
                logger.warning(f"Could not fetch anime details or reviews: {e}")

        # Generate roast and stats using Gemini with review context
        model = genai.GenerativeModel(settings.gemini_model)
        review_context = review_analysis.dict() if review_analysis else None
        prompt = generate_roast_and_stats_prompt(anime_name, review_context)

        response = model.generate_content(prompt)

        if not response or not response.text:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate roast - empty response from AI",
            )

        # Parse response to extract roast and stats
        roast_text, stats_data = parse_roast_response(response.text)

        # Create AnimeStats object
        stats = AnimeStats(
            horniness_level=stats_data.get("horniness_level", 50),
            plot_armor_thickness=stats_data.get("plot_armor_thickness", 50),
            filler_hell=stats_data.get("filler_hell", 50),
            power_creep=stats_data.get("power_creep", 50),
            cringe_factor=stats_data.get("cringe_factor", 50),
            fan_toxicity=stats_data.get("fan_toxicity", 50),
        )

        # Log successful request
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

        # Parse response to extract roast and stats
        roast_text, stats_data = parse_roast_response(response.text)

        # Create AnimeStats object
        stats = AnimeStats(
            horniness_level=stats_data.get("horniness_level", 50),
            plot_armor_thickness=stats_data.get("plot_armor_thickness", 50),
            filler_hell=stats_data.get("filler_hell", 50),
            power_creep=stats_data.get("power_creep", 50),
            cringe_factor=stats_data.get("cringe_factor", 50),
            fan_toxicity=stats_data.get("fan_toxicity", 50),
        )

        # Fetch anime details if ID provided
        cover_image = None
        anime_id = None
        anime_details = None

        if roast_request.anime_id:
            try:
                client = get_anilist_client()
                anime_data = await client.get_anime_by_id(roast_request.anime_id)
                if anime_data:
                    anime_id = roast_request.anime_id
                    cover_image = anime_data.get("coverImage", {}).get("large")
                    anime_details = AnimeDetails(**anime_data)
            except Exception as e:
                logger.warning(f"Could not fetch anime details: {e}")

        # Log successful request
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
        # Re-raise HTTP exceptions
        SecurityManager.log_request(
            request,
            roast_request.anime_name,
            success=False,
            error_message="Validation failed",
        )
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating roast: {error_msg}")
        SecurityManager.log_request(
            request, roast_request.anime_name, success=False, error_message=error_msg
        )

        # Check for specific Gemini API errors
        if "429" in error_msg or "Resource exhausted" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="API rate limit reached. Please wait a minute before trying again.",
            )
        elif "400" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid request. Please check your input and try again.",
            )
        else:
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
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An unexpected error occurred", error_code="INTERNAL_ERROR"
        ).dict(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
