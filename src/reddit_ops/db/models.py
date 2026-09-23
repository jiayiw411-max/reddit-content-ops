from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"
    BANNED = "banned"


class ScoreChannel(str, enum.Enum):
    MAIN = "main"
    BLIND = "blind"
    CROSS = "cross"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="image")


class Subreddit(Base):
    __tablename__ = "subreddits"

    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    rules_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_fetched_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    requires_flair: Mapped[bool] = mapped_column(Boolean, default=False)
    allows_image_post: Mapped[bool] = mapped_column(Boolean, default=True)
    # 用于把实际表现换算成"相对该社区基准"的 bucket,而不是用绝对 upvotes
    baseline_score_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_sample_count: Mapped[int] = mapped_column(Integer, default=0)

    posts: Mapped[list["Post"]] = relationship(back_populates="subreddit")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("images.id"), nullable=True)
    subreddit_name: Mapped[str | None] = mapped_column(ForeignKey("subreddits.name"), nullable=True)

    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.DRAFT)

    risk_gate_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    predicted_bucket: Mapped[str | None] = mapped_column(String(16), nullable=True)
    predicted_raw_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 用户手动发布后回填 —— 工具不自动发帖,这两个字段由用户提供帖子链接后写入
    reddit_post_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reddit_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    posted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    image: Mapped[Image | None] = relationship(back_populates="posts")
    subreddit: Mapped[Subreddit | None] = relationship(back_populates="posts")
    rubric_scores: Mapped[list["RubricScore"]] = relationship(back_populates="post")
    snapshots: Mapped[list["PerformanceSnapshot"]] = relationship(back_populates="post")
    ban_reports: Mapped[list["BanReport"]] = relationship(back_populates="post")


class RubricScore(Base):
    __tablename__ = "rubric_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    channel: Mapped[ScoreChannel] = mapped_column(Enum(ScoreChannel))
    dimension: Mapped[str] = mapped_column(String(64))
    score: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    post: Mapped[Post] = relationship(back_populates="rubric_scores")


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    checked_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    score: Mapped[int] = mapped_column(Integer)  # 净 upvotes,即这篇帖子贡献的 karma
    num_comments: Mapped[int] = mapped_column(Integer)
    upvote_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_crossposts: Mapped[int] = mapped_column(Integer, default=0)  # "转发"的官方代理指标

    post: Mapped[Post] = relationship(back_populates="snapshots")


class BanReport(Base):
    __tablename__ = "ban_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    subreddit_name: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(Text)
    reported_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    root_cause_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    post: Mapped[Post] = relationship(back_populates="ban_reports")
