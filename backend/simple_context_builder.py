"""Simplified context builder for creating natural LLM prompts without statistics."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SimpleContextBuilder:
    """Builds simplified, qualitative context for natural roasts."""

    MIN_REVIEWS_FOR_DATA = 10  # Minimum reviews before using review data

    @staticmethod
    def build_context(anime_data: dict, review_context: Optional[dict] = None) -> str:
        """Build simplified context without statistics.

        Focuses on qualitative insights rather than quantitative data.
        """
        sections = []

        # Basic Info
        sections.append(SimpleContextBuilder._build_basic_info(anime_data))

        # Reception (qualitative only)
        sections.append(SimpleContextBuilder._build_reception(anime_data))

        # Review themes (if sufficient data)
        if (
            review_context
            and review_context.get("review_count", 0)
            >= SimpleContextBuilder.MIN_REVIEWS_FOR_DATA
        ):
            sections.append(SimpleContextBuilder._build_review_themes(review_context))

        # Source/franchise context
        sections.append(SimpleContextBuilder._build_source_context(anime_data))

        return "\n\n".join(sections)

    @staticmethod
    def _build_basic_info(anime_data: dict) -> str:
        """Build basic anime info."""
        title = anime_data.get("title", {})
        display_title = title.get("english") or title.get("romaji") or "Unknown"

        info = [f"Anime: {display_title}"]

        if anime_data.get("year"):
            info.append(f"Year: {anime_data['year']}")

        if anime_data.get("episodes"):
            info.append(f"Episodes: {anime_data['episodes']}")

        if anime_data.get("format"):
            info.append(f"Format: {anime_data['format']}")

        studios = anime_data.get("studios", [])
        if studios:
            info.append(f"Studio: {', '.join(studios[:2])}")

        return "\n".join(info)

    @staticmethod
    def _build_reception(anime_data: dict) -> str:
        """Build qualitative reception description."""
        score = anime_data.get("score")

        if not score:
            return "Reception: Unknown"

        score_10 = score / 10

        # Categorize without exact numbers
        if score_10 >= 8.0:
            reception = "Highly rated by the community"
        elif score_10 >= 7.0:
            reception = "Generally well-received"
        elif score_10 >= 6.0:
            reception = "Mixed reception with both fans and critics"
        elif score_10 >= 5.0:
            reception = "Below average reception"
        else:
            reception = "Poorly received by the community"

        # Check controversy
        controversy = anime_data.get("controversyScore", 0)
        if controversy > 30:
            reception += " - polarizing opinions"

        return f"Reception: {reception}"

    @staticmethod
    def _build_review_themes(review_context: dict) -> str:
        """Build review themes section with actual quotes."""
        sections = ["=== COMMON THEMES IN REVIEWS ==="]

        complaints = review_context.get("verified_complaints", [])

        if not complaints:
            return ""

        for complaint in complaints[:4]:  # Top 4 themes
            category = complaint["category"]
            examples = complaint.get("examples", [])

            if examples:
                # Pick the most vivid example (short but punchy)
                best_quote = min(examples, key=lambda x: abs(len(x) - 80))
                sections.append(f"\n{category.replace('_', ' ').title()}:")
                sections.append(f'  "{best_quote}"')

        return "\n".join(sections)

    @staticmethod
    def _build_source_context(anime_data: dict) -> str:
        """Build source material and franchise context."""
        sections = []

        source = anime_data.get("source", "")
        if source == "MANGA":
            sections.append("Source: Manga adaptation")
        elif source == "LIGHT_NOVEL":
            sections.append("Source: Light novel adaptation")
        elif source == "VISUAL_NOVEL":
            sections.append("Source: Visual novel adaptation")
        elif source == "WEB_NOVEL":
            sections.append("Source: Web novel adaptation")
        elif source == "ORIGINAL":
            sections.append("Source: Original anime (no source material)")

        # Franchise context for sequels
        relations = anime_data.get("relations", [])
        if relations:
            prequels = [
                r for r in relations if r.get("relation") in ["PREQUEL", "PARENT"]
            ]
            if prequels:
                sections.append(f"Note: This is a sequel in a franchise")

                # Get previous season scores for comparison
                current_score = anime_data.get("score", 0)
                prequel_scores = []

                for prequel in prequels[:2]:  # Check up to 2 prequels
                    # Note: In a real implementation, you'd fetch actual prequel data
                    # For now, we'll just note it's a sequel
                    pass

                if current_score and current_score < 70:  # Score below 7/10
                    sections.append("Reception: Lower than previous seasons")

        return "\n".join(sections) if sections else ""

    @staticmethod
    def build_constraints() -> str:
        """Build constraints that prevent robotic/statistical roasts."""
        return """=== ROASTING GUIDELINES ===
1. Write naturally like a sarcastic friend, NOT like a data analyst
2. DO NOT mention specific percentages, review counts, or statistics
3. DO NOT quote exact scores (e.g., "it has a 5.1/10")
4. DO NOT say things like "X% of reviews" or "out of Y reviews"
5. Use the data as BACKGROUND CONTEXT to inform your jokes
6. Focus on patterns and themes, not numbers
7. The roast should feel organic and conversational
8. Mock tropes and expectations, not data points

FORBIDDEN PHRASES:
- Any percentage (e.g., "50%", "100%")
- Review counts (e.g., "4 reviews", "out of 10 reviews")
- Exact ratings (e.g., "5.1/10", "scored 51/100")
- Statistical language (e.g., "according to the data", "statistics show")

INSTEAD, speak naturally:
- "people are saying..."
- "fans noticed..."
- "the community agrees..."
- "it's become a running joke that..."""
