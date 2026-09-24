from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Reddit AI 内容运营助手"""


@cli.command(name="init")
def init_cmd() -> None:
    """初始化本地 SQLite 数据库"""
    from .db.session import init_db

    init_db()
    click.echo("db initialized")


@cli.command()
def track() -> None:
    """抓取所有已发布帖子的最新表现数据(需要官方 API 审批通过)"""
    from .tracker.fetcher import track_pending_posts

    snapshots = track_pending_posts()
    click.echo(f"updated {len(snapshots)} posts")


@cli.command()
@click.option("--url", required=True, help="已发布帖子的完整链接")
@click.option("--score", "score_", type=int, required=True, help="当前 upvotes/score")
@click.option("--comments", type=int, required=True, help="当前评论数")
@click.option("--upvote-ratio", type=float, default=None, help="可选,0-1 之间")
@click.option("--views", type=int, default=None, help="可选,只有你自己能看到的浏览量")
@click.option("--subreddit", default=None, help="第一次记录这篇帖子时提供")
@click.option("--title", default=None, help="第一次记录这篇帖子时可选提供")
def record(
    url: str,
    score_: int,
    comments: int,
    upvote_ratio: float | None,
    views: int | None,
    subreddit: str | None,
    title: str | None,
) -> None:
    """人工录入一次表现快照(配合书签工具或自己肉眼看数字)"""
    from .tracker.manual import record_snapshot

    snapshot = record_snapshot(
        url=url,
        score=score_,
        num_comments=comments,
        upvote_ratio=upvote_ratio,
        views=views,
        subreddit=subreddit,
        title=title,
    )
    click.echo(f"recorded: score={snapshot.score} comments={snapshot.num_comments} at {snapshot.checked_at}")


@cli.command()
@click.option("--port", type=int, default=8765, help="本地端口")
def serve(port: int) -> None:
    """启动本地网页(创作台 + 复盘看板,启动后留着别关)"""
    import uvicorn

    click.echo(f"看板地址: http://127.0.0.1:{port}  (Ctrl+C 停止)")
    uvicorn.run("reddit_ops.webapp:app", host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    cli()
