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
@click.argument("image_description")
@click.argument("subreddit")
def draft(image_description: str, subreddit: str) -> None:
    """生成一篇草稿(需要 ANTHROPIC_API_KEY)"""
    from .generation.generator import draft_post

    result = draft_post(image_description, subreddit)
    click.echo(f"Title: {result.title}\n\n{result.body}")


@cli.command()
@click.argument("title")
@click.argument("body")
@click.argument("subreddit")
def score(title: str, body: str, subreddit: str) -> None:
    """对一篇草稿跑盲评打分 + bucket 预测(需要 ANTHROPIC_API_KEY)"""
    from .review.blind_scorer import blind_score_draft

    result = blind_score_draft(title, body, subreddit)
    click.echo(f"raw_score={result.raw_score:.2f} bucket={result.predicted_bucket}")
    click.echo(f"risk: {'pass' if result.risk.passed else 'FAIL — ' + (result.risk.reason or '')}")
    for dim, val in result.scores.items():
        click.echo(f"  {dim}: {val}")


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


if __name__ == "__main__":
    cli()
