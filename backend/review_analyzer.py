"""Review analyzer for extracting insights from AniList reviews."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class ReviewAnalyzer:
    """Analyzes anime reviews to extract criticisms and sentiment."""

    # Keywords for identifying common complaints
    CRITICISM_KEYWORDS = {
        "pacing": ["pacing", "slow", "rushed", "dragging", "filler", "boring", "pace"],
        "plot": [
            "plot holes",
            "inconsistent",
            "makes no sense",
            "confusing",
            "predictable",
            "cliche",
            "trope",
        ],
        "characters": [
            "character development",
            "shallow",
            "one-dimensional",
            "annoying",
            "unlikable",
            "bland",
            "mary sue",
            "gary stu",
        ],
        "animation": [
            "animation",
            "art",
            "budget",
            "quality drop",
            "off-model",
            "still frames",
        ],
        "ending": ["ending", "rushed ending", "disappointing ending", "finale"],
        "power_scaling": [
            "power creep",
            "asspull",
            "plot armor",
            "convenient",
            "deus ex machina",
        ],
    }

    # Toxic phrases and community memes to look for
    TOXIC_PHRASES = [
        "mid",
        "cope",
        "copium",
        "carried by",
        "fell off",
        "peaked at",
        "read the manga",
        "friendship power",
        "talk no jutsu",
        "truck-kun",
        "nothing happens",
        "down bad",
        "least horny",
        "entry-level",
        "normie",
        "filtered",
        "toxic fanbase",
        "defend anything",
        "wasted potential",
        "overrated",
        "overhyped",
    ]

    @staticmethod
    def extract_spicy_quotes(reviews: list[dict], max_quotes: int = 2) -> list[str]:
        """Extract the most memorable/negative quotes from reviews.

        Args:
            reviews: List of review dictionaries with 'body' and 'summary'
            max_quotes: Maximum number of quotes to return

        Returns:
            List of spicy review excerpts
        """
        spicy_quotes = []

        for review in reviews:
            text = review.get("body", "") or review.get("summary", "")
            if not text:
                continue

            # Look for sentences with toxic phrases or strong negative sentiment
            sentences = re.split(r"[.!?]+", text)

            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20 or len(sentence) > 150:
                    continue

                # Check for toxic phrases
                lower_sentence = sentence.lower()
                score = 0

                for phrase in ReviewAnalyzer.TOXIC_PHRASES:
                    if phrase in lower_sentence:
                        score += 2

                # Check for strong negative words
                negative_words = [
                    "terrible",
                    "awful",
                    "garbage",
                    "trash",
                    "worst",
                    "disappointing",
                    "waste",
                    "regret",
                ]
                for word in negative_words:
                    if word in lower_sentence:
                        score += 1

                # Check for humor/sarcasm indicators
                humor_indicators = ["lmao", "lol", "💀", "bruh", "literally", "somehow"]
                for indicator in humor_indicators:
                    if indicator in lower_sentence:
                        score += 1

                if score >= 2:
                    spicy_quotes.append((sentence, score))

        # Sort by score and return top quotes
        spicy_quotes.sort(key=lambda x: x[1], reverse=True)
        return [quote[0] for quote in spicy_quotes[:max_quotes]]

    @staticmethod
    def identify_common_criticisms(reviews: list[dict]) -> list[str]:
        """Identify the most common criticisms across reviews.

        Args:
            reviews: List of review dictionaries

        Returns:
            List of top criticisms (max 5)
        """
        criticism_counts = {}

        for review in reviews:
            text = review.get("body", "") or review.get("summary", "")
            if not text:
                continue

            lower_text = text.lower()

            for category, keywords in ReviewAnalyzer.CRITICISM_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in lower_text:
                        criticism_counts[category] = (
                            criticism_counts.get(category, 0) + 1
                        )
                        break  # Only count once per category per review

        # Sort by frequency and return top 5
        sorted_criticisms = sorted(
            criticism_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [c[0] for c in sorted_criticisms[:5]]

    @staticmethod
    def calculate_average_rating(reviews: list[dict]) -> Optional[float]:
        """Calculate average user rating from reviews.

        Args:
            reviews: List of review dictionaries with 'rating' field

        Returns:
            Average rating or None if no ratings
        """
        ratings = [r.get("rating") for r in reviews if r.get("rating")]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)

    @staticmethod
    def create_review_summary(reviews: list[dict]) -> dict:
        """Create a comprehensive summary of reviews.

        Args:
            reviews: List of review dictionaries

        Returns:
            Dictionary with analysis results
        """
        if not reviews:
            return {
                "review_count": 0,
                "average_rating": None,
                "top_criticisms": [],
                "spicy_quotes": [],
                "summary": "No reviews available",
            }

        review_count = len(reviews)
        avg_rating = ReviewAnalyzer.calculate_average_rating(reviews)
        criticisms = ReviewAnalyzer.identify_common_criticisms(reviews)
        quotes = ReviewAnalyzer.extract_spicy_quotes(reviews)

        # Create a brief summary
        summary_parts = []
        if avg_rating:
            summary_parts.append(f"Average rating: {avg_rating:.1f}/10")
        if criticisms:
            summary_parts.append(f"Main complaints: {', '.join(criticisms[:3])}")
        if quotes:
            summary_parts.append(f"Community sentiment: mixed to negative")

        summary = (
            " | ".join(summary_parts) if summary_parts else "Community reviews analyzed"
        )

        return {
            "review_count": review_count,
            "average_rating": avg_rating,
            "top_criticisms": criticisms,
            "spicy_quotes": quotes,
            "summary": summary,
        }

    @staticmethod
    def format_reviews_for_gemini(reviews: list[dict], max_reviews: int = 10) -> str:
        """Format reviews into a concise string for Gemini API.

        Args:
            reviews: List of review dictionaries
            max_reviews: Maximum reviews to include

        Returns:
            Formatted review text
        """
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
            text = (
                summary
                if summary
                else (body[:200] + "..." if len(body) > 200 else body)
            )

            if rating:
                formatted.append(f"{i}. [Rating: {rating}/10] {text}")
            else:
                formatted.append(f"{i}. {text}")

        return "\n".join(formatted)
