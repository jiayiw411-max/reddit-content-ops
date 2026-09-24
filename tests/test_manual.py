from reddit_ops.db import session as session_module
from reddit_ops.db.models import Base, Post, PostStatus
from reddit_ops.tracker.manual import record_snapshot
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _use_temp_db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(session_module, "SessionLocal", Session)
    return Session


def test_record_snapshot_creates_post_on_first_call(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)

    snapshot = record_snapshot(
        url="https://www.reddit.com/r/CasualUK/comments/abc123/test/",
        score=41,
        num_comments=30,
        upvote_ratio=0.95,
        views=500,
        subreddit="CasualUK",
        title="test post",
    )

    assert snapshot.score == 41
    assert snapshot.views == 500

    post = Session().get(Post, snapshot.post_id)
    assert post.subreddit_name == "CasualUK"
    assert post.status == PostStatus.POSTED


def test_record_snapshot_reuses_existing_post_by_url(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)

    url = "https://www.reddit.com/r/CasualUK/comments/abc123/test/"
    first = record_snapshot(url=url, score=10, num_comments=2, subreddit="CasualUK")
    second = record_snapshot(url=url, score=41, num_comments=30)

    assert first.post_id == second.post_id

    post = Session().get(Post, second.post_id)
    assert len(post.snapshots) == 2
    assert post.snapshots[-1].score == 41
