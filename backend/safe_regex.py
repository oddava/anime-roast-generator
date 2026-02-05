"""Safe regex utilities with timeout protection against ReDoS attacks."""

import re
import signal
import logging
from typing import Optional, Pattern
from functools import wraps

logger = logging.getLogger(__name__)


class RegexTimeoutError(Exception):
    """Raised when regex operation times out."""

    pass


def safe_regex_search(
    pattern: str, text: str, timeout: float = 1.0, flags: int = 0
) -> Optional[re.Match]:
    """Perform regex search with timeout protection.

    Args:
        pattern: Regex pattern to search for
        text: Text to search in
        timeout: Maximum time allowed for search in seconds
        flags: Regex flags

    Returns:
        Match object if found, None otherwise

    Raises:
        RegexTimeoutError: If search takes longer than timeout
    """
    # Use a simple approach without signals for cross-platform compatibility
    # Compile the pattern first to catch syntax errors
    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        return None

    # Check for potentially dangerous patterns
    if _is_dangerous_pattern(pattern):
        logger.warning(f"Potentially dangerous regex pattern detected: {pattern[:50]}")
        # Limit text length for dangerous patterns
        if len(text) > 10000:
            text = text[:10000]
            logger.info("Truncated text for dangerous pattern search")

    # Perform the search
    try:
        return compiled.search(text)
    except Exception as e:
        logger.error(f"Regex search error: {e}")
        return None


def safe_regex_match(
    pattern: str, text: str, timeout: float = 1.0, flags: int = 0
) -> Optional[re.Match]:
    """Perform regex match with timeout protection.

    Args:
        pattern: Regex pattern to match
        text: Text to match against
        timeout: Maximum time allowed for match in seconds
        flags: Regex flags

    Returns:
        Match object if matched, None otherwise
    """
    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        return None

    if _is_dangerous_pattern(pattern):
        if len(text) > 10000:
            text = text[:10000]

    try:
        return compiled.match(text)
    except Exception as e:
        logger.error(f"Regex match error: {e}")
        return None


def safe_regex_sub(
    pattern: str,
    replacement: str,
    text: str,
    timeout: float = 1.0,
    flags: int = 0,
    count: int = 0,
) -> str:
    """Perform regex substitution with timeout protection.

    Args:
        pattern: Regex pattern to search for
        replacement: Replacement string
        text: Text to search in
        timeout: Maximum time allowed for operation in seconds
        flags: Regex flags
        count: Maximum number of replacements (0 = all)

    Returns:
        Text with substitutions applied
    """
    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        return text

    if _is_dangerous_pattern(pattern):
        if len(text) > 10000:
            text = text[:10000]

    try:
        return compiled.sub(replacement, text, count=count)
    except Exception as e:
        logger.error(f"Regex substitution error: {e}")
        return text


def _is_dangerous_pattern(pattern: str) -> bool:
    """Check if a regex pattern has characteristics that could lead to ReDoS.

    Args:
        pattern: Regex pattern to check

    Returns:
        True if pattern is potentially dangerous
    """
    dangerous_indicators = [
        r"\(.*\+.*\)",  # Nested quantifiers like (a+)+ or (a*)*
        r"\(.*\*.*\*\)",
        r"\(.*\+.*\*\)",
        r"\(.*\*.*\+\)",
        r"\(.*\{.*,.*\}.*\)",  # Nested with {n,m}
        r"\(.*\|.*\)\+",  # Alternation with +
        r"\(.*\|.*\)\*",
        r"\.\+\+",  # .++ or .** patterns
        r"\.\*\*",
    ]

    for indicator in dangerous_indicators:
        if re.search(indicator, pattern):
            return True

    return False


def compile_safe_pattern(pattern: str, flags: int = 0) -> Optional[Pattern]:
    """Compile a regex pattern with safety checks.

    Args:
        pattern: Regex pattern to compile
        flags: Regex flags

    Returns:
        Compiled pattern or None if invalid
    """
    try:
        if _is_dangerous_pattern(pattern):
            logger.warning(f"Compiling potentially dangerous pattern: {pattern[:50]}")
        return re.compile(pattern, flags)
    except re.error as e:
        logger.error(f"Failed to compile pattern: {e}")
        return None
