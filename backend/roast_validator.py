"""Post-generation validation and hallucination detection."""

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class RoastValidator:
    """Validates generated roasts for hallucinations and factual errors."""

    # Common hallucination patterns
    HALLUCINATION_PATTERNS = {
        "fake_ratings": [
            r"\b\d+\.\d+/10\b",  # Matches "10.0/10", "7.5/10", etc.
            r"\b\d+/10\b",  # Matches "5/10", "10/10", etc.
        ],
        "pacing_claims": [
            r"(?:feels? like watching|pacing is) (?:paint dry|glacier|snail|dragging)",
            r"pacing.*(?:terrible|awful|boring|slow)",
        ],
        "character_claims": [
            r"(?:characters?|protagonist).*unlikable",
            r"bar for likeability",
            r"shallow characters",
        ],
        "ending_claims": [
            r"(?:ending|finale).*fell off",
            r"(?:ending|finale).*disappointing",
        ],
    }

    @staticmethod
    def validate_and_fix_roast(
        roast_text: str, anime_data: dict, review_context: Optional[dict]
    ) -> Tuple[str, list[str]]:
        """Validate a generated roast and fix any hallucinations.

        Returns:
            Tuple of (fixed_roast, list_of_issues_found)
        """
        issues = []
        fixed_roast = roast_text

        # Check for fake rating claims
        rating_issues = RoastValidator._check_fake_ratings(fixed_roast, anime_data)
        if rating_issues:
            issues.extend(rating_issues)
            fixed_roast = RoastValidator._fix_fake_ratings(fixed_roast, anime_data)

        # Check for unverified pacing complaints
        if review_context:
            pacing_issues = RoastValidator._check_unverified_claims(
                fixed_roast, review_context, "pacing"
            )
            if pacing_issues:
                issues.extend(pacing_issues)
                fixed_roast = RoastValidator._soften_claim(fixed_roast, "pacing")

            # Check for unverified character complaints
            char_issues = RoastValidator._check_unverified_claims(
                fixed_roast, review_context, "characters"
            )
            if char_issues:
                issues.extend(char_issues)
                fixed_roast = RoastValidator._soften_claim(fixed_roast, "characters")

            # Check for unverified ending complaints
            ending_issues = RoastValidator._check_unverified_claims(
                fixed_roast, review_context, "ending"
            )
            if ending_issues:
                issues.extend(ending_issues)
                fixed_roast = RoastValidator._soften_claim(fixed_roast, "ending")

        # Check for overuse of meme phrases
        meme_issues = RoastValidator._check_meme_overuse(fixed_roast)
        if meme_issues:
            issues.extend(meme_issues)

        return fixed_roast, issues

    @staticmethod
    def _check_fake_ratings(roast_text: str, anime_data: dict) -> list[str]:
        """Check if the roast contains fake rating claims."""
        issues = []

        # Look for rating patterns
        rating_matches = re.findall(r"\b(\d+(?:\.\d+)?)/10\b", roast_text)

        if rating_matches:
            actual_score = (
                anime_data.get("score", 0) / 10 if anime_data.get("score") else None
            )

            for claimed_rating in rating_matches:
                claimed = float(claimed_rating)

                # If actual score is available, check if claimed rating is way off
                if actual_score is not None:
                    if (
                        abs(claimed - actual_score) > 1.0
                    ):  # More than 1 point difference
                        issues.append(
                            f"FAKE RATING: Claimed {claimed}/10 but actual AniList score is {actual_score:.1f}/10"
                        )
                else:
                    # No actual score available - any claimed rating is suspicious
                    issues.append(
                        f"SUSPICIOUS RATING: Claimed {claimed}/10 but no source data available"
                    )

        return issues

    @staticmethod
    def _fix_fake_ratings(roast_text: str, anime_data: dict) -> str:
        """Replace fake ratings with actual data or remove them."""
        actual_score = anime_data.get("score")

        if actual_score:
            # Replace any X/10 with actual score
            score_text = f"{actual_score / 10:.1f}/10"
            roast_text = re.sub(r"\b\d+(?:\.\d+)?/10\b", score_text, roast_text)
        else:
            # Remove rating claims if no actual data
            roast_text = re.sub(r"\s*\b\d+(?:\.\d+)?/10\b", "", roast_text)

        return roast_text

    @staticmethod
    def _check_unverified_claims(
        roast_text: str, review_context: dict, category: str
    ) -> list[str]:
        """Check if claims about a category are verified in reviews."""
        issues = []

        # Get verified complaints
        verified_complaints = review_context.get("verified_complaints", [])
        complaint_categories = [c["category"] for c in verified_complaints]

        # Check if the category is mentioned in the roast but not verified
        category_keywords = {
            "pacing": ["pacing", "slow", "dragging", "rushed"],
            "characters": ["character", "protagonist", "unlikable", "shallow"],
            "ending": ["ending", "finale", "conclusion", "fell off"],
        }

        roast_lower = roast_text.lower()

        # Check if roast mentions this category
        mentions_category = any(
            kw in roast_lower for kw in category_keywords.get(category, [])
        )

        # Check if it's verified
        is_verified = category in complaint_categories

        if mentions_category and not is_verified:
            issues.append(
                f"UNVERIFIED CLAIM: Roast mentions {category} issues but no verified complaints found in reviews"
            )

        return issues

    @staticmethod
    def _soften_claim(roast_text: str, category: str) -> str:
        """Soften unverified claims by making them more speculative."""
        # Replace definitive statements with softer language
        softeners = {
            "pacing": {
                r"(?:the )?pacing (?:is|feels?) (?:like|watching)": "some might say the pacing feels like",
                r"(?:the )?pacing (?:is|was) (?:terrible|awful|bad)": "the pacing isn't for everyone",
            },
            "characters": {
                r"(?:the )?characters? (?:are|is) (?:unlikable|shallow|bland)": "the characters might not click with everyone",
                r"bar for likeability": "character appeal varies",
            },
            "ending": {
                r"(?:the )?ending (?:fell off|was disappointing)": "the ending divided some viewers",
                r"(?:the )?finale (?:fell off|was disappointing)": "the finale got mixed reactions",
            },
        }

        patterns = softeners.get(category, {})
        for pattern, replacement in patterns.items():
            roast_text = re.sub(pattern, replacement, roast_text, flags=re.IGNORECASE)

        return roast_text

    @staticmethod
    def _check_meme_overuse(roast_text: str) -> list[str]:
        """Check for overuse of meme phrases."""
        issues = []

        meme_phrases = ["cope", "copium", "mid", "fell off", "peaked", "carried by"]
        roast_lower = roast_text.lower()

        meme_count = sum(roast_lower.count(phrase) for phrase in meme_phrases)

        if meme_count >= 3:
            issues.append(
                f"MEME OVERUSE: Found {meme_count} meme phrases - roast may feel generic"
            )

        return issues

    @staticmethod
    def generate_accuracy_warning(
        roast_text: str, anime_data: dict, review_context: Optional[dict]
    ) -> Optional[str]:
        """Generate a warning if the roast has significant accuracy issues."""
        _, issues = RoastValidator.validate_and_fix_roast(
            roast_text, anime_data, review_context
        )

        if not issues:
            return None

        critical_issues = [i for i in issues if i.startswith(("FAKE", "UNVERIFIED"))]

        if len(critical_issues) >= 2:
            return "Note: This roast may contain some creative liberties."

        return None
