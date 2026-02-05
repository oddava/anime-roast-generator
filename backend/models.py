from typing import Optional
from pydantic import BaseModel, Field, validator


class AnimeTitle(BaseModel):
    """Anime title in different languages."""

    romaji: Optional[str] = None
    english: Optional[str] = None
    native: Optional[str] = None


class AnimeCoverImage(BaseModel):
    """Anime cover image URLs."""

    large: Optional[str] = None
    medium: Optional[str] = None
    extraLarge: Optional[str] = None


class AnimeSearchResult(BaseModel):
    """Model for anime search results from AniList."""

    id: int
    title: AnimeTitle
    coverImage: AnimeCoverImage
    episodes: Optional[int] = None
    year: Optional[int] = None
    score: Optional[int] = None
    format: Optional[str] = None


class AnimeDetails(AnimeSearchResult):
    """Extended anime details including description and genres."""

    description: Optional[str] = None
    genres: list[str] = []
    studios: list[str] = []


class RoastRequest(BaseModel):
    """Request model for generating a roast."""

    anime_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the anime to roast",
        example="Naruto",
    )
    anime_id: Optional[int] = Field(
        None, description="Optional AniList anime ID for fetching cover image"
    )

    @validator("anime_name")
    def validate_anime_name(cls, v):
        """Basic validation at model level."""
        if not v or not v.strip():
            raise ValueError("Anime name cannot be empty")
        return v.strip()


class AnimeStats(BaseModel):
    """Model for humorous anime statistics."""

    horniness_level: int = Field(
        ..., ge=0, le=100, description="Fan service/ecchi content level"
    )
    plot_armor_thickness: int = Field(
        ..., ge=0, le=100, description="Protagonist invincibility level"
    )
    filler_hell: int = Field(
        ..., ge=0, le=100, description="Percentage of filler episodes"
    )
    power_creep: int = Field(..., ge=0, le=100, description="Power scaling absurdity")
    cringe_factor: int = Field(
        ..., ge=0, le=100, description="Awkward moments and tropes"
    )
    fan_toxicity: int = Field(..., ge=0, le=100, description="Fanbase intensity level")


class RoastResponse(BaseModel):
    """Response model for generated roast."""

    anime_name: str = Field(..., description="The anime that was roasted")
    roast: str = Field(..., description="The generated roast text")
    stats: AnimeStats = Field(..., description="Humorous anime statistics")
    cover_image: Optional[str] = Field(None, description="URL to anime cover image")
    anime_id: Optional[int] = Field(None, description="AniList anime ID")
    anime_details: Optional[AnimeDetails] = Field(
        None, description="Full anime details from AniList"
    )
    success: bool = Field(default=True, description="Whether the request succeeded")
    message: str = Field(default="", description="Additional message if any")


class AnimeReview(BaseModel):
    """Model for AniList anime reviews."""

    id: int
    summary: str
    body: Optional[str] = None
    rating: Optional[int] = None
    score: Optional[int] = None
    user_name: str
    created_at: Optional[int] = None


class ReviewAnalysis(BaseModel):
    """Analysis results from community reviews."""

    review_count: int = Field(..., description="Number of reviews analyzed")
    average_rating: Optional[float] = Field(
        None, description="Average user rating from reviews"
    )
    top_criticisms: list[str] = Field(
        default=[], description="Most common complaints from reviews"
    )
    spicy_quotes: list[str] = Field(
        default=[], description="Memorable/negative quotes from reviews"
    )
    summary: str = Field(..., description="Brief summary of community sentiment")


class EnhancedRoastResponse(RoastResponse):
    """Extended response model including review analysis."""

    review_analysis: Optional[ReviewAnalysis] = Field(
        None, description="Analysis of community reviews"
    )
    reviews_used: int = Field(
        default=0, description="Number of reviews used for analysis"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")
    error_code: str = Field(
        default="GENERAL_ERROR", description="Error code for frontend handling"
    )


class CommentCreate(BaseModel):
    """Request model for creating a comment."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Comment content",
        example="This anime is actually pretty good!",
    )
    author_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Optional custom author name (auto-generated if not provided)",
    )

    @validator("content")
    def validate_content(cls, v):
        """Sanitize and validate comment content."""
        if not v or not v.strip():
            raise ValueError("Comment cannot be empty")
        # Basic XSS prevention - remove script tags
        v = v.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
        return v.strip()


class CommentResponse(BaseModel):
    """Response model for a comment."""

    id: int = Field(..., description="Comment ID")
    anime_id: int = Field(..., description="Anime ID this comment belongs to")
    content: str = Field(..., description="Comment content")
    author_name: str = Field(..., description="Name of the comment author")
    created_at: str = Field(..., description="ISO format timestamp")

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Response model for listing comments."""

    comments: list[CommentResponse] = Field(..., description="List of comments")
    total: int = Field(..., description="Total number of comments")
    anime_id: int = Field(..., description="Anime ID")


class ThreadedCommentResponse(BaseModel):
    """Response model for threaded comments."""

    id: int
    anime_id: int
    parent_id: Optional[int]
    content: str
    author_name: str
    created_at: str
    updated_at: str
    is_deleted: int
    is_edited: int
    upvotes: int
    downvotes: int
    score: int
    depth: int
    reply_count: int
    user_vote: Optional[int] = None  # Current user's vote: 1, -1, or None
    replies: list["ThreadedCommentResponse"] = []

    class Config:
        from_attributes = True


class ThreadedCommentListResponse(BaseModel):
    """Response model for listing threaded comments."""

    comments: list[ThreadedCommentResponse]
    total: int
    anime_id: int
    has_more: bool


class CommentReplyRequest(BaseModel):
    """Request model for replying to a comment."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Reply content",
    )
    author_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Author name (from localStorage)",
    )

    @validator("content")
    def validate_content(cls, v):
        """Sanitize and validate reply content."""
        if not v or not v.strip():
            raise ValueError("Reply cannot be empty")
        v = v.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
        return v.strip()


class CommentVoteRequest(BaseModel):
    """Request model for voting on a comment."""

    vote_type: int = Field(
        ...,
        ge=-1,
        le=1,
        description="Vote type: 1 for upvote, -1 for downvote, 0 to remove vote",
    )


class CommentVoteResponse(BaseModel):
    """Response model for vote action."""

    comment_id: int
    upvotes: int
    downvotes: int
    score: int
    user_vote: int


class CommentEditRequest(BaseModel):
    """Request model for editing a comment."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="New comment content",
    )

    @validator("content")
    def validate_content(cls, v):
        """Sanitize and validate edited content."""
        if not v or not v.strip():
            raise ValueError("Comment cannot be empty")
        v = v.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
        return v.strip()


class CommentEditResponse(BaseModel):
    """Response model for edit action."""

    id: int
    content: str
    is_edited: int
    updated_at: str
