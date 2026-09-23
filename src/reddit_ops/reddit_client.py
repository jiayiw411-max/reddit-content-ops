from __future__ import annotations

import praw

from .config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_PASSWORD,
    REDDIT_USER_AGENT,
    REDDIT_USERNAME,
)

_reddit: praw.Reddit | None = None


def get_client() -> praw.Reddit:
    """
    共享的只读 PRAW 客户端。注册一个 reddit.com/prefs/apps 上的 "script" 类型
    应用即可获得 client_id/secret —— 这是 Reddit 官方允许的个人开发者用法,
    不是抓取。带上规范的 User-Agent 是不被限流/拦截的关键。

    我们只做只读(社区规则、帖子表现数据都是公开信息,读谁的帖子都不需要
    "登录成那个账号"),所以用户名/密码是可选的:填了就走密码授权,
    不填就自动走 app-only 只读授权,两种都能读公开数据,没必要把账号密码
    放进 .env。
    """
    global _reddit
    if _reddit is None:
        missing = [
            name
            for name, val in [
                ("REDDIT_CLIENT_ID", REDDIT_CLIENT_ID),
                ("REDDIT_CLIENT_SECRET", REDDIT_CLIENT_SECRET),
            ]
            if not val
        ]
        if missing:
            raise RuntimeError(f"missing reddit credentials: {missing} — see .env.example")

        kwargs: dict[str, str] = {
            "client_id": REDDIT_CLIENT_ID,
            "client_secret": REDDIT_CLIENT_SECRET,
            "user_agent": REDDIT_USER_AGENT,
        }
        if REDDIT_USERNAME and REDDIT_PASSWORD:
            kwargs["username"] = REDDIT_USERNAME
            kwargs["password"] = REDDIT_PASSWORD

        _reddit = praw.Reddit(**kwargs)
    return _reddit
