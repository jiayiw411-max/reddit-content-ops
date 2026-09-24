from __future__ import annotations

import datetime as dt

from ..db.models import PerformanceSnapshot, Post, PostStatus, Subreddit
from ..db.session import get_session


def record_snapshot(
    url: str,
    score: int,
    num_comments: int,
    upvote_ratio: float | None = None,
    views: int | None = None,
    subreddit: str | None = None,
    title: str | None = None,
) -> PerformanceSnapshot:
    """
    人工录入一次表现快照——你自己在浏览器里看到的数字(书签工具帮你把 score/
    comments/upvote_ratio 抄进一条命令,你可以再手动加上 views,这是 API 永远
    拿不到、只有作者本人能看到的数据)。

    第一次记录某个 url 时,如果本地还没有这条 Post,就用 subreddit/title 建一条
    最小记录(status=POSTED);后续同一个 url 再记录,直接找到已有的 Post 追加
    一条新快照,不需要重复传 subreddit/title。
    """
    session = get_session()
    post = session.query(Post).filter(Post.reddit_url == url).one_or_none()

    if post is None:
        if subreddit and session.get(Subreddit, subreddit) is None:
            session.add(Subreddit(name=subreddit))
        post = Post(
            reddit_url=url,
            subreddit_name=subreddit,
            title=title or "",
            body="",
            status=PostStatus.POSTED,
            posted_at=dt.datetime.utcnow(),
        )
        session.add(post)
        session.flush()

    snapshot = PerformanceSnapshot(
        post_id=post.id,
        checked_at=dt.datetime.utcnow(),
        score=score,
        num_comments=num_comments,
        upvote_ratio=upvote_ratio,
        views=views,
    )
    session.add(snapshot)
    session.commit()
    return snapshot
