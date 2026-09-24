from __future__ import annotations

import datetime as dt

from .community.selector import suggest_communities
from .db.models import CommunityAttempt, Image, Post, PostStatus, RubricScore, ScoreChannel, Subreddit
from .db.session import get_session
from .generation.generator import draft_post
from .review.blind_scorer import blind_score_draft


def create_draft(image_path: str, extra_context: str = "") -> dict:
    """
    创作台的入口:选图 → 撰写。建一条 Image(如果这个路径没记录过)+ 一条
    Post(status=DRAFT),直接读图片内容生成标题/正文(多模态,不是靠文字描述),
    再给出候选社区建议(未验证,见 community/selector.py)。选社区、尝试发布
    是下一步,不在这里做。
    """
    session = get_session()

    image = session.query(Image).filter(Image.path == image_path).one_or_none()
    if image is None:
        image = Image(path=image_path)
        session.add(image)
        session.flush()
    image.used = True

    draft = draft_post(image_path, extra_context)
    candidates = suggest_communities(draft.title, draft.body)

    post = Post(
        image_id=image.id,
        title=draft.title,
        body=draft.body,
        status=PostStatus.DRAFT,
    )
    session.add(post)
    session.commit()

    return {
        "post_id": post.id,
        "title": post.title,
        "body": post.body,
        "candidates": [
            {"name": c.name, "fit_reason": c.fit_reason, "verified": c.verified} for c in candidates
        ],
    }


def record_attempt(
    post_id: int,
    subreddit: str,
    outcome: str,
    reason: str | None = None,
    reddit_url: str | None = None,
) -> CommunityAttempt:
    """
    记一次"选社区"的发布尝试。outcome 只能是 "rejected"(发布失败,换一个候选
    重试)或 "posted"(发成功了)。成功的话同步把 Post 更新成已发布状态,复盘
    看板才会认到这篇帖子。
    """
    if outcome not in ("rejected", "posted"):
        raise ValueError(f"invalid outcome: {outcome!r}")

    session = get_session()
    post = session.get(Post, post_id)
    if post is None:
        raise ValueError(f"no such post: {post_id}")

    attempt = CommunityAttempt(
        post_id=post_id,
        subreddit_name=subreddit,
        outcome=outcome,
        reason=reason,
    )
    session.add(attempt)

    if outcome == "posted":
        if session.get(Subreddit, subreddit) is None:
            session.add(Subreddit(name=subreddit))
        post.subreddit_name = subreddit
        post.reddit_url = reddit_url
        post.status = PostStatus.POSTED
        post.posted_at = dt.datetime.utcnow()

        # 这时候才知道最终社区是哪个,盲评打分(需要 subreddit 判断 community_fit)
        # 在这一刻做最合适——发布前的最后一次机会,不接触任何真实表现数据。
        result = blind_score_draft(post.title, post.body, subreddit)
        post.predicted_bucket = result.predicted_bucket
        post.predicted_raw_score = result.raw_score
        post.risk_gate_passed = result.risk.passed
        post.risk_notes = result.risk.reason
        for dim, val in result.scores.items():
            session.add(
                RubricScore(
                    post_id=post.id,
                    channel=ScoreChannel.BLIND,
                    dimension=dim,
                    score=val,
                    reasoning=result.reasoning.get(dim),
                )
            )

    session.commit()
    return attempt
