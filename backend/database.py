from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Index,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Comment(Base):
    """Database model for threaded anime comments."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    anime_id = Column(Integer, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    author_name = Column(String(50), nullable=False)
    ip_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_deleted = Column(Integer, default=0, nullable=False)  # 0 = active, 1 = deleted
    is_edited = Column(Integer, default=0, nullable=False)  # 0 = not edited, 1 = edited

    # Vote counts (denormalized for performance)
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    score = Column(Integer, default=0, nullable=False)  # upvotes - downvotes

    # Threading
    path = Column(
        String(500), nullable=True, index=True
    )  # Materialized path for tree structure
    depth = Column(Integer, default=0, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)

    # Relationships
    replies = relationship("Comment", backref="parent", remote_side=[id])
    votes = relationship(
        "CommentVote", back_populates="comment", cascade="all, delete-orphan"
    )

    # Composite indexes
    __table_args__ = (
        Index("idx_anime_score", "anime_id", "score"),
        Index("idx_anime_created", "anime_id", "created_at"),
        Index("idx_parent_id", "parent_id"),
    )


class CommentVote(Base):
    """Database model for comment votes."""

    __tablename__ = "comment_votes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip_hash = Column(String(64), nullable=False, index=True)
    vote_type = Column(Integer, nullable=False)  # 1 = upvote, -1 = downvote
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    comment = relationship("Comment", back_populates="votes")

    # Unique constraint to prevent duplicate votes
    __table_args__ = (
        UniqueConstraint("comment_id", "ip_hash", name="unique_comment_vote"),
    )


# Database setup
data_dir = os.getenv("DATA_DIR", ".")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{data_dir}/comments.db")

# Create engine with proper settings for SQLite
echo = os.getenv("ENVIRONMENT") == "development"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
    echo=echo,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
