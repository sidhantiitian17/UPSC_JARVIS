"""FSRS (py-fsrs, MIT) cards, scheduling, the daily review queue and its subject interleaving."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime

from fsrs import Card, Rating, Scheduler

DEFAULT_DAILY_LIMIT = 40
_scheduler = Scheduler()


def _utc(now: datetime | None) -> datetime:
    return (now or datetime.now(UTC)).astimezone(UTC)


def _setting(conn: sqlite3.Connection, key: str):  # noqa: ANN202
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def daily_limit(conn: sqlite3.Connection) -> int:
    return int(_setting(conn, "review_daily_limit") or DEFAULT_DAILY_LIMIT)


def subject_for_session(conn: sqlite3.Connection, session_id: int) -> str:
    """Subject used to interleave cards: the 'subject' ancestor of the session's first tag (else the tag)."""
    tag = conn.execute(
        "select dst_id from link where src_type='session' and src_id=? and dst_type='node' and kind='tag' "
        "order by rowid limit 1",
        (str(session_id),),
    ).fetchone()
    if tag is None:
        return "unknown"
    node_id: str | None = tag["dst_id"]
    seen = set()
    while node_id and node_id not in seen:
        seen.add(node_id)
        n = conn.execute("select id, parent_id, kind from syllabus_node where id = ?", (node_id,)).fetchone()
        if n is None:
            break
        if n["kind"] == "subject":
            return n["id"]
        node_id = n["parent_id"]
    return tag["dst_id"]


def create_or_lapse_card(
    conn: sqlite3.Connection, question_id: int, subject_id: str | None, now: datetime | None = None
) -> int:
    """A wrong answer: create the card (first FSRS review = Again) or lapse the existing one."""
    at = _utc(now)
    row = conn.execute("select * from card where question_id = ?", (question_id,)).fetchone()
    if row is None:
        card, _ = _scheduler.review_card(Card(), Rating.Again, at)
        cur = conn.execute(
            "insert into card(question_id,due,state_json,created_at,subject_id) values (?,?,?,?,?)",
            (question_id, card.due.isoformat(), json.dumps(card.to_dict()), at.isoformat(), subject_id),
        )
        return cur.lastrowid
    before = row["state_json"]
    card, _ = _scheduler.review_card(Card.from_dict(json.loads(before)), Rating.Again, at)
    conn.execute(
        "update card set due = ?, state_json = ?, suspended = 0 where id = ?",
        (card.due.isoformat(), json.dumps(card.to_dict()), row["id"]),
    )
    conn.execute(
        "insert into review_log(card_id,rating,reviewed_at,scheduled_days,state_before_json) "
        "values (?,?,?,?,?)",
        (row["id"], 1, at.isoformat(), (card.due - at).total_seconds() / 86400, before),
    )
    return row["id"]


def rate_card(conn: sqlite3.Connection, card_id: int, rating: int, now: datetime | None = None) -> dict:
    if rating not in (1, 2, 3, 4):
        raise ValueError("rating must be 1 (Again), 2 (Hard), 3 (Good) or 4 (Easy)")
    row = conn.execute("select * from card where id = ?", (card_id,)).fetchone()
    if row is None:
        raise KeyError(card_id)
    at = _utc(now)
    card, _ = _scheduler.review_card(Card.from_dict(json.loads(row["state_json"])), Rating(rating), at)
    days = (card.due - at).total_seconds() / 86400
    conn.execute(
        "update card set due = ?, state_json = ? where id = ?",
        (card.due.isoformat(), json.dumps(card.to_dict()), card_id),
    )
    conn.execute(
        "insert into review_log(card_id,rating,reviewed_at,scheduled_days,state_before_json) "
        "values (?,?,?,?,?)",
        (card_id, rating, at.isoformat(), days, row["state_json"]),
    )
    return {"card_id": card_id, "due": card.due.isoformat(), "interval_days": round(days, 3)}


def _day_start(at: datetime) -> datetime:
    return at.astimezone().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)


def reviewed_today(conn: sqlite3.Connection, at: datetime) -> int:
    return conn.execute(
        "select count(distinct card_id) from review_log where reviewed_at >= ?", (_day_start(at).isoformat(),)
    ).fetchone()[0]


def _due_rows(conn: sqlite3.Connection, at: datetime) -> list[sqlite3.Row]:
    return conn.execute(
        "select c.id as card_id, c.question_id, c.due, c.subject_id, q.stem, q.options_json, q.answer_index, "
        "q.explanation, q.source_quote from card c join question q on q.id = c.question_id "
        "where c.suspended = 0 and q.status = 'active' and c.due <= ? order by c.due, c.id",
        (at.isoformat(),),
    ).fetchall()


def _interleave(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    """Oldest-due first, but never the same subject more than twice in a row while others remain."""
    buckets: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        buckets[r["subject_id"] or "unknown"].append(r)
    out: list[sqlite3.Row] = []
    while any(buckets.values()):
        banned = None
        if len(out) >= 2 and (out[-1]["subject_id"] or "unknown") == (out[-2]["subject_id"] or "unknown"):
            banned = out[-1]["subject_id"] or "unknown"
        options = [(b[0]["due"], s) for s, b in buckets.items() if b and s != banned]
        if not options:  # only the banned subject is left
            options = [(b[0]["due"], s) for s, b in buckets.items() if b]
        _, subject = min(options)
        out.append(buckets[subject].pop(0))
    return out


def queue(conn: sqlite3.Connection, now: datetime | None = None) -> list[dict]:
    at = _utc(now)
    allowance = max(0, daily_limit(conn) - reviewed_today(conn, at))
    rows = _interleave(_due_rows(conn, at)[:allowance])
    return [
        {
            "card_id": r["card_id"],
            "question_id": r["question_id"],
            "subject": r["subject_id"] or "unknown",
            "due": r["due"],
            "stem": r["stem"],
            "options": json.loads(r["options_json"]),
            "answer_index": r["answer_index"],
            "explanation": r["explanation"] or "",
            "source_quote": r["source_quote"] or "",
        }
        for r in rows
    ]


def stats(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    at = _utc(now)
    limit = daily_limit(conn)
    done = reviewed_today(conn, at)
    return {
        "due_now": len(_due_rows(conn, at)),
        "daily_limit": limit,
        "reviewed_today": done,
        "remaining_today": max(0, limit - done),
        "total_cards": conn.execute("select count(*) from card").fetchone()[0],
    }
