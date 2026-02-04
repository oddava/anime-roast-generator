"""Post-generation cleanup to remove statistical language from roasts."""

import re
import logging

logger = logging.getLogger(__name__)


class RoastCleaner:
    """Cleans generated roasts to remove robotic/statistical language."""

    # Patterns to detect and remove/replace
    STATISTICAL_PATTERNS = [
        # Percentages
        (r"\b\d+%", ""),
        (r"\b\d+ percent", ""),
        # Review counts
        (r"\bout of \d+ reviews?\b", "", re.IGNORECASE),
        (r"\b\d+ reviews?\b", ""),
        # Exact scores
        (r"\b\d+\.\d+/10\b", ""),
        (r"\bscored \d+", ""),
        (r"\brating of \d+", "", re.IGNORECASE),
        # Statistical language
        (r"\baccording to (the )?data\b", "", re.IGNORECASE),
        (r"\bstatistics show\b", "", re.IGNORECASE),
        (r"\bdata indicates\b", "", re.IGNORECASE),
        # Awkward constructions
        (r"\bcoming in at\b", "", re.IGNORECASE),
        (r"\ban earth-shattering\b", "", re.IGNORECASE),
        (r"\bglorious\b", "", re.IGNORECASE),  # Often used sarcastically with data
    ]

    # Replacement suggestions for common awkward phrases
    AWKWARD_REPLACEMENTS = {
        r"\bearth-shattering\b": "",
        r"\bglorious\b": "",
        r"\bexactly\? Right\.\b": "",
        r"\bSOMEONE[\'s]*\b": "someone",  # Normalize shouting
    }

    @staticmethod
    def clean_roast(roast_text: str) -> str:
        """Clean statistical language from roast.

        Returns cleaned text.
        """
        original = roast_text
        cleaned = roast_text

        # Remove statistical patterns
        for pattern in RoastCleaner.STATISTICAL_PATTERNS:
            if len(pattern) == 2:
                regex, replacement = pattern
                flags = 0
            else:
                regex, replacement, flags = pattern

            cleaned = re.sub(regex, replacement, cleaned, flags=flags)

        # Replace awkward phrases
        for pattern, replacement in RoastCleaner.AWKWARD_REPLACEMENTS.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # Clean up double spaces and awkward punctuation
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"\s+([.,!?])", r"\1", cleaned)
        cleaned = re.sub(r"([.,!?])\s*\1", r"\1", cleaned)

        # Remove empty parentheses that might be left
        cleaned = re.sub(r"\(\s*\)", "", cleaned)
        cleaned = re.sub(r"\[\s*\]", "", cleaned)

        # Trim
        cleaned = cleaned.strip()

        if cleaned != original:
            logger.info(f"Cleaned roast: removed statistical language")

        return cleaned

    @staticmethod
    def has_statistics(roast_text: str) -> bool:
        """Check if roast contains statistical language.

        Returns True if statistics detected.
        """
        checks = [
            # Percentages
            bool(re.search(r"\b\d+%", roast_text)),
            # Review counts
            bool(re.search(r"\b\d+ reviews?\b", roast_text, re.IGNORECASE)),
            # Exact scores with decimal
            bool(re.search(r"\b\d+\.\d+/10\b", roast_text)),
            # Statistical phrases
            bool(
                re.search(
                    r"\b(according to (the )?data|statistics show|data indicates)\b",
                    roast_text,
                    re.IGNORECASE,
                )
            ),
            # Awkward data-focused phrases
            bool(re.search(r"\bcoming in at\b", roast_text, re.IGNORECASE)),
        ]

        return any(checks)
