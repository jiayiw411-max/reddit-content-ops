from unittest.mock import patch

import pytest
from reddit_ops.db import session as session_module
from reddit_ops.db.models import Base, Post, PostStatus
from reddit_ops.review.blind_scorer import BlindScoreResult
from reddit_ops.review.rubric import QUALITY_DIMENSIONS, RiskGateResult
from reddit_ops.workspace import record_attempt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _use_temp_db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(session_module, "SessionLocal", Session)
    return Session


def _make_draft_post(Session) -> int:
    session = Session()
    post = Post(title="t", body="b", status=PostStatus.DRAFT)
    session.add(post)
    session.commit()
    return post.id


def test_record_attempt_rejected_does_not_publish(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)
    post_id = _make_draft_post(Session)

    attempt = record_attempt(post_id, "CasualUK", "rejected", reason="missing flair")

    assert attempt.outcome == "rejected"
    post = Session().get(Post, post_id)
    assert post.status == PostStatus.DRAFT
    assert post.reddit_url is None


def test_record_attempt_posted_publishes_and_scores(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)
    post_id = _make_draft_post(Session)

    fake_result = BlindScoreResult(
        scores={dim: 4.0 for dim in QUALITY_DIMENSIONS},
        raw_score=4.0,
        predicted_bucket="高",
        risk=RiskGateResult(passed=True, reason=None),
        reasoning={dim: "ok" for dim in QUALITY_DIMENSIONS},
    )

    with patch("reddit_ops.workspace.blind_score_draft", return_value=fake_result) as mocked:
        attempt = record_attempt(post_id, "CasualUK", "posted", reddit_url="https://www.reddit.com/r/CasualUK/x/")
        mocked.assert_called_once()

    assert attempt.outcome == "posted"
    post = Session().get(Post, post_id)
    assert post.status == PostStatus.POSTED
    assert post.subreddit_name == "CasualUK"
    assert post.predicted_bucket == "高"
    assert post.risk_gate_passed is True
    assert len(post.rubric_scores) == len(QUALITY_DIMENSIONS)


def test_record_attempt_invalid_outcome_rejected(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)
    post_id = _make_draft_post(Session)

    with pytest.raises(ValueError):
        record_attempt(post_id, "CasualUK", "maybe")
