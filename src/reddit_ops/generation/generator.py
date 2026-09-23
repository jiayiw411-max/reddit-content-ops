from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import Anthropic

from ..config import ANTHROPIC_API_KEY, STANDARDS_DIR

_WRITING_STANDARD_PATH = STANDARDS_DIR / "writing_standard.md"


@dataclass
class DraftResult:
    title: str
    body: str


def draft_post(image_description: str, subreddit: str, community_notes: str = "") -> DraftResult:
    """
    按 standards/writing_standard.md 生成标题+正文。改文案规则改那份文件,
    不用改这里的代码。
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")

    writing_standard = _WRITING_STANDARD_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""{writing_standard}

# 图片描述
{image_description}

# 目标社区
r/{subreddit}
{community_notes}

按 JSON 输出,只输出 JSON,不要多余文字:
{{"title": "...", "body": "..."}}"""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    payload = json.loads(response.content[0].text)
    return DraftResult(title=payload["title"], body=payload["body"])
