from __future__ import annotations

import datetime as dt
import json

from ..config import RULES_CACHE_TTL_HOURS
from ..db.models import Subreddit
from ..db.session import get_session
from ..reddit_client import get_client


def fetch_rules(subreddit_name: str, force: bool = False) -> dict:
    """
    结构化规则(/about/rules.json)+ 侧边栏原文(/about.json 的 description)。
    不维护一份长期规则库——每次真正要用的时候现查(带 TTL 缓存),这样版主
    改了规则也不会用到过期信息,不需要额外开一个"规则库维护"任务。
    """
    session = get_session()
    row = session.get(Subreddit, subreddit_name)

    if (
        not force
        and row
        and row.rules_fetched_at
        and dt.datetime.utcnow() - row.rules_fetched_at < dt.timedelta(hours=RULES_CACHE_TTL_HOURS)
    ):
        return json.loads(row.rules_json)

    reddit = get_client()
    sub = reddit.subreddit(subreddit_name)
    payload = {
        "structured_rules": [
            {
                "short_name": r.short_name,
                "description": r.description,
                "violation_reason": r.violation_reason,
            }
            for r in sub.rules
        ],
        "sidebar_description": sub.description,
        "submission_type": sub.submission_type,  # "any" | "link" | "self"
        "over18": sub.over18,
        "subscribers": sub.subscribers,
    }

    if row is None:
        row = Subreddit(name=subreddit_name)
        session.add(row)
    row.rules_json = json.dumps(payload, ensure_ascii=False)
    row.rules_fetched_at = dt.datetime.utcnow()
    row.allows_image_post = payload["submission_type"] in ("any", "link")
    session.commit()

    return payload
