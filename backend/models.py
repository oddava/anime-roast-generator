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
