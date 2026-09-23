from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import Anthropic

from ..config import ANTHROPIC_API_KEY, STANDARDS_DIR
from .rubric import QUALITY_DIMENSIONS, RiskGateResult, compute_raw_score, predict_bucket

_RUBRIC_NOTES_PATH = STANDARDS_DIR / "review_rubric.md"


@dataclass
class BlindScoreResult:
    scores: dict[str, float]
    raw_score: float
    predicted_bucket: str
    risk: RiskGateResult
    reasoning: dict[str, str]


def blind_score_draft(title: str, body: str, subreddit: str) -> BlindScoreResult:
    """
    对标 cheat-on-content 的 blind sub-agent 打分通道(channel B)。

    只能看到 title / body / subreddit 这三样,绝不能传入历史表现数据、账号历史、
    其他帖子的结果——这是"盲评"的核心约束。一旦打破,这个分数就不再是能和
    真实表现做独立对比的校准信号,只是又一次"AI自己觉得写得不错"。
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")

    rubric_notes = _RUBRIC_NOTES_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    dims = ", ".join(QUALITY_DIMENSIONS)
    prompt = f"""你是一个独立的内容评分器,只能依据下面的评分标准和草稿本身打分,
不能假设、不能推测任何发布后的表现数据,不知道这篇草稿最终有没有发布过。

# 评分标准
{rubric_notes}

# 待评草稿
subreddit: r/{subreddit}
title: {title}
body:
{body}

按 JSON 格式输出,只输出 JSON,不要多余文字:
{{
  "hook_strength": 0-5 浮点数, "hook_strength_reasoning": "一句话理由",
  ...(其余维度同样格式,键名用: {dims}),
  "risk_pass": true/false,
  "risk_reason": "若 risk_pass 为 false 必须给出具体理由,否则可为空字符串"
}}"""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    payload = json.loads(response.content[0].text)

    scores = {dim: float(payload[dim]) for dim in QUALITY_DIMENSIONS}
    raw_score = compute_raw_score(scores)

    return BlindScoreResult(
        scores=scores,
        raw_score=raw_score,
        predicted_bucket=predict_bucket(raw_score),
        risk=RiskGateResult(
            passed=bool(payload["risk_pass"]),
            reason=(payload.get("risk_reason") or None),
        ),
        reasoning={dim: payload.get(f"{dim}_reasoning", "") for dim in QUALITY_DIMENSIONS},
    )
