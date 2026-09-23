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
    """抓取所有已发布帖子的最新表现数据(需要 Reddit API 凭证)"""
    from .tracker.fetcher import track_pending_posts

    snapshots = track_pending_posts()
    click.echo(f"updated {len(snapshots)} posts")


if __name__ == "__main__":
    cli()
