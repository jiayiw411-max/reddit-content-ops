import pytest

from reddit_ops.review.rubric import QUALITY_DIMENSIONS, compute_raw_score, predict_bucket


def test_compute_raw_score_equal_weight():
    scores = {dim: 4.0 for dim in QUALITY_DIMENSIONS}
    assert compute_raw_score(scores) == 4.0


def test_compute_raw_score_missing_dimension():
    scores = {dim: 4.0 for dim in list(QUALITY_DIMENSIONS)[:-1]}
    with pytest.raises(ValueError):
        compute_raw_score(scores)


@pytest.mark.parametrize(
    "raw_score,expected_bucket",
    [(4.5, "爆款"), (3.8, "高"), (3.0, "中"), (2.0, "低"), (0.5, "差")],
)
def test_predict_bucket(raw_score, expected_bucket):
    assert predict_bucket(raw_score) == expected_bucket


def test_predict_bucket_out_of_range():
    with pytest.raises(ValueError):
        predict_bucket(5.5)
