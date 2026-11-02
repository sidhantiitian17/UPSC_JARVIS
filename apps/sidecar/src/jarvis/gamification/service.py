from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime

from jarvis.gamification.rules import DayStats, compute_progress

DEFAULT_GOAL = 60
DEFAULT_BAD_DAY_GOAL = 20


def _setting(conn: sqlite3.Connection, key: str):  # noqa: ANN202
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def load_days(conn: sqlite3.Connection) -> dict[date, DayStats]:
    minutes: dict[date, float] = defaultdict(float)
    xp: dict[date, int] = defaultdict(int)
    for r in conn.execute(
        "select g.finished_at, g.xp, s.focused_seconds from gate_result g "
        "join study_session s on s.id = g.session_id where g.passed = 1 and g.skipped = 0"
    ):
        d = datetime.fromisoformat(r["finished_at"]).astimezone().date()
        minutes[d] += r["focused_seconds"] / 60
        xp[d] += r["xp"]
    return {d: DayStats(minutes[d], xp[d]) for d in minutes}


def progress(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    today = (now or datetime.now(UTC)).astimezone().date()
    goal = int(_setting(conn, "daily_goal_minutes") or DEFAULT_GOAL)
    bad_goal = int(_setting(conn, "bad_day_goal_minutes") or DEFAULT_BAD_DAY_GOAL)
    bad_days = {date.fromisoformat(x) for x in (_setting(conn, "bad_days") or [])}
    out = compute_progress(load_days(conn), today, goal, bad_days, bad_goal)
    out["daily_goal_minutes"] = goal
    out["bad_day_goal_minutes"] = bad_goal
    return out
