from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import Anthropic

from ..config import ANTHROPIC_API_KEY, STANDARDS_DIR
from ..reddit_client import get_client
from .rules import fetch_rules

_COMMUNITY_STANDARD_PATH = STANDARDS_DIR / "community_standard.md"


@dataclass
class SubredditCandidate:
    name: str
    fit_reason: str
    required_actions: list[str]


def discover_candidates(theme_keywords: list[str], limit_per_keyword: int = 15) -> list[str]:
    """
    用 Reddit 官方搜索接口按关键词发现候选社区,不依赖静态白名单。
    返回的每一个名字都是真实存在的 subreddit —— 这一步本身就是"防幻觉"验证。
    """
    reddit = get_client()
    seen: set[str] = set()
    for kw in theme_keywords:
        for sub in reddit.subreddits.search(kw, limit=limit_per_keyword):
            seen.add(sub.display_name)
    return sorted(seen)


def rank_candidates(
    candidate_names: list[str], draft_title: str, draft_body: str, top_n: int = 5
) -> list[SubredditCandidate]:
    """
    按 standards/community_standard.md 对候选社区排序,选 top_n,只给一句话理由。
    再对入选的每一个现查规则,只有真正"必须做的动作"(强制 flair / 强制标题格式)
    才写进 required_actions —— 从自由文本规则里稳健地抽取"是否强制"这件事,
    比结构化字段本身更难,先做成显式 TODO,留到规则误判率有真实数据后再细化,
    不在骨架阶段假装已经解决。
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")
    if not candidate_names:
        return []

    community_standard = _COMMUNITY_STANDARD_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""{community_standard}

# 草稿
title: {draft_title}
body:
{draft_body}

# 候选社区(必须只从这个列表里选,不能编造)
{", ".join(candidate_names)}

从候选里选出最匹配的 {top_n} 个,按匹配度降序排列。按 JSON 输出,只输出 JSON:
{{"ranked": [{{"name": "...", "fit_reason": "一句话"}}, ...]}}"""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    payload = json.loads(response.content[0].text)

    ranked = [
        SubredditCandidate(name=item["name"], fit_reason=item["fit_reason"], required_actions=[])
        for item in payload["ranked"]
    ]

    for candidate in ranked:
        fetch_rules(candidate.name)  # 预热缓存,供后续人工确认前查看
        # TODO(phase 2): 从 structured_rules + sidebar_description 里稳健抽取
        # "强制 flair / 强制标题格式" 写入 candidate.required_actions

    return ranked
