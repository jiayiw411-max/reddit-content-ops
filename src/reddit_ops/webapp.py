from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .db.models import Post, PostStatus
from .db.session import get_session
from .tracker.manual import record_snapshot
from .workspace import create_draft, record_attempt

app = FastAPI(title="Reddit AI 内容运营助手")

# 书签是在 reddit.com 页面里发起的跨源请求,只放行这一个来源,不是完全开放。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.reddit.com"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------- 创作台:选图 → 撰写 → 选社区(带失败重试) ----------


class DraftPayload(BaseModel):
    image_path: str
    image_description: str


@app.post("/api/drafts")
def api_create_draft(payload: DraftPayload) -> dict:
    return create_draft(payload.image_path, payload.image_description)


class AttemptPayload(BaseModel):
    subreddit: str
    outcome: str  # "rejected" | "posted"
    reason: str | None = None
    reddit_url: str | None = None


@app.post("/api/drafts/{post_id}/attempts")
def api_record_attempt(post_id: int, payload: AttemptPayload) -> dict:
    attempt = record_attempt(
        post_id=post_id,
        subreddit=payload.subreddit,
        outcome=payload.outcome,
        reason=payload.reason,
        reddit_url=payload.reddit_url,
    )
    return {"ok": True, "outcome": attempt.outcome, "attempted_at": attempt.attempted_at.isoformat()}


@app.get("/api/drafts")
def api_list_drafts() -> list[dict]:
    session = get_session()
    posts = session.query(Post).order_by(Post.created_at.desc()).all()
    return [
        {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "status": post.status.value,
            "predicted_bucket": post.predicted_bucket,
            "risk_gate_passed": post.risk_gate_passed,
            "attempts": [
                {
                    "subreddit": a.subreddit_name,
                    "outcome": a.outcome,
                    "reason": a.reason,
                    "attempted_at": a.attempted_at.isoformat(),
                }
                for a in sorted(post.community_attempts, key=lambda a: a.attempted_at)
            ],
        }
        for post in posts
        if post.status != PostStatus.POSTED
    ]


# ---------- 复盘看板:已发布帖子的表现追踪 ----------


class RecordPayload(BaseModel):
    url: str
    score: int
    comments: int
    upvote_ratio: float | None = None
    views: int | None = None
    subreddit: str | None = None
    title: str | None = None


@app.post("/api/record")
def api_record(payload: RecordPayload) -> dict:
    snapshot = record_snapshot(
        url=payload.url,
        score=payload.score,
        num_comments=payload.comments,
        upvote_ratio=payload.upvote_ratio,
        views=payload.views,
        subreddit=payload.subreddit,
        title=payload.title,
    )
    return {"ok": True, "post_id": snapshot.post_id, "checked_at": snapshot.checked_at.isoformat()}


@app.get("/api/posts")
def api_posts() -> list[dict]:
    session = get_session()
    posts = session.query(Post).filter(Post.status == PostStatus.POSTED).order_by(Post.posted_at.desc()).all()
    return [
        {
            "id": post.id,
            "title": post.title,
            "subreddit": post.subreddit_name,
            "url": post.reddit_url,
            "posted_at": post.posted_at.isoformat() if post.posted_at else None,
            "predicted_bucket": post.predicted_bucket,
            "snapshots": [
                {
                    "checked_at": s.checked_at.isoformat(),
                    "score": s.score,
                    "comments": s.num_comments,
                    "upvote_ratio": s.upvote_ratio,
                    "views": s.views,
                }
                for s in sorted(post.snapshots, key=lambda s: s.checked_at)
            ],
        }
        for post in posts
    ]


_STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")
