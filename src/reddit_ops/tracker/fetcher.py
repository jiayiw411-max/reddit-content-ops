from __future__ import annotations

import datetime as dt

from ..db.models import PerformanceSnapshot, Post
from ..db.session import get_session
from ..reddit_client import get_json


def take_snapshot(post: Post) -> PerformanceSnapshot:
    """
    只读,不发布。工具不自动发帖——发布后把帖子链接回填到 post.reddit_post_id,
    这里才能开始追踪。

    走公开的 /comments/{id} 接口,只拉稳定暴露的字段:score(净 upvotes,即这篇
    帖子贡献的 karma)、num_comments、upvote_ratio、num_crossposts(Reddit 官方
    对"转发"最接近的代理指标)。浏览量 Reddit 不对外暴露,不在这里采集——如果
    之后要接登录态浏览器读取 insights 页面作为补充,应该单独开一个模块,不要
    混进这条稳定的公开接口读取路径,避免一个脆弱数据源拖垮整个追踪任务。
    """
    if not post.reddit_post_id:
        raise ValueError(f"post {post.id} has no reddit_post_id yet — not published through this tool")

    listing = get_json(f"/comments/{post.reddit_post_id}")
    submission = listing[0]["data"]["children"][0]["data"]

    snapshot = PerformanceSnapshot(
        post_id=post.id,
        checked_at=dt.datetime.utcnow(),
        score=submission["score"],
        num_comments=submission["num_comments"],
        upvote_ratio=submission.get("upvote_ratio"),
        num_crossposts=submission.get("num_crossposts", 0),
    )

    session = get_session()
    session.add(snapshot)
    session.commit()
    return snapshot


def track_pending_posts() -> list[PerformanceSnapshot]:
    session = get_session()
    posts = session.query(Post).filter(Post.reddit_post_id.isnot(None)).all()
    return [take_snapshot(p) for p in posts]
