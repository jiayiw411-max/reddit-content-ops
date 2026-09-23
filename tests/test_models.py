from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from reddit_ops.db.models import Base, Image, Post, PostStatus, Subreddit


def test_create_and_query_post(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    image = Image(path="/tmp/example.jpg")
    subreddit = Subreddit(name="CasualUK")
    session.add_all([image, subreddit])
    session.commit()

    post = Post(
        image_id=image.id,
        subreddit_name=subreddit.name,
        title="t",
        body="b",
        status=PostStatus.DRAFT,
    )
    session.add(post)
    session.commit()

    fetched = session.query(Post).filter_by(title="t").one()
    assert fetched.status == PostStatus.DRAFT
    assert fetched.subreddit.name == "CasualUK"
    assert fetched.image.path == "/tmp/example.jpg"


def test_ban_report_links_to_post(tmp_path):
    from reddit_ops.db.models import BanReport

    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    post = Post(title="t", body="b", status=PostStatus.BANNED)
    session.add(post)
    session.commit()

    report = BanReport(post_id=post.id, subreddit_name="CasualUK", reason="疑似广告")
    session.add(report)
    session.commit()

    assert post.ban_reports[0].reason == "疑似广告"
