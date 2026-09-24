from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from anthropic import Anthropic

from ..config import ANTHROPIC_API_KEY, STANDARDS_DIR
from ..images import read_image_bytes

_WRITING_STANDARD_PATH = STANDARDS_DIR / "writing_standard.md"


@dataclass
class DraftResult:
    title: str
    body: str


def draft_post(image_path: str, extra_context: str = "") -> DraftResult:
    """
    按 standards/writing_standard.md 生成标题+正文。直接读图片本身(多模态),
    不是靠人手打一段文字描述再转述给模型——细节、氛围这些东西让模型自己看,
    比你转述更准。extra_context 是可选的补充信息(比如价格、地点这些照片里
    看不出来的事实)。

    流程顺序是 选图 → 撰写 → 选社区,写这一步时还不知道要发哪个社区,所以
    不接受 subreddit 参数——"社区联动"的那条规则(比如 r/food 要求正文带
    tips)在选定社区之后,由使用方决定要不要针对那个社区再润色一版。
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")

    image_bytes, media_type = read_image_bytes(image_path)
    image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    writing_standard = _WRITING_STANDARD_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    context_line = f"\n补充信息(照片里看不出来的事实,比如价格/地点): {extra_context}" if extra_context else ""

    text_prompt = f"""{writing_standard}

看图片本身写标题和正文,细节要从图片里来,不要泛泛而写。{context_line}

这一步还没选定发布社区,先按通用标准写,不用假设任何特定社区的规则。

按 JSON 输出,只输出 JSON,不要多余文字:
{{"title": "...", "body": "..."}}"""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                    },
                    {"type": "text", "text": text_prompt},
                ],
            }
        ],
    )
    payload = json.loads(response.content[0].text)
    return DraftResult(title=payload["title"], body=payload["body"])
