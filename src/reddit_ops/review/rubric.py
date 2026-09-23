from __future__ import annotations

from dataclasses import dataclass

# 必须和 standards/review_rubric.md 保持一致 —— 那份文件是给 blind sub-agent 看的
# prompt 源,这里是代码里算分用的定义,两边对不上会导致盲评分数和本地校准逻辑脱节。
QUALITY_DIMENSIONS: dict[str, str] = {
    "hook_strength": "标题第一眼抓人的程度(强情绪或悬念反差),越具体越高分",
    "specificity": "是否有可验证的具体细节(价格/地点/时间),而非空泛描述",
    "community_fit": "内容是否精准踩中目标 subreddit 的惯例与口味",
    "emotional_sharpness": "是否有明确态度或情绪,而非中立陈述",
    "image_text_cohesion": "图片与文案的呼应程度,图片本身的话题性",
    "discussion_openness": "结尾是否自然邀请互动,而非强推 CTA",
}

# v0 占位边界,未校准。满 5 篇真实表现数据后重新拟合。
BUCKET_BOUNDARIES: list[tuple[str, float, float]] = [
    ("爆款", 4.3, 5.0),
    ("高", 3.5, 4.2),
    ("中", 2.5, 3.4),
    ("低", 1.5, 2.4),
    ("差", 0.0, 1.4),
]


@dataclass
class RiskGateResult:
    """
    风险/合规是独立于质量维度的 pass/fail 判定,不参与 raw_score 平均。
    "文案好但踩了社区红线"不该被其他维度的高分稀释成及格分。
    """

    passed: bool
    reason: str | None = None


def compute_raw_score(scores: dict[str, float]) -> float:
    missing = set(QUALITY_DIMENSIONS) - set(scores)
    if missing:
        raise ValueError(f"missing scores for dimensions: {sorted(missing)}")
    return sum(scores[d] for d in QUALITY_DIMENSIONS) / len(QUALITY_DIMENSIONS)


def predict_bucket(raw_score: float) -> str:
    for bucket, low, high in BUCKET_BOUNDARIES:
        if low <= raw_score <= high:
            return bucket
    raise ValueError(f"raw_score {raw_score} out of range [0, 5]")
