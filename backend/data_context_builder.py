"""Data context builder for creating comprehensive LLM prompts."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnimeDataContextBuilder:
    """Builds comprehensive context about an anime from AniList data."""

    @staticmethod
    def build_context(anime_data: dict, review_context: Optional[dict] = None) -> str:
        """Build a comprehensive context string for the LLM.

        This provides the LLM with factual data to base its roast on,
        preventing hallucinations.
        """
        sections = []

        # Basic Info Section
        sections.append(AnimeDataContextBuilder._build_basic_info(anime_data))

        # Stats Section
        sections.append(AnimeDataContextBuilder._build_stats_section(anime_data))

        # Staff/Creator Section
        sections.append(AnimeDataContextBuilder._build_staff_section(anime_data))

        # Characters Section
        sections.append(AnimeDataContextBuilder._build_characters_section(anime_data))

        # Relations Section
        sections.append(AnimeDataContextBuilder._build_relations_section(anime_data))

        # Genre/Tag Analysis
        sections.append(AnimeDataContextBuilder._build_genre_analysis(anime_data))

        # Review Context (if available)
        if review_context:
            sections.append(
                AnimeDataContextBuilder._build_review_section(review_context)
            )

        return "\n\n".join(sections)

    @staticmethod
    def _build_basic_info(anime_data: dict) -> str:
        """Build basic anime information section."""
        title = anime_data.get("title", {})
        display_title = title.get("english") or title.get("romaji") or "Unknown"

        info = ["=== ANIME BASIC INFO ==="]
        info.append(f"Title: {display_title}")
        info.append(f"Romaji: {title.get('romaji', 'N/A')}")
        info.append(f"Format: {anime_data.get('format', 'Unknown')}")
        info.append(f"Source: {anime_data.get('source', 'Unknown')}")
        info.append(f"Episodes: {anime_data.get('episodes', 'Unknown')}")
        info.append(f"Year: {anime_data.get('year', 'Unknown')}")
        info.append(f"Season: {anime_data.get('season', 'Unknown')}")
        info.append(f"Status: {anime_data.get('status', 'Unknown')}")

        # Studios
        studios = anime_data.get("studios", [])
        if studios:
            info.append(f"Studios: {', '.join(studios)}")

        # Description (cleaned)
        description = anime_data.get("description", "")
        if description:
            # Remove HTML tags
            import re

            clean_desc = re.sub(r"<[^>]+>", "", description)
            clean_desc = (
                clean_desc[:300] + "..." if len(clean_desc) > 300 else clean_desc
            )
            info.append(f"\nSynopsis: {clean_desc}")

        return "\n".join(info)

    @staticmethod
    def _build_stats_section(anime_data: dict) -> str:
        """Build statistics section."""
        stats = ["=== ANILIST STATISTICS ==="]

        score = anime_data.get("score")
        if score:
            stats.append(f"Average Score: {score}/100")

        mean_score = anime_data.get("meanScore")
        if mean_score:
            stats.append(f"Mean Score: {mean_score}/100")

        popularity = anime_data.get("popularity")
        if popularity:
            stats.append(f"Popularity Rank: #{popularity:,}")

        favourites = anime_data.get("favourites")
        if favourites:
            stats.append(f"Favorites: {favourites:,}")

        # Score distribution for understanding reception
        score_dist = anime_data.get("scoreDistribution", {})
        if score_dist:
            total_votes = sum(score_dist.values())
            if total_votes > 0:
                high_votes = (
                    score_dist.get(10, 0) + score_dist.get(9, 0) + score_dist.get(8, 0)
                )
                low_votes = (
                    score_dist.get(1, 0) + score_dist.get(2, 0) + score_dist.get(3, 0)
                )

                stats.append(f"\nScore Distribution (out of {total_votes:,} votes):")
                stats.append(
                    f"  High scores (8-10): {high_votes:,} ({high_votes / total_votes * 100:.1f}%)"
                )
                stats.append(
                    f"  Low scores (1-3): {low_votes:,} ({low_votes / total_votes * 100:.1f}%)"
                )

                controversy = anime_data.get("controversyScore", 0)
                if controversy > 30:
                    stats.append(f"  ⚠️ Controversial (polarizing opinions)")
                elif controversy < 10:
                    stats.append(f"  ✅ Generally agreed upon quality")

        # Rankings
        rankings = anime_data.get("rankings", [])
        if rankings:
            stats.append("\nTop Rankings:")
            for rank in rankings[:3]:
                stats.append(f"  #{rank['rank']} in {rank['context']}")

        return "\n".join(stats)

    @staticmethod
    def _build_staff_section(anime_data: dict) -> str:
        """Build staff information section."""
        staff = anime_data.get("staff", [])
        if not staff:
            return "=== STAFF INFO ===\nNo staff information available."

        staff_info = ["=== KEY STAFF ==="]

        # Look for key roles
        key_roles = [
            "Director",
            "Original Creator",
            "Storyboard",
            "Series Composition",
            "Music",
        ]
        found_roles = []

        for member in staff:
            role = member.get("role", "")
            name = member.get("name", "Unknown")

            for key_role in key_roles:
                if key_role.lower() in role.lower():
                    found_roles.append(f"  {role}: {name}")
                    break

        if found_roles:
            staff_info.extend(found_roles[:6])  # Limit to first 6 key staff
        else:
            # Just list first 4 staff members
            for member in staff[:4]:
                staff_info.append(
                    f"  {member.get('role', 'Unknown')}: {member.get('name', 'Unknown')}"
                )

        return "\n".join(staff_info)

    @staticmethod
    def _build_characters_section(anime_data: dict) -> str:
        """Build characters information section."""
        characters = anime_data.get("mainCharacters", [])
        if not characters:
            return "=== MAIN CHARACTERS ===\nNo character information available."

        char_info = ["=== MAIN CHARACTERS ==="]

        main_chars = [c for c in characters if c.get("role") == "MAIN"]
        supporting = [c for c in characters if c.get("role") != "MAIN"]

        if main_chars:
            char_info.append(
                f"Protagonists: {', '.join(c['name'] for c in main_chars[:4])}"
            )

        if supporting:
            char_info.append(
                f"Key Supporting: {', '.join(c['name'] for c in supporting[:3])}"
            )

        return "\n".join(char_info)

    @staticmethod
    def _build_relations_section(anime_data: dict) -> str:
        """Build relations section (sequels, prequels, etc.)."""
        relations = anime_data.get("relations", [])
        if not relations:
            return "=== FRANCHISE INFO ===\nStandalone series."

        rel_info = ["=== FRANCHISE INFO ==="]

        # Group by relation type
        by_type = {}
        for rel in relations:
            rel_type = rel.get("relation", "RELATED")
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel.get("title", "Unknown"))

        for rel_type, titles in by_type.items():
            rel_info.append(f"{rel_type}: {', '.join(titles[:3])}")

        return "\n".join(rel_info)

    @staticmethod
    def _build_genre_analysis(anime_data: dict) -> str:
        """Build genre and tag analysis."""
        genres = anime_data.get("genres", [])

        analysis = ["=== GENRE & THEMES ==="]

        if genres:
            analysis.append(f"Genres: {', '.join(genres)}")

        # Source material implications
        source = anime_data.get("source", "Unknown")
        source_hints = {
            "MANGA": "Adapted from manga - may have source material comparisons",
            "LIGHT_NOVEL": "Light novel adaptation - often has source readers critiquing cuts",
            "VISUAL_NOVEL": "Visual novel adaptation - may have multiple routes condensed",
            "ORIGINAL": "Original anime - no source material to compare",
            "NOVEL": "Novel adaptation",
            "GAME": "Game adaptation",
            "WEB_NOVEL": "Web novel adaptation - often has pacing issues",
        }

        if source in source_hints:
            analysis.append(f"\nSource Context ({source}): {source_hints[source]}")

        # Format implications
        format_type = anime_data.get("format", "")
        format_hints = {
            "TV": "TV series format",
            "TV_SHORT": "Short-form TV episodes",
            "MOVIE": "Movie format - higher budget expected",
            "OVA": "OVA format - often for fans",
            "ONA": "Web series format",
            "SPECIAL": "Special episode",
        }

        if format_type in format_hints:
            analysis.append(
                f"Format Context ({format_type}): {format_hints[format_type]}"
            )

        return "\n".join(analysis)

    @staticmethod
    def _build_review_section(review_context: dict) -> str:
        """Build review analysis section."""
        section = ["=== COMMUNITY REVIEW ANALYSIS ==="]

        # Sentiment breakdown
        sentiment = review_context.get("sentiment_breakdown", {})
        if sentiment:
            section.append(
                f"Sentiment from {sentiment.get('total', 0)} analyzed reviews:"
            )
            section.append(f"  Positive: {sentiment.get('positive_pct', 0):.0f}%")
            section.append(f"  Negative: {sentiment.get('negative_pct', 0):.0f}%")

        # AniList score comparison
        anilist_score = review_context.get("anilist_score")
        if anilist_score:
            section.append(f"\nActual AniList Score: {anilist_score:.1f}/10")

        # Controversy
        if review_context.get("is_controversial"):
            section.append(f"⚠️ This anime is CONTROVERSIAL (polarizing opinions)")

        # Verified complaints
        complaints = review_context.get("verified_complaints", [])
        if complaints:
            section.append(
                "\nVERIFIED COMMUNITY COMPLAINTS (backed by multiple reviews):"
            )
            for i, c in enumerate(complaints[:4], 1):
                section.append(
                    f"  {i}. {c['category'].upper()}: {c['review_count']} reviews mentioned this"
                )
                if c.get("examples"):
                    example = c["examples"][0]
                    if len(example) > 100:
                        example = example[:100] + "..."
                    section.append(f'     "{example}"')
        else:
            section.append("\nNo consistent complaints found across reviews.")

        # Community memes
        memes = review_context.get("community_memes", [])
        if memes:
            section.append(
                f"\nCommunity Memes/Phrases: {', '.join(m[0] for m in memes[:5])}"
            )

        return "\n".join(section)

    @staticmethod
    def build_constraints_section() -> str:
        """Build the constraints section that prevents hallucinations."""
        return """=== STRICT ROASTING RULES ===
1. ONLY use criticisms mentioned in the "VERIFIED COMMUNITY COMPLAINTS" section above
2. DO NOT make up fake ratings - use ONLY the "Actual AniList Score" provided
3. DO NOT claim the anime "fell off" or "peaked" unless mentioned in reviews
4. DO NOT make generic statements about pacing, characters, or plot unless verified
5. If NO verified complaints exist, roast based on genre tropes and format expectations
6. NEVER state something as fact unless it's in the data above
7. Keep criticisms playful but GROUNDED IN REALITY
8. Reference specific data points (score, rankings, source material) for credibility"""


# Legacy compatibility - wrapper functions for existing code
def format_reviews_for_gemini(reviews: list[dict], max_reviews: int = 10) -> str:
    """Legacy function for backward compatibility."""
    if not reviews:
        return "No community reviews available."

    # Take top reviews (by score/rating)
    sorted_reviews = sorted(
        reviews,
        key=lambda x: (x.get("score", 0) or 0, x.get("rating", 0) or 0),
        reverse=True,
    )[:max_reviews]

    formatted = []
    for i, review in enumerate(sorted_reviews, 1):
        summary = review.get("summary", "").strip()
        body = review.get("body", "").strip()
        rating = review.get("rating")

        # Use summary if available, otherwise truncate body
        text = summary if summary else (body[:200] + "..." if len(body) > 200 else body)

        if rating:
            formatted.append(f"{i}. [Rating: {rating}/10] {text}")
        else:
            formatted.append(f"{i}. {text}")

    return "\n".join(formatted)
