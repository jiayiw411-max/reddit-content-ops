from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
STANDARDS_DIR = ROOT_DIR / "standards"

REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "python:reddit-content-ops:0.1 (by /u/PLACEHOLDER)")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

RULES_CACHE_TTL_HOURS = int(os.getenv("RULES_CACHE_TTL_HOURS", "24"))
