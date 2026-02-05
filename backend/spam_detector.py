"""Distributed spam detection using Redis with database fallback."""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SpamDetector:
    """Distributed spam detection using Redis with SQLite fallback."""

    # Rate limits
    MAX_COMMENTS_PER_MINUTE = 10
    BURST_THRESHOLD = 3
    BURST_DELAY_SECONDS = 10
    DUPLICATE_WINDOW_MINUTES = 5
    SIMILARITY_THRESHOLD = 0.9

    def __init__(self):
        self._redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis client if available."""
        try:
            import redis

            redis_url = os.getenv("REDIS_URL") or os.getenv("UPSTASH_REDIS_URL")
            if redis_url:
                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self._redis_client.ping()
                logger.info("SpamDetector: Redis connection established")
        except Exception as e:
            logger.warning(
                f"SpamDetector: Redis not available, using database fallback: {e}"
            )
            self._redis_client = None

    def _get_redis_key(self, ip_hash: str, key_type: str) -> str:
        """Generate Redis key for spam detection data."""
        return f"spam:{ip_hash}:{key_type}"

    async def check_spam(
        self, db: Session, ip_hash: str, content: str, author_name: str
    ) -> Tuple[bool, str]:
        """
        Check if a comment is spam using Redis or database fallback.

        Returns: (is_spam, reason)
        """
        if self._redis_client:
            return await self._check_spam_redis(ip_hash, content, author_name)
        else:
            return await self._check_spam_db(db, ip_hash, content, author_name)

    async def _check_spam_redis(
        self, ip_hash: str, content: str, author_name: str
    ) -> Tuple[bool, str]:
        """Check spam using Redis."""
        now = datetime.utcnow()
        pipe = self._redis_client.pipeline()

        # Keys for different rate limit windows
        minute_key = self._get_redis_key(ip_hash, "minute")
        burst_key = self._get_redis_key(ip_hash, "burst")
        last_comment_key = self._get_redis_key(ip_hash, "last_comment")
        comments_key = self._get_redis_key(ip_hash, "comments")

        # Check 1: Rate limit - max 10 comments per minute
        current_minute_count = self._redis_client.get(minute_key)
        if (
            current_minute_count
            and int(current_minute_count) >= self.MAX_COMMENTS_PER_MINUTE
        ):
            return True, "Too many comments. Please slow down."

        # Check 2: Burst detection
        recent_count = self._redis_client.zcard(comments_key) or 0
        last_comment_time = self._redis_client.get(last_comment_key)

        if last_comment_time and recent_count >= self.BURST_THRESHOLD:
            last_time = datetime.fromisoformat(last_comment_time)
            time_since_last = (now - last_time).total_seconds()
            if time_since_last < self.BURST_DELAY_SECONDS:
                return True, "Please wait a few seconds before posting again."

        # Check 3 & 4: Duplicate and similarity detection
        # Get recent comments from sorted set
        five_min_ago_timestamp = (
            now - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)
        ).timestamp()
        recent_comments = self._redis_client.zrangebyscore(
            comments_key, five_min_ago_timestamp, "+inf", withscores=False
        )

        content_lower = content.lower()
        for past_comment in recent_comments:
            past_data = past_comment.split("|", 1)
            if len(past_data) < 2:
                continue
            past_content = past_data[1]

            # Check exact duplicate
            if past_content.lower() == content_lower:
                return True, "You've already posted this comment recently."

            # Check similarity
            similarity = SequenceMatcher(
                None, content_lower, past_content.lower()
            ).ratio()
            if similarity > self.SIMILARITY_THRESHOLD:
                return True, "Your comment is too similar to a recent one."

        # Record this comment attempt
        pipe.multi()

        # Increment minute counter with 60s TTL
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)

        # Add to sorted set with timestamp as score
        comment_entry = f"{now.isoformat()}|{content}"
        pipe.zadd(comments_key, {comment_entry: now.timestamp()})

        # Remove old entries (older than 5 minutes)
        cutoff = (now - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)).timestamp()
        pipe.zremrangebyscore(comments_key, "-inf", cutoff)

        # Set expiration on comments set
        pipe.expire(comments_key, self.DUPLICATE_WINDOW_MINUTES * 60 + 10)

        # Update last comment time
        pipe.set(last_comment_key, now.isoformat(), ex=300)

        pipe.execute()

        return False, ""

    async def _check_spam_db(
        self, db: Session, ip_hash: str, content: str, author_name: str
    ) -> Tuple[bool, str]:
        """Check spam using database fallback (SQLite)."""
        from database import Comment

        now = datetime.utcnow()
        one_min_ago = now - timedelta(minutes=1)
        five_min_ago = now - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)

        # Check 1: Rate limit - max 10 comments per minute
        recent_count = (
            db.query(Comment)
            .filter(Comment.ip_hash == ip_hash, Comment.created_at > one_min_ago)
            .count()
        )

        if recent_count >= self.MAX_COMMENTS_PER_MINUTE:
            return True, "Too many comments. Please slow down."

        # Check 2: Burst detection
        if recent_count >= self.BURST_THRESHOLD:
            last_comment = (
                db.query(Comment)
                .filter(Comment.ip_hash == ip_hash)
                .order_by(Comment.created_at.desc())
                .first()
            )

            if last_comment:
                time_since_last = (now - last_comment.created_at).total_seconds()
                if time_since_last < self.BURST_DELAY_SECONDS:
                    return True, "Please wait a few seconds before posting again."

        # Check 3 & 4: Duplicate and similarity detection
        recent_comments = (
            db.query(Comment.content)
            .filter(Comment.ip_hash == ip_hash, Comment.created_at > five_min_ago)
            .all()
        )

        content_lower = content.lower()
        for (past_content,) in recent_comments:
            # Check exact duplicate
            if past_content.lower() == content_lower:
                return True, "You've already posted this comment recently."

            # Check similarity
            similarity = SequenceMatcher(
                None, content_lower, past_content.lower()
            ).ratio()
            if similarity > self.SIMILARITY_THRESHOLD:
                return True, "Your comment is too similar to a recent one."

        return False, ""

    async def cleanup_old_entries(self, ip_hash: Optional[str] = None):
        """Clean up old spam detection entries.

        If ip_hash is provided, clean only that IP's entries.
        Otherwise, clean all expired entries.
        """
        if not self._redis_client:
            return

        if ip_hash:
            # Clean specific IP
            keys = [
                self._get_redis_key(ip_hash, "minute"),
                self._get_redis_key(ip_hash, "burst"),
                self._get_redis_key(ip_hash, "last_comment"),
                self._get_redis_key(ip_hash, "comments"),
            ]
            for key in keys:
                self._redis_client.delete(key)
        else:
            # Clean all expired entries - Redis TTL handles this automatically
            pass


# Global instance
_spam_detector: Optional[SpamDetector] = None


def get_spam_detector() -> SpamDetector:
    """Get or create the global spam detector instance."""
    global _spam_detector
    if _spam_detector is None:
        _spam_detector = SpamDetector()
    return _spam_detector


async def check_spam(
    db: Session, ip_hash: str, content: str, author_name: str
) -> Tuple[bool, str]:
    """Convenience function to check spam."""
    detector = get_spam_detector()
    return await detector.check_spam(db, ip_hash, content, author_name)
