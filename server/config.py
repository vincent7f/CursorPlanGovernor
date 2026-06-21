from __future__ import annotations

import os

DEFAULT_DB_URL = "sqlite:///./plan_governor.db"


def get_db_url() -> str:
    return os.environ.get("PLAN_GOVERNOR_DB_URL", DEFAULT_DB_URL)
