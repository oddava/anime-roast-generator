import logging
import json
import re
import os
import asyncio
import hashlib
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
    CommentCreate,
    CommentResponse,
    CommentListResponse,
    ThreadedCommentResponse,
    ThreadedCommentListResponse,
    CommentReplyRequest,
    CommentVoteRequest,
    CommentVoteResponse,
    CommentEditRequest,
    CommentEditResponse,
)
from security import (
    SecurityManager,
    get_limiter,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RateLimitInfoMiddleware,
)
from anilist_client import AniListClient
from enhanced_review_analyzer import EnhancedReviewAnalyzer
from simple_context_builder import SimpleContextBuilder
from roast_cleaner import RoastCleaner
from cache import get_cache
from database import init_db, get_db, Comment, CommentVote
from name_generator import generate_random_name, hash_ip
from spam_detector import check_spam
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import Depends
from constants import (
    ROAST_RATE_LIMIT_PER_MINUTE,
    SEARCH_RATE_LIMIT_PER_MINUTE,
    ANIME_DETAILS_RATE_LIMIT_PER_MINUTE,
    COMMENT_CREATE_RATE_LIMIT_PER_MINUTE,
    COMMENT_VOTE_RATE_LIMIT_PER_MINUTE,
    COMMENT_EDIT_RATE_LIMIT_PER_MINUTE,
    COMMENT_DELETE_RATE_LIMIT_PER_MINUTE,
    MAX_COMMENT_LENGTH,
    MAX_AUTHOR_NAME_LENGTH,
    COMMENT_EDIT_TIME_LIMIT_SECONDS,
    MAX_COMMENT_DEPTH,
    DEFAULT_COMMENTS_PER_PAGE,
    MAX_COMMENTS_PER_PAGE,
    MIN_SEARCH_QUERY_LENGTH,
    MAX_SEARCH_QUERY_LENGTH,
    DEFAULT_SEARCH_RESULTS,
    MAX_SEARCH_RESULTS,
    MAX_ANIME_NAME_LENGTH,
    GEMINI_API_TIMEOUT_SECONDS,
    MAX_ROAST_RETRIES,
    DEFAULT_STATS,
    FRONTEND_API_TIMEOUT_MS,
)


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

# Add response compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure Gemini with timeout
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
else:
    logger.error("GEMINI_API_KEY not set!")

# Initialize cache
_cache = get_cache()


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()
    logger.info("Database initialized")


def generate_cache_key(anime_name: str, review_context: Optional[dict]) -> str:
    """Generate cache key from request data using deterministic hash."""
    key_data = f"{anime_name}:{json.dumps(review_context, sort_keys=True) if review_context else 'none'}"
    return hashlib.sha256(key_data.encode()).hexdigest()[:32]  # Deterministic hash


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
    return DEFAULT_STATS.copy()


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
@limiter.limit(f"{SEARCH_RATE_LIMIT_PER_MINUTE}/minute")
async def search_anime(request: Request, q: str = ""):
    """
    Search for anime titles as user types.
    Rate limited to 30 requests per minute per IP.
    """
    if not q or len(q.strip()) < MIN_SEARCH_QUERY_LENGTH:
        return {"results": [], "query": q}

    if len(q) > MAX_SEARCH_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="Search query too long")

    client = None
    try:
        client = AniListClient()
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
    finally:
        if client:
            await client.close()


@app.get("/api/anime/{anime_id}")
@limiter.limit("30/minute")
async def get_anime_details(request: Request, anime_id: int):
    """Get detailed information about a specific anime by AniList ID."""
    client = None
    try:
        client = AniListClient()
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
    finally:
        if client:
            await client.close()


@app.post("/api/generate-roast", response_model=RoastResponse)
@limiter.limit(f"{ROAST_RATE_LIMIT_PER_MINUTE}/minute")
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

        client = None
        if roast_request.anime_id:
            try:
                client = AniListClient()
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
            finally:
                if client:
                    await client.close()

        # Check cache first
        cache_key = generate_cache_key(anime_name, enhanced_context)
        cached_response = await _cache.get(cache_key)

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

        max_retries = MAX_ROAST_RETRIES
        roast_text = None
        stats_data = None
        validation_issues = []

        for attempt in range(max_retries + 1):
            try:
                # Add timeout for Gemini API
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt),
                    timeout=GEMINI_API_TIMEOUT_SECONDS,
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
        await _cache.set(cache_key, response_data)

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


def build_comment_tree(
    comments: list, user_ip_hash: str, db: Session, max_depth: int = 3
) -> list:
    """Build threaded comment tree structure with optimized vote fetching."""
    comment_map = {}
    root_comments = []

    # Batch fetch all user votes in a single query to avoid N+1
    comment_ids = [c.id for c in comments]
    votes_map = {}
    if comment_ids:
        votes = (
            db.query(CommentVote.comment_id, CommentVote.vote_type)
            .filter(
                CommentVote.comment_id.in_(comment_ids),
                CommentVote.ip_hash == user_ip_hash,
            )
            .all()
        )
        votes_map = {vote.comment_id: vote.vote_type for vote in votes}

    # First pass: create map and identify roots
    for comment in comments:
        user_vote = votes_map.get(comment.id)
        comment_data = ThreadedCommentResponse(
            id=comment.id,
            anime_id=comment.anime_id,
            parent_id=comment.parent_id,
            content=comment.content if not comment.is_deleted else "[deleted]",
            author_name=comment.author_name if not comment.is_deleted else "[deleted]",
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat(),
            is_deleted=comment.is_deleted,
            is_edited=comment.is_edited,
            upvotes=comment.upvotes,
            downvotes=comment.downvotes,
            score=comment.score,
            depth=comment.depth,
            reply_count=comment.reply_count,
            user_vote=user_vote,
            replies=[],
        )
        comment_map[comment.id] = comment_data
        if comment.parent_id is None:
            root_comments.append(comment_data)

    # Second pass: build tree
    for comment in comments:
        if comment.parent_id and comment.parent_id in comment_map:
            parent = comment_map[comment.parent_id]
            child = comment_map[comment.id]
            # Only include replies if depth allows
            if child.depth <= max_depth:
                parent.replies.append(child)

    return root_comments


@app.get("/api/anime/{anime_id}/comments", response_model=ThreadedCommentListResponse)
@limiter.limit("60/minute")
async def get_comments(
    request: Request,
    anime_id: int,
    db: Session = Depends(get_db),
    sort: str = "best",
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """
    Get threaded comments for a specific anime.
    Rate limited to 60 requests per minute per IP.

    Sort options:
    - best: Wilson score (default)
    - new: Chronological, newest first
    - top: Highest score
    """
    try:
        # Validate parameters
        limit = min(max(limit, 1), 50)
        if sort not in ["best", "new", "top"]:
            sort = "best"

        # Get client IP for vote tracking
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hash_ip(client_ip)

        # Build query for root comments only
        query = db.query(Comment).filter(
            Comment.anime_id == anime_id, Comment.parent_id == None
        )

        # Apply sorting
        if sort == "new":
            query = query.order_by(Comment.created_at.desc())
        elif sort == "top":
            query = query.order_by(Comment.score.desc(), Comment.created_at.desc())
        else:  # best
            # Simple score-based sorting for now (can be improved with Wilson score)
            query = query.order_by(Comment.score.desc(), Comment.created_at.desc())

        # Cursor-based pagination
        if cursor:
            try:
                cursor_id = int(cursor)
                if sort == "new":
                    query = query.filter(Comment.id < cursor_id)
                else:
                    query = query.filter(Comment.id < cursor_id)
            except ValueError:
                pass

        # Get root comments
        root_comments = query.limit(limit + 1).all()
        has_more = len(root_comments) > limit
        root_comments = root_comments[:limit]

        # Get all replies for these root comments
        root_ids = [c.id for c in root_comments]
        if root_ids:
            # Get all descendants using path-based query
            all_comments = root_comments.copy()

            # Get direct replies (depth 1)
            replies = (
                db.query(Comment)
                .filter(Comment.parent_id.in_(root_ids))
                .order_by(Comment.score.desc(), Comment.created_at.desc())
                .all()
            )
            all_comments.extend(replies)

            # Get nested replies (depth 2+)
            reply_ids = [r.id for r in replies]
            if reply_ids:
                nested = (
                    db.query(Comment)
                    .filter(Comment.parent_id.in_(reply_ids))
                    .order_by(Comment.score.desc(), Comment.created_at.desc())
                    .all()
                )
                all_comments.extend(nested)

                # Continue for deeper nesting
                nested_ids = [n.id for n in nested]
                if nested_ids:
                    deeper = (
                        db.query(Comment)
                        .filter(Comment.parent_id.in_(nested_ids))
                        .order_by(Comment.score.desc(), Comment.created_at.desc())
                        .limit(100)
                        .all()
                    )
                    all_comments.extend(deeper)
        else:
            all_comments = root_comments

        # Build tree structure
        comment_tree = build_comment_tree(all_comments, ip_hash, db)

        # Get total count
        total = db.query(Comment).filter(Comment.anime_id == anime_id).count()

        return ThreadedCommentListResponse(
            comments=comment_tree, total=total, anime_id=anime_id, has_more=has_more
        )

    except Exception as e:
        logger.error(f"Error fetching comments for anime {anime_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch comments. Please try again later.",
        )


@app.post("/api/anime/{anime_id}/comments", response_model=ThreadedCommentResponse)
@limiter.limit("5/minute")
async def create_comment(
    request: Request,
    anime_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new root comment for an anime.
    Rate limited to 5 comments per minute per IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hash_ip(client_ip)

        # Generate or use provided author name
        author_name = comment_data.author_name or generate_random_name()
        if len(author_name) > 50:
            author_name = author_name[:50]

        # Check for spam using advanced detection
        is_spam, reason = await check_spam(
            db, ip_hash, comment_data.content, author_name
        )
        if is_spam:
            raise HTTPException(status_code=429, detail=reason)

        # Create new comment
        new_comment = Comment(
            anime_id=anime_id,
            content=comment_data.content,
            author_name=author_name,
            ip_hash=ip_hash,
            depth=0,
            path=str(anime_id),
        )

        try:
            db.add(new_comment)
            db.flush()  # Flush to get the ID without committing
            new_comment.path = f"{anime_id}/{new_comment.id}"
            db.commit()
            db.refresh(new_comment)
        except Exception:
            db.rollback()
            raise

        logger.info(
            f"[{request_id}] Created comment {new_comment.id} for anime {anime_id}"
        )

        return ThreadedCommentResponse(
            id=new_comment.id,
            anime_id=new_comment.anime_id,
            parent_id=new_comment.parent_id,
            content=new_comment.content,
            author_name=new_comment.author_name,
            created_at=new_comment.created_at.isoformat(),
            updated_at=new_comment.updated_at.isoformat(),
            is_deleted=new_comment.is_deleted,
            is_edited=new_comment.is_edited,
            upvotes=new_comment.upvotes,
            downvotes=new_comment.downvotes,
            score=new_comment.score,
            depth=new_comment.depth,
            reply_count=new_comment.reply_count,
            user_vote=None,
            replies=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error creating comment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create comment. Please try again later.",
        )


@app.post("/api/comments/{comment_id}/reply", response_model=ThreadedCommentResponse)
@limiter.limit("5/minute")
async def reply_to_comment(
    request: Request,
    comment_id: int,
    reply_data: CommentReplyRequest,
    db: Session = Depends(get_db),
):
    """
    Reply to an existing comment.
    Rate limited to 5 replies per minute per IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hash_ip(client_ip)

        # Find parent comment
        parent = db.query(Comment).filter(Comment.id == comment_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        # Use provided author name or generate new one
        author_name = reply_data.author_name or generate_random_name()
        if len(author_name) > 50:
            author_name = author_name[:50]

        # Check for spam using advanced detection
        is_spam, reason = await check_spam(db, ip_hash, reply_data.content, author_name)
        if is_spam:
            raise HTTPException(status_code=429, detail=reason)

        # Create reply
        reply = Comment(
            anime_id=parent.anime_id,
            parent_id=parent.id,
            content=reply_data.content,
            author_name=author_name,
            ip_hash=ip_hash,
            depth=parent.depth + 1,
            path=f"{parent.path}/{parent.id}",
        )

        try:
            db.add(reply)
            db.flush()  # Flush to get the ID without committing

            # Update parent's reply count
            parent.reply_count += 1

            # Update path with reply ID
            reply.path = f"{parent.path}/{reply.id}"

            db.commit()
            db.refresh(reply)
        except Exception:
            db.rollback()
            raise

        logger.info(f"[{request_id}] Created reply {reply.id} to comment {comment_id}")

        return ThreadedCommentResponse(
            id=reply.id,
            anime_id=reply.anime_id,
            parent_id=reply.parent_id,
            content=reply.content,
            author_name=reply.author_name,
            created_at=reply.created_at.isoformat(),
            updated_at=reply.updated_at.isoformat(),
            is_deleted=reply.is_deleted,
            is_edited=reply.is_edited,
            upvotes=reply.upvotes,
            downvotes=reply.downvotes,
            score=reply.score,
            depth=reply.depth,
            reply_count=reply.reply_count,
            user_vote=None,
            replies=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error creating reply: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create reply. Please try again later.",
        )


@app.post("/api/comments/{comment_id}/vote", response_model=CommentVoteResponse)
@limiter.limit("10/minute")
async def vote_comment(
    request: Request,
    comment_id: int,
    vote_data: CommentVoteRequest,
    db: Session = Depends(get_db),
):
    """
    Vote on a comment (upvote/downvote).
    Rate limited to 10 votes per minute per IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hash_ip(client_ip)

        # Find comment with lock to prevent race conditions
        comment = (
            db.query(Comment).filter(Comment.id == comment_id).with_for_update().first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Prevent self-voting
        if comment.ip_hash == ip_hash:
            raise HTTPException(
                status_code=403, detail="Cannot vote on your own comment"
            )

        # Check existing vote
        existing_vote = (
            db.query(CommentVote)
            .filter(
                CommentVote.comment_id == comment_id, CommentVote.ip_hash == ip_hash
            )
            .first()
        )

        if vote_data.vote_type == 0:
            # Remove vote
            if existing_vote:
                if existing_vote.vote_type == 1:
                    comment.upvotes -= 1
                else:
                    comment.downvotes -= 1
                db.delete(existing_vote)
        else:
            # Add or update vote
            if existing_vote:
                if existing_vote.vote_type == vote_data.vote_type:
                    # Same vote, remove it (toggle)
                    if vote_data.vote_type == 1:
                        comment.upvotes -= 1
                    else:
                        comment.downvotes -= 1
                    db.delete(existing_vote)
                    vote_data.vote_type = 0
                else:
                    # Change vote
                    if existing_vote.vote_type == 1:
                        comment.upvotes -= 1
                        comment.downvotes += 1
                    else:
                        comment.downvotes -= 1
                        comment.upvotes += 1
                    existing_vote.vote_type = vote_data.vote_type
            else:
                # New vote
                new_vote = CommentVote(
                    comment_id=comment_id,
                    ip_hash=ip_hash,
                    vote_type=vote_data.vote_type,
                )
                db.add(new_vote)
                if vote_data.vote_type == 1:
                    comment.upvotes += 1
                else:
                    comment.downvotes += 1

        # Update score
        comment.score = comment.upvotes - comment.downvotes

        db.commit()

        logger.info(
            f"[{request_id}] Vote on comment {comment_id}: {vote_data.vote_type}"
        )

        return CommentVoteResponse(
            comment_id=comment_id,
            upvotes=comment.upvotes,
            downvotes=comment.downvotes,
            score=comment.score,
            user_vote=vote_data.vote_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error voting: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to vote. Please try again later.",
        )


@app.put("/api/comments/{comment_id}", response_model=ThreadedCommentResponse)
@limiter.limit("5/minute")
async def edit_comment(
    request: Request,
    comment_id: int,
    edit_data: CommentEditRequest,
    db: Session = Depends(get_db),
):
    """
    Edit a comment (only own comments, within 15 minutes of creation).
    Rate limited to 5 edits per minute per IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hash_ip(client_ip)

        # Find comment
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check ownership
        if comment.ip_hash != ip_hash:
            raise HTTPException(
                status_code=403, detail="Cannot edit other users' comments"
            )

        # Check time limit (15 minutes)
        time_since_creation = datetime.utcnow() - comment.created_at
        if time_since_creation.total_seconds() > COMMENT_EDIT_TIME_LIMIT_SECONDS:
            raise HTTPException(
                status_code=403,
                detail="Comments can only be edited within 15 minutes of creation",
            )

        # Update comment
        comment.content = edit_data.content
        comment.is_edited = 1
        comment.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"[{request_id}] Edited comment {comment_id}")

        return ThreadedCommentResponse(
            id=comment.id,
            anime_id=comment.anime_id,
            parent_id=comment.parent_id,
            content=comment.content,
            author_name=comment.author_name,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat(),
            is_deleted=comment.is_deleted,
            is_edited=comment.is_edited,
            upvotes=comment.upvotes,
            downvotes=comment.downvotes,
            score=comment.score,
            depth=comment.depth,
            reply_count=comment.reply_count,
            user_vote=None,
            replies=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error editing comment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to edit comment. Please try again later.",
        )


@app.delete("/api/comments/{comment_id}")
@limiter.limit("5/minute")
async def delete_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db),
):
    """
    Soft delete a comment (only own comments).
    Rate limited to 5 deletions per minute per IP.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = hash_ip(client_ip)

        # Find comment
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check ownership
        if comment.ip_hash != ip_hash:
            raise HTTPException(
                status_code=403, detail="Cannot delete other users' comments"
            )

        # Soft delete
        comment.is_deleted = 1
        comment.content = "[deleted]"
        comment.author_name = "[deleted]"

        db.commit()

        logger.info(f"[{request_id}] Deleted comment {comment_id}")

        return {"success": True, "message": "Comment deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error deleting comment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete comment. Please try again later.",
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
