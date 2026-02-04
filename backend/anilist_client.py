"""AniList API client for fetching anime data."""

import logging
from typing import Optional
import httpx
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ANILIST_API_URL = "https://graphql.anilist.co"

# GraphQL queries
SEARCH_ANIME_QUERY = """
query ($search: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: ANIME, sort: POPULARITY_DESC) {
      id
      title {
        romaji
        english
        native
      }
      coverImage {
        large
        medium
      }
      episodes
      seasonYear
      averageScore
      format
    }
  }
}
"""

GET_ANIME_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    coverImage {
      large
      medium
      extraLarge
    }
    episodes
    seasonYear
    averageScore
    format
    description
    genres
    tags {
      name
      rank
    }
    studios {
      nodes {
        name
      }
    }
  }
}
"""

GET_ANIME_REVIEWS_QUERY = """
query ($mediaId: Int, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    reviews(mediaId: $mediaId, sort: RATING_DESC) {
      id
      summary
      body
      rating
      score
      user {
        name
      }
      createdAt
    }
  }
}
"""


class AniListClient:
    """Client for interacting with AniList GraphQL API."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self._last_request_time = None
        self._min_delay = (
            0.7  # Minimum delay between requests (AniList allows ~90 req/min)
        )

    async def _make_request(self, query: str, variables: dict) -> dict:
        """Make a GraphQL request to AniList API with rate limiting."""
        # Rate limiting
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_delay:
                import asyncio

                await asyncio.sleep(self._min_delay - elapsed)

        try:
            response = await self.client.post(
                ANILIST_API_URL,
                json={"query": query, "variables": variables},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            self._last_request_time = datetime.now()

            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"AniList API errors: {data['errors']}")
                raise Exception(f"AniList API error: {data['errors'][0]['message']}")

            return data["data"]

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from AniList: {e}")
            raise Exception(
                f"Failed to fetch data from AniList: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Error making AniList request: {e}")
            raise

    async def search_anime(self, query: str, per_page: int = 10) -> list[dict]:
        """Search for anime by title.

        Args:
            query: Search query string
            per_page: Number of results to return (max 50)

        Returns:
            List of anime results with id, title, coverImage, etc.
        """
        if not query or len(query.strip()) < 2:
            return []

        variables = {"search": query.strip(), "page": 1, "perPage": min(per_page, 50)}

        try:
            data = await self._make_request(SEARCH_ANIME_QUERY, variables)
            media_list = data.get("Page", {}).get("media", [])

            # Format the results
            results = []
            for media in media_list:
                title = media.get("title", {})
                cover = media.get("coverImage", {})

                results.append(
                    {
                        "id": media.get("id"),
                        "title": {
                            "romaji": title.get("romaji"),
                            "english": title.get("english"),
                            "native": title.get("native"),
                        },
                        "coverImage": {
                            "large": cover.get("large"),
                            "medium": cover.get("medium"),
                        },
                        "episodes": media.get("episodes"),
                        "year": media.get("seasonYear"),
                        "score": media.get("averageScore"),
                        "format": media.get("format"),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching anime: {e}")
            return []

    async def get_anime_by_id(self, anime_id: int) -> Optional[dict]:
        """Get detailed anime information by ID.

        Args:
            anime_id: AniList anime ID

        Returns:
            Anime details or None if not found
        """
        variables = {"id": anime_id}

        try:
            data = await self._make_request(GET_ANIME_QUERY, variables)
            media = data.get("Media")

            if not media:
                return None

            title = media.get("title", {})
            cover = media.get("coverImage", {})
            studios = media.get("studios", {}).get("nodes", [])

            return {
                "id": media.get("id"),
                "title": {
                    "romaji": title.get("romaji"),
                    "english": title.get("english"),
                    "native": title.get("native"),
                },
                "coverImage": {
                    "large": cover.get("large"),
                    "medium": cover.get("medium"),
                    "extraLarge": cover.get("extraLarge"),
                },
                "episodes": media.get("episodes"),
                "year": media.get("seasonYear"),
                "score": media.get("averageScore"),
                "format": media.get("format"),
                "description": media.get("description"),
                "genres": media.get("genres", []),
                "studios": [s.get("name") for s in studios if s.get("name")],
            }

        except Exception as e:
            logger.error(f"Error fetching anime by ID: {e}")
            return None

    def get_display_title(self, anime: dict) -> str:
        """Get the best display title for an anime.

        Prefers English title, falls back to Romaji, then Native.
        """
        title = anime.get("title", {})
        return (
            title.get("english")
            or title.get("romaji")
            or title.get("native")
            or "Unknown"
        )

    async def get_anime_reviews(self, anime_id: int, per_page: int = 25) -> list[dict]:
        """Fetch reviews for a specific anime.

        Args:
            anime_id: AniList anime ID
            per_page: Number of reviews to fetch (max 25)

        Returns:
            List of review objects with summary, body, rating, etc.
        """
        variables = {"mediaId": anime_id, "page": 1, "perPage": min(per_page, 25)}

        try:
            data = await self._make_request(GET_ANIME_REVIEWS_QUERY, variables)
            reviews_list = data.get("Page", {}).get("reviews", [])

            # Format the results
            reviews = []
            for review in reviews_list:
                user = review.get("user", {})

                reviews.append(
                    {
                        "id": review.get("id"),
                        "summary": review.get("summary", ""),
                        "body": review.get("body", ""),
                        "rating": review.get("rating"),
                        "score": review.get("score"),
                        "user_name": user.get("name", "Anonymous"),
                        "created_at": review.get("createdAt"),
                    }
                )

            return reviews

        except Exception as e:
            logger.error(f"Error fetching anime reviews: {e}")
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global client instance
_anilist_client: Optional[AniListClient] = None


def get_anilist_client() -> AniListClient:
    """Get or create the global AniList client instance."""
    global _anilist_client
    if _anilist_client is None:
        _anilist_client = AniListClient()
    return _anilist_client


async def close_anilist_client():
    """Close the global AniList client."""
    global _anilist_client
    if _anilist_client:
        await _anilist_client.close()
        _anilist_client = None
