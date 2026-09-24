from unittest.mock import patch

import pytest
from reddit_ops.db import session as session_module
from reddit_ops.db.models import Base, Image
from reddit_ops.generation.generator import DraftResult
from reddit_ops.workspace import create_draft
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _use_temp_db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(session_module, "SessionLocal", Session)
    return Session


def _make_image_folder(tmp_path, names):
    folder = tmp_path / "photos"
    folder.mkdir()
    for name in names:
        (folder / name).write_bytes(b"fake image bytes")
    return str(folder)


_FAKE_DRAFT = DraftResult(title="t", body="b")


def test_create_draft_skips_used_images(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)
    folder = _make_image_folder(tmp_path, ["a.jpg", "b.jpg"])

    used_path = str(tmp_path / "photos" / "a.jpg")
    session = Session()
    session.add(Image(path=used_path, used=True))
    session.commit()

    with (
        patch("reddit_ops.workspace.draft_post", return_value=_FAKE_DRAFT) as mock_draft,
        patch("reddit_ops.workspace.suggest_communities", return_value=[]),
    ):
        create_draft(folder)
        chosen_path = mock_draft.call_args[0][0]

    assert chosen_path != used_path
    assert chosen_path.endswith("b.jpg")


def test_create_draft_marks_image_used(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)
    folder = _make_image_folder(tmp_path, ["only.jpg"])

    with (
        patch("reddit_ops.workspace.draft_post", return_value=_FAKE_DRAFT),
        patch("reddit_ops.workspace.suggest_communities", return_value=[]),
    ):
        result = create_draft(folder)

    session = Session()
    image = session.query(Image).filter(Image.path == result["image_path"]).one()
    assert image.used is True


def test_create_draft_raises_when_all_used(tmp_path, monkeypatch):
    Session = _use_temp_db(tmp_path, monkeypatch)
    folder = _make_image_folder(tmp_path, ["a.jpg"])

    session = Session()
    session.add(Image(path=str(tmp_path / "photos" / "a.jpg"), used=True))
    session.commit()

    with pytest.raises(ValueError, match="用过"):
        create_draft(folder)


def test_create_draft_raises_on_empty_folder(tmp_path, monkeypatch):
    _use_temp_db(tmp_path, monkeypatch)
    folder = tmp_path / "empty"
    folder.mkdir()

    with pytest.raises(ValueError):
        create_draft(str(folder))
