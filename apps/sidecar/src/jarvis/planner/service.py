"""Daily planner v1 and the commitment contract (specs/planner.feature). Rules only: no LLM involved."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from jarvis.gamification.service import load_days
from jarvis.review.fsrs_service import stats as review_stats
from jarvis.review.fsrs_service import subject_for_session

MIN_STUDY_BLOCK = 25
CATCH_UP_MINUTES = 15
CATCH_UP_THRESHOLD = 0.7
REVIEW_MIN, REVIEW_MAX_SHARE, REVIEW_CAP = 10, 0.25, 40
STARTERS = [
    "pre.polity",
    "pre.history",
    "pre.economy",
    "pre.geography",
    "pre.environment",
    "pre.science",
    "pre.current",
]
CATCH_UP_NOTE = (
    "Yesterday's plan was only partly verified. A short catch-up recall gate comes first. "
    "No penalty, just a gentle reset."
)


def _setting(conn: sqlite3.Connection, key: str):  # noqa: ANN202
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def _local(now: datetime | None) -> datetime:
    return (now or datetime.now(UTC)).astimezone()


def _subject_titles(conn: sqlite3.Connection) -> dict[str, str]:
    return {
        r["id"]: r["title"]
        for r in conn.execute("select id, title from syllabus_node where kind = 'subject'")
    }


def weak_subjects(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """[(subject_id, recall %)] lowest recall first, from every answered gate question."""
    total: dict[str, int] = defaultdict(int)
    right: dict[str, int] = defaultdict(int)
    for r in conn.execute(
        "select session_id, count(*) as n, sum(correct) as ok from attempt group by session_id"
    ):
        if r["session_id"] is None:
            continue
        subject = subject_for_session(conn, r["session_id"])
        total[subject] += r["n"]
        right[subject] += r["ok"]
    ranked = sorted(
        ((s, round(100 * right[s] / total[s])) for s in total if total[s] > 0), key=lambda x: (x[1], x[0])
    )
    return ranked


def _starters(conn: sqlite3.Connection, titles: dict[str, str]) -> list[str]:
    present = [s for s in STARTERS if s in titles]
    return present or list(titles)[:3]


def yesterday_status(conn: sqlite3.Connection, now: datetime | None) -> dict | None:
    at = _local(now)
    y = (at - timedelta(days=1)).date()
    committed = _setting(conn, f"plan:{y.isoformat()}")
    if not committed or not committed.get("study_minutes"):
        return None
    verified = round(load_days(conn).get(y).minutes) if y in load_days(conn) else 0
    mins = int(committed["study_minutes"])
    return {
        "committed_minutes": mins,
        "verified_minutes": verified,
        "missed": verified < CATCH_UP_THRESHOLD * mins,
    }


def build_plan(conn: sqlite3.Connection, free_hours: float, now: datetime | None = None) -> dict:
    free = int(free_hours * 60)
    focus = int(_setting(conn, "focus_minutes") or 50)
    rest = int(_setting(conn, "break_minutes") or 10)
    titles = _subject_titles(conn)
    blocks: list[dict] = []
    notes: list[str] = []
    used = 0

    yday = yesterday_status(conn, now)
    catch_up = bool(yday and yday["missed"]) and free >= 3 * MIN_STUDY_BLOCK
    if catch_up:
        blocks.append(
            {"kind": "catch_up", "subject_id": None, "subject": None, "minutes": CATCH_UP_MINUTES,
             "reason": "catch-up recall gate for yesterday's plan"}
        )  # fmt: skip
        used += CATCH_UP_MINUTES
        notes.append(CATCH_UP_NOTE)

    stats = review_stats(conn, (now or datetime.now(UTC)).astimezone(UTC))
    due = min(stats["due_now"], stats["remaining_today"])
    cap = min(REVIEW_CAP, int(REVIEW_MAX_SHARE * free))
    if due > 0 and cap >= REVIEW_MIN:
        minutes = max(REVIEW_MIN, min(due, cap))
        blocks.append(
            {"kind": "review", "subject_id": None, "subject": None, "minutes": minutes,
             "reason": f"{due} cards due"}
        )  # fmt: skip
        used += minutes

    weak = weak_subjects(conn)
    picks: list[tuple[str, str]] = [(s, f"weakest area: {pct}% recall") for s, pct in weak[:3]]
    for s in _starters(conn, titles):
        if len(picks) >= 3:
            break
        if all(s != p[0] for p in picks):
            picks.append((s, "starter subject for Prelims"))

    i = 0
    remaining = free - used
    while remaining >= MIN_STUDY_BLOCK and picks:
        minutes = min(focus, remaining)
        sid, reason = picks[i % len(picks)]
        blocks.append(
            {
                "kind": "study",
                "subject_id": sid,
                "subject": titles.get(sid, sid),
                "minutes": minutes,
                "reason": reason,
            }
        )
        i += 1
        remaining -= minutes
        if remaining - rest >= MIN_STUDY_BLOCK:
            blocks.append(
                {"kind": "break", "subject_id": None, "subject": None, "minutes": rest, "reason": "rest"}
            )
            remaining -= rest
    planned = sum(b["minutes"] for b in blocks)
    return {
        "free_minutes": free,
        "planned_minutes": planned,
        "blocks": blocks,
        "catch_up": catch_up,
        "notes": notes,
    }


def commit_plan(conn: sqlite3.Connection, plan: dict, now: datetime | None = None) -> dict:
    day = _local(now).date().isoformat()
    record = {
        "free_minutes": plan["free_minutes"],
        "study_minutes": sum(b["minutes"] for b in plan["blocks"] if b["kind"] == "study"),
        "blocks": plan["blocks"],
    }
    conn.execute(
        "insert into setting(key,value_json) values (?,?) "
        "on conflict(key) do update set value_json = excluded.value_json",
        (f"plan:{day}", json.dumps(record)),
    )
    return record


def planner_status(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    day = _local(now).date().isoformat()
    yday = yesterday_status(conn, now)
    return {
        "committed_today": _setting(conn, f"plan:{day}"),
        "yesterday": yday,
        "catch_up_due": bool(yday and yday["missed"]),
    }
