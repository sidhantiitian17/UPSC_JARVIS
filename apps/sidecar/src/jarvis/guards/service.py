from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime, time

from jarvis.guards.rules import burnout_status, in_sleep_window, minutes_until_end

DEFAULT_SLEEP_START = "23:30"
DEFAULT_SLEEP_END = "05:30"
MAX_BAD_DAYS = 400

SLEEP_TEXT = "It is late. Sleep is when memory sticks, so stopping now is a good study decision."
BURNOUT_TEXT = (
    "You have studied a very long day. Rest is part of the plan. A walk or an early night will help tomorrow."
)
HEAVY_TEXT = "Several long days in a row. Consider a lighter day soon to keep your energy steady."
BAD_DAY_TEXT = "Bad-day mode keeps your streak safe with a smaller goal. Showing up a little still counts."
SUPPORTIVE_TEXTS = [SLEEP_TEXT, BURNOUT_TEXT, HEAVY_TEXT, BAD_DAY_TEXT]


def _setting(conn: sqlite3.Connection, key: str):  # noqa: ANN202
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def _hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


def sleep_config(conn: sqlite3.Connection) -> dict:
    enabled = _setting(conn, "sleep_guard_enabled")
    return {
        "enabled": True if enabled is None else bool(enabled),
        "start": _setting(conn, "sleep_start") or DEFAULT_SLEEP_START,
        "end": _setting(conn, "sleep_end") or DEFAULT_SLEEP_END,
    }


def _local(now: datetime | None) -> datetime:
    return (now or datetime.now(UTC)).astimezone()


def _hours_by_day(conn: sqlite3.Connection) -> dict[date, float]:
    out: dict[date, float] = defaultdict(float)
    for r in conn.execute("select coalesce(ended_at, started_at) as at, focused_seconds from study_session"):
        out[datetime.fromisoformat(r["at"]).astimezone().date()] += r["focused_seconds"] / 3600
    return out


def _bad_days(conn: sqlite3.Connection) -> list[str]:
    return list(_setting(conn, "bad_days") or [])


def status(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    at = _local(now)
    cfg = sleep_config(conn)
    inside = cfg["enabled"] and in_sleep_window(at.time(), _hhmm(cfg["start"]), _hhmm(cfg["end"]))
    burn = burnout_status(_hours_by_day(conn), at.date())
    messages: list[str] = []
    if inside:
        messages.append(SLEEP_TEXT)
    if burn["warning"]:
        messages.append(BURNOUT_TEXT)
    elif burn["heavy_stretch"]:
        messages.append(HEAVY_TEXT)
    return {
        "sleep": {
            **cfg,
            "active": bool(inside),
            "minutes_until_end": minutes_until_end(at.time(), _hhmm(cfg["end"])) if inside else None,
        },
        "burnout": burn,
        "bad_day": {"today_active": at.date().isoformat() in _bad_days(conn), "note": BAD_DAY_TEXT},
        "messages": messages,
    }


def set_bad_day(conn: sqlite3.Connection, active: bool, now: datetime | None = None) -> dict:
    """Only today can be switched; earlier days stay as they were."""
    at = _local(now)
    today = at.date().isoformat()
    days = [d for d in _bad_days(conn) if d != today]
    if active:
        days.append(today)
    conn.execute(
        "insert into setting(key,value_json) values ('bad_days',?) "
        "on conflict(key) do update set value_json = excluded.value_json",
        (json.dumps(sorted(days)[-MAX_BAD_DAYS:]),),
    )
    return status(conn, now)
