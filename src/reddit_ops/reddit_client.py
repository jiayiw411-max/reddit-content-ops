from __future__ import annotations

import time

import requests

from .config import REDDIT_USER_AGENT

BASE_URL = "https://www.reddit.com"

# Reddit 在 2025-11-11 关闭了个人开发者自助注册 OAuth 应用的入口(Responsible
# Builder Policy),script app 现在卡在 reCAPTCHA 循环、走不通,不是配置问题。
# 我们要读的都是公开数据(子版规则、帖子分数/评论数),公开只读 .json 接口
# 不受这次收紧影响,不需要注册应用、不需要 client_id/secret。
# 未认证访问限速更紧(约 10 req/min),所以这里做了个简单节流。
_MIN_INTERVAL_SECONDS = 6.0  # ~10 req/min 留出余量
_last_request_at: float = 0.0


def get_json(path: str, params: dict | None = None) -> dict:
    """
    直接调 Reddit 公开只读 .json 接口,例如 get_json("/r/CasualUK/about") 或
    get_json("/comments/abc123")。path 不带 .json 后缀,这里统一拼接。
    """
    global _last_request_at

    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)

    url = f"{BASE_URL}{path}.json"
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": REDDIT_USER_AGENT},
        timeout=10,
    )
    _last_request_at = time.monotonic()
    response.raise_for_status()
    return response.json()
