from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    BigInteger,
    ARRAY,
)

from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    bio = Column(Text)
    followers_count = Column(Integer)
    following_count = Column(Integer)
    posts_count = Column(Integer)
    is_verified = Column(Boolean, default=False)
    profile_pic_url = Column(Text)
    external_url = Column(Text)
    is_private = Column(Boolean)
    metadata_json = Column("metadata", JSON, default={})
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    post_id = Column(
        String(255), unique=True
    )  # This seems to be the BigInt ID as string
    shortcode = Column(String(50), unique=True)
    post_url = Column(Text)
    username = Column(String(255))
    caption = Column(Text)
    likes_count = Column(Integer)
    comments_count = Column(Integer)
    posted_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column("metadata", JSON, default={})


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    comment_id = Column(String(255), unique=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    username = Column(String(255))
    comment_text = Column(Text)
    likes_count = Column(Integer)
    created_at = Column(DateTime(timezone=True))
    parent_comment_id = Column(String(255))
    metadata_json = Column("metadata", JSON, default={})


class InstagramAccount(Base):
    """Model untuk instagram_accounts table"""

    __tablename__ = "instagram_accounts"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_encrypted = Column(Text, nullable=False)
    email = Column(String(255))
    phone = Column(String(50))

    # Account Status
    status = Column(
        String(20), default="active"
    )  # active, banned, suspended, rate_limited, inactive
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    # Ban Information
    ban_reason = Column(Text)
    banned_at = Column(DateTime(timezone=True))
    ban_count = Column(Integer, default=0)
    last_ban_type = Column(String(50))  # temporary, permanent, challenge_required

    # Rate Limiting
    is_rate_limited = Column(Boolean, default=False)
    rate_limited_at = Column(DateTime(timezone=True))
    rate_limit_expires_at = Column(DateTime(timezone=True))
    rate_limit_count = Column(Integer, default=0)

    # Usage Statistics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    last_success_at = Column(DateTime(timezone=True))
    last_error_at = Column(DateTime(timezone=True))
    last_error_message = Column(Text)

    # Scraping Statistics (Daily)
    posts_scraped_today = Column(Integer, default=0)
    comments_scraped_today = Column(Integer, default=0)
    last_daily_reset = Column(DateTime(timezone=True), default=func.now())

    # Account Health Score (0-100)
    health_score = Column(Integer, default=100)
    trust_level = Column(
        String(20), default="new"
    )  # new, trusted, veteran, risky, untrusted

    # Account Creation Info
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Account Age & Reliability
    account_age_days = Column(Integer)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    is_business = Column(Boolean, default=False)

    # Session Management
    session_file = Column(Text)
    session_expires_at = Column(DateTime(timezone=True))

    # Proxy Information
    proxy_host = Column(String(255))
    proxy_port = Column(Integer)
    proxy_username = Column(String(100))
    proxy_type = Column(String(20))  # http, socks5, residential

    # Notes & Tags
    notes = Column(Text)
    tags = Column(ARRAY(String))

    # Metadata
    metadata_json = Column("metadata", JSON, default={})
