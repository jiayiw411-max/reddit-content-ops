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


def draft_post(image_description: str) -> DraftResult:
    """
    按 standards/writing_standard.md 生成标题+正文。改文案规则改那份文件,
    不用改这里的代码。

    流程顺序是 选图 → 撰写 → 选社区,写这一步时还不知道要发哪个社区,所以
    不接受 subreddit 参数——"社区联动"的那条规则(比如 r/food 要求正文带
    tips)在选定社区之后,由使用方决定要不要针对那个社区再润色一版,不在
    这一步里强求。
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")

    writing_standard = _WRITING_STANDARD_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""{writing_standard}

# 图片描述
{image_description}

这一步还没选定发布社区,先按通用标准写,不用假设任何特定社区的规则。

按 JSON 输出,只输出 JSON,不要多余文字:
{{"title": "...", "body": "..."}}"""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    payload = json.loads(response.content[0].text)
    return DraftResult(title=payload["title"], body=payload["body"])
