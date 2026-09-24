from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import Anthropic

from ..config import ANTHROPIC_API_KEY, STANDARDS_DIR

_COMMUNITY_STANDARD_PATH = STANDARDS_DIR / "community_standard.md"


@dataclass
class SubredditCandidate:
    name: str
    fit_reason: str
    verified: bool  # 恒为 False,见下方说明


def suggest_communities(
    draft_title: str, draft_body: str, top_n: int = 5
) -> list[SubredditCandidate]:
    """
    完全基于 LLM 训练知识给候选社区排序,不做实时搜索/验证——"发现+验证全网
    社区是否真实存在"需要 Reddit 搜索接口,这条路目前被反爬拦着,只有官方 API
    审批下来才能补上(见 reddit_client.py 的说明)。

    在那之前,每个候选都标 verified=False:大社区(比如 r/CasualUK 这种量级)
    训练知识里的信息大概率没过期,但不保证,小众/新兴社区风险更高。使用方
    发布前打开对应页面看一眼是唯一现在就能做的验证方式,这一步不需要额外工具,
    因为发帖本来就要打开那个页面。
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")

    community_standard = _COMMUNITY_STANDARD_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""{community_standard}

# 草稿
title: {draft_title}
body:
{draft_body}

你现在没有实时搜索 Reddit 的能力,只能凭你训练知识里的了解给建议。选出最匹配
这篇草稿的 {top_n} 个真实 subreddit 名字,按匹配度降序排列。只推荐你比较确信
真实存在、活跃的社区,不确定的宁可少给。按 JSON 输出,只输出 JSON:
{{"suggested": [{{"name": "...", "fit_reason": "一句话"}}, ...]}}"""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    payload = json.loads(response.content[0].text)

    return [
        SubredditCandidate(name=item["name"], fit_reason=item["fit_reason"], verified=False)
        for item in payload["suggested"]
    ]
