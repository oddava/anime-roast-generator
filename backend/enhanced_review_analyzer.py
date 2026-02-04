"""Enhanced review analyzer for extracting verified criticisms and sentiment."""

import logging
import re
from typing import Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ExtractedComplaint:
    """A verified complaint extracted from reviews."""

    category: str
    text: str
    sentiment: str  # 'negative', 'mixed', 'positive'
    confidence: float  # 0-1
    review_count: int
    example_quotes: list[str]


class EnhancedReviewAnalyzer:
    """Analyzes anime reviews to extract verified criticisms with context."""

    # Comprehensive criticism categories with keywords
    CRITICISM_PATTERNS = {
        "pacing": {
            "keywords": [
                "pacing",
                "slow",
                "rushed",
                "dragging",
                "filler",
                "boring",
                "pace",
                "too long",
                "bloated",
            ],
            "positive_indicators": [
                "perfect pacing",
                "well-paced",
                "never drags",
                "great pacing",
            ],
            "negative_indicators": [
                "too slow",
                "drags",
                "rushed",
                "boring",
                "filler hell",
                "padding",
            ],
        },
        "plot": {
            "keywords": [
                "plot holes",
                "inconsistent",
                "makes no sense",
                "confusing",
                "predictable",
                "cliche",
                "trope",
                "formulaic",
                "asspull",
            ],
            "positive_indicators": [
                "great story",
                "masterpiece",
                "well written",
                "engaging plot",
            ],
            "negative_indicators": [
                "plot holes",
                "makes no sense",
                "asspull",
                "convenient",
                "lazy writing",
            ],
        },
        "characters": {
            "keywords": [
                "character development",
                "shallow",
                "one-dimensional",
                "annoying",
                "unlikable",
                "bland",
                "mary sue",
                "gary stu",
                "generic protagonist",
            ],
            "positive_indicators": [
                "great characters",
                "character development",
                "complex",
                "relatable",
                "memorable",
            ],
            "negative_indicators": [
                "shallow",
                "annoying",
                "bland",
                "no development",
                "generic",
            ],
        },
        "animation": {
            "keywords": [
                "animation",
                "art",
                "budget",
                "quality drop",
                "off-model",
                "still frames",
                "cgi",
                "sakuga",
            ],
            "positive_indicators": [
                "beautiful animation",
                "stunning",
                "sakuga",
                "great art",
            ],
            "negative_indicators": [
                " QUALITY",
                "budget cuts",
                "off-model",
                "still frames",
                "bad cgi",
            ],
        },
        "ending": {
            "keywords": [
                "ending",
                "finale",
                "conclusion",
                "rushed ending",
                "disappointing ending",
                "last episode",
            ],
            "positive_indicators": [
                "satisfying ending",
                "perfect conclusion",
                "great finale",
            ],
            "negative_indicators": [
                "rushed ending",
                "disappointing",
                "bad ending",
                "fell apart",
            ],
        },
        "power_scaling": {
            "keywords": [
                "power creep",
                "asspull",
                "plot armor",
                "convenient",
                "deus ex machina",
                "power scaling",
            ],
            "positive_indicators": [
                "well explained",
                "consistent powers",
                "logical progression",
            ],
            "negative_indicators": [
                "power creep",
                "plot armor",
                "asspull",
                "inconsistent",
            ],
        },
        "adaptation": {
            "keywords": [
                "adaptation",
                "read the manga",
                "skipped",
                "cut content",
                "rushed adaptation",
                "anime original",
            ],
            "positive_indicators": ["great adaptation", "faithful", "improved"],
            "negative_indicators": [
                "butchered",
                "rushed adaptation",
                "skipped arcs",
                "read the manga",
            ],
        },
        "fan_service": {
            "keywords": [
                "fan service",
                "ecchi",
                "harem",
                "unnecessary scenes",
                "sexualization",
            ],
            "positive_indicators": ["tasteful", "subtle", "rare"],
            "negative_indicators": [
                "too much fan service",
                "unnecessary",
                "creepy",
                "uncomfortable",
            ],
        },
    }

    # Phrases indicating genuine sentiment vs memes
    GENUINE_SENTIMENT_MARKERS = [
        "personally",
        "for me",
        "i felt",
        "i think",
        "in my opinion",
        "the reason",
        "because",
        "the problem is",
        "while",
        "although",
    ]

    MEME_PHRASES = [
        "mid",
        "cope",
        "copium",
        "touch grass",
        "ratio",
        "rent free",
        "based",
        "cringe",
        "kino",
        "sneed",
        "chud",
        "literally me",
    ]

    @staticmethod
    def analyze_sentiment_with_context(text: str, category: str) -> tuple[str, float]:
        """Analyze sentiment with confidence score for a specific criticism category.

        Returns:
            Tuple of (sentiment, confidence) where sentiment is 'positive', 'negative', or 'mixed'
        """
        if not text:
            return "neutral", 0.0

        patterns = EnhancedReviewAnalyzer.CRITICISM_PATTERNS.get(category, {})
        pos_indicators = patterns.get("positive_indicators", [])
        neg_indicators = patterns.get("negative_indicators", [])

        text_lower = text.lower()

        # Count positive and negative indicators
        pos_count = sum(1 for ind in pos_indicators if ind in text_lower)
        neg_count = sum(1 for ind in neg_indicators if ind in text_lower)

        # Look for negation words that flip sentiment
        negation_words = [
            "not",
            "no",
            "never",
            "doesn't",
            "isn't",
            "wasn't",
            "hardly",
            "barely",
        ]
        negation_count = sum(1 for word in negation_words if word in text_lower)

        # Calculate confidence based on indicator strength
        total_mentions = pos_count + neg_count
        if total_mentions == 0:
            return "neutral", 0.0

        # Determine sentiment
        if neg_count > pos_count:
            sentiment = "negative"
            confidence = min(0.5 + (neg_count / total_mentions) * 0.5, 1.0)
        elif pos_count > neg_count:
            sentiment = "positive"
            confidence = min(0.5 + (pos_count / total_mentions) * 0.5, 1.0)
        else:
            sentiment = "mixed"
            confidence = 0.5

        # Boost confidence for genuine sentiment markers
        genuine_markers = sum(
            1
            for marker in EnhancedReviewAnalyzer.GENUINE_SENTIMENT_MARKERS
            if marker in text_lower
        )
        if genuine_markers > 0:
            confidence = min(confidence + 0.1, 1.0)

        return sentiment, confidence

    @staticmethod
    def extract_specific_complaint(text: str, category: str) -> Optional[str]:
        """Extract the specific complaint text with context from a review.

        Returns the sentence containing the criticism, or None if not found.
        """
        if not text:
            return None

        patterns = EnhancedReviewAnalyzer.CRITICISM_PATTERNS.get(category, {})
        keywords = patterns.get("keywords", [])

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15 or len(sentence) > 200:
                continue

            sentence_lower = sentence.lower()

            # Check if sentence contains keywords
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Extract surrounding context (3 words before and after)
                    words = sentence_lower.split()
                    for i, word in enumerate(words):
                        if keyword in word:
                            start = max(0, i - 3)
                            end = min(len(words), i + 4)
                            return sentence

        return None

    @staticmethod
    def identify_verified_criticisms(
        reviews: list[dict], min_confidence: float = 0.6
    ) -> list[ExtractedComplaint]:
        """Identify criticisms that appear multiple times with high confidence.

        Args:
            reviews: List of review dictionaries
            min_confidence: Minimum confidence threshold (0-1)

        Returns:
            List of verified complaints
        """
        category_data = defaultdict(
            lambda: {"sentiment_scores": [], "examples": [], "count": 0}
        )

        for review in reviews:
            text = review.get("body", "") or review.get("summary", "")
            if not text:
                continue

            # Check each category
            for category in EnhancedReviewAnalyzer.CRITICISM_PATTERNS:
                complaint_text = EnhancedReviewAnalyzer.extract_specific_complaint(
                    text, category
                )

                if complaint_text:
                    sentiment, confidence = (
                        EnhancedReviewAnalyzer.analyze_sentiment_with_context(
                            complaint_text, category
                        )
                    )

                    # Only count negative/mixed sentiments
                    if (
                        sentiment in ["negative", "mixed"]
                        and confidence >= min_confidence
                    ):
                        category_data[category]["sentiment_scores"].append(confidence)
                        category_data[category]["count"] += 1

                        # Store unique examples
                        if len(category_data[category]["examples"]) < 3:
                            # Clean up the example text
                            clean_example = complaint_text.strip().replace("\n", " ")
                            if clean_example not in category_data[category]["examples"]:
                                category_data[category]["examples"].append(
                                    clean_example
                                )

        # Build verified complaints list
        verified_complaints = []
        for category, data in category_data.items():
            if data["count"] >= 2:  # Must appear in at least 2 reviews
                avg_confidence = sum(data["sentiment_scores"]) / len(
                    data["sentiment_scores"]
                )

                complaint = ExtractedComplaint(
                    category=category,
                    text=f"Multiple reviewers mentioned issues with {category}",
                    sentiment="negative",
                    confidence=avg_confidence,
                    review_count=data["count"],
                    example_quotes=data["examples"],
                )
                verified_complaints.append(complaint)

        # Sort by confidence and review count
        verified_complaints.sort(
            key=lambda x: (x.confidence * x.review_count), reverse=True
        )
        return verified_complaints[:5]  # Return top 5

    @staticmethod
    def extract_community_memes(reviews: list[dict]) -> list[tuple[str, int]]:
        """Extract popular meme phrases and their frequency.

        Returns:
            List of (phrase, count) tuples
        """
        meme_counts = defaultdict(int)

        for review in reviews:
            text = (review.get("body", "") or review.get("summary", "")).lower()

            for meme in EnhancedReviewAnalyzer.MEME_PHRASES:
                if meme in text:
                    meme_counts[meme] += 1

        # Return memes that appear at least twice
        return [(phrase, count) for phrase, count in meme_counts.items() if count >= 2]

    @staticmethod
    def calculate_sentiment_breakdown(reviews: list[dict]) -> dict:
        """Calculate detailed sentiment breakdown.

        Returns:
            Dictionary with sentiment statistics
        """
        sentiments = []

        for review in reviews:
            text = review.get("body", "") or review.get("summary", "")
            rating = review.get("rating")

            if rating:
                # Use rating as sentiment indicator
                if rating >= 8:
                    sentiments.append("very_positive")
                elif rating >= 6:
                    sentiments.append("positive")
                elif rating >= 4:
                    sentiments.append("mixed")
                elif rating >= 2:
                    sentiments.append("negative")
                else:
                    sentiments.append("very_negative")
            else:
                # Analyze text sentiment
                text_lower = text.lower()
                negative_words = [
                    "bad",
                    "terrible",
                    "awful",
                    "worst",
                    "disappointing",
                    "waste",
                    "regret",
                ]
                positive_words = [
                    "great",
                    "amazing",
                    "best",
                    "masterpiece",
                    "excellent",
                    "love",
                ]

                neg_count = sum(1 for w in negative_words if w in text_lower)
                pos_count = sum(1 for w in positive_words if w in text_lower)

                if pos_count > neg_count:
                    sentiments.append("positive")
                elif neg_count > pos_count:
                    sentiments.append("negative")
                else:
                    sentiments.append("neutral")

        total = len(sentiments)
        if total == 0:
            return {"positive": 0, "mixed": 0, "negative": 0}

        return {
            "positive": sentiments.count("positive")
            + sentiments.count("very_positive"),
            "mixed": sentiments.count("mixed") + sentiments.count("neutral"),
            "negative": sentiments.count("negative")
            + sentiments.count("very_negative"),
            "total": total,
            "positive_pct": (
                sentiments.count("positive") + sentiments.count("very_positive")
            )
            / total
            * 100,
            "negative_pct": (
                sentiments.count("negative") + sentiments.count("very_negative")
            )
            / total
            * 100,
        }

    @staticmethod
    def format_enhanced_review_context(reviews: list[dict], anime_data: dict) -> dict:
        """Create comprehensive review context for the LLM.

        Returns:
            Structured context dictionary
        """
        verified_complaints = EnhancedReviewAnalyzer.identify_verified_criticisms(
            reviews
        )
        meme_phrases = EnhancedReviewAnalyzer.extract_community_memes(reviews)
        sentiment = EnhancedReviewAnalyzer.calculate_sentiment_breakdown(reviews)

        # Get actual average score from AniList
        anilist_score = (
            anime_data.get("score", 0) / 10 if anime_data.get("score") else None
        )

        # Build complaints section
        complaints_text = []
        for complaint in verified_complaints:
            complaint_str = f"- {complaint.category.upper()}: Mentioned in {complaint.review_count} reviews (confidence: {complaint.confidence:.0%})"
            if complaint.example_quotes:
                quote = (
                    complaint.example_quotes[0][:100] + "..."
                    if len(complaint.example_quotes[0]) > 100
                    else complaint.example_quotes[0]
                )
                complaint_str += f'\n  Example: "{quote}"'
            complaints_text.append(complaint_str)

        return {
            "review_count": len(reviews),
            "verified_complaints": [
                {
                    "category": c.category,
                    "confidence": c.confidence,
                    "review_count": c.review_count,
                    "examples": c.example_quotes,
                }
                for c in verified_complaints
            ],
            "sentiment_breakdown": sentiment,
            "community_memes": meme_phrases,
            "anilist_score": anilist_score,
            "complaints_text": "\n".join(complaints_text)
            if complaints_text
            else "No consistent complaints found",
            "is_controversial": anime_data.get("controversyScore", 0) > 30,
            "controversy_score": anime_data.get("controversyScore", 0),
        }
