"""PYQ weightage per subject and the Direction Drift Alert (specs/pyq-trends.feature)."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import UTC, datetime, timedelta

MIN_TAGGED = 30
MIN_VERIFIED_MINUTES = 120
WINDOW_DAYS = 28
UNDER_SERVED_MIN_WEIGHT = 15
HEAVY_MIN_TIME = 40
HEAVY_MAX_WEIGHT = 10

NOT_ENOUGH = (
    "Not enough data yet. Tag at least 30 PYQs and verify about 2 hours of study to see where your time "
    "and the exam's weightage differ."
)


def subject_of_node(conn: sqlite3.Connection, node_id: str) -> tuple[str, str] | None:
    """(subject id, title): the nearest 'subject' ancestor, or the node itself when there is none."""
    seen: set[str] = set()
    cur: str | None = node_id
    first: sqlite3.Row | None = None
    while cur and cur not in seen:
        seen.add(cur)
        n = conn.execute(
            "select id, parent_id, kind, title from syllabus_node where id = ?", (cur,)
        ).fetchone()
        if n is None:
            return None
        first = first or n
        if n["kind"] == "subject":
            return n["id"], n["title"]
        cur = n["parent_id"]
    return (first["id"], first["title"]) if first else None


def trends(conn: sqlite3.Connection) -> dict:
    per_q: dict[str, tuple[int, list[str]]] = {}
    for r in conn.execute(
        "select p.id, p.year, t.node_id from pyq_tag t join pyq p on p.id = t.pyq_id "
        "where t.status = 'accepted' order by p.id, t.rowid"
    ):
        per_q.setdefault(r["id"], (r["year"], []))[1].append(r["node_id"])

    subjects: dict[str, dict] = {}
    years: set[int] = set()
    for year, nodes in per_q.values():
        weight = 1 / len(nodes)
        years.add(year)
        for node_id in nodes:
            sub = subject_of_node(conn, node_id)
            if sub is None:
                continue
            s = subjects.setdefault(
                sub[0], {"id": sub[0], "title": sub[1], "counts_by_year": {}, "total": 0.0}
            )
            s["counts_by_year"][str(year)] = s["counts_by_year"].get(str(year), 0.0) + weight
            s["total"] += weight
    grand = sum(s["total"] for s in subjects.values())
    out = []
    for s in sorted(subjects.values(), key=lambda s: (-s["total"], s["id"])):
        out.append(
            {
                "id": s["id"],
                "title": s["title"],
                "counts_by_year": {y: round(v, 2) for y, v in sorted(s["counts_by_year"].items())},
                "total": round(s["total"], 2),
                "share_pct": round(100 * s["total"] / grand) if grand else 0,
            }
        )
    with_text = conn.execute("select count(*) from pyq where trim(stem) != ''").fetchone()[0]
    return {
        "years": sorted(years),
        "subjects": out,
        "tagged_questions": len(per_q),
        "questions_with_text": with_text,
        "tagged_pct": round(100 * len(per_q) / with_text) if with_text else None,
    }


def _time_by_subject(conn: sqlite3.Connection, now: datetime) -> dict[str, float]:
    since = (now.astimezone(UTC) - timedelta(days=WINDOW_DAYS)).isoformat()
    tags: dict[int, list[str]] = defaultdict(list)
    for r in conn.execute(
        "select src_id, dst_id from link where src_type='session' and dst_type='node' and kind='tag'"
    ):
        tags[int(r["src_id"])].append(r["dst_id"])
    minutes: dict[str, float] = defaultdict(float)
    for r in conn.execute(
        "select s.id, s.focused_seconds from gate_result g join study_session s on s.id = g.session_id "
        "where g.passed = 1 and g.skipped = 0 and g.finished_at >= ?",
        (since,),
    ):
        subs = {sub[0] for n in tags.get(r["id"], []) if (sub := subject_of_node(conn, n))}
        for sid in subs:
            minutes[sid] += r["focused_seconds"] / 60 / len(subs)
    return dict(minutes)


def drift(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    at = now or datetime.now(UTC)
    t = trends(conn)
    time = _time_by_subject(conn, at)
    total_time = sum(time.values())
    enough = t["tagged_questions"] >= MIN_TAGGED and total_time >= MIN_VERIFIED_MINUTES

    titles = {s["id"]: s["title"] for s in t["subjects"]}
    weights = {s["id"]: s["share_pct"] for s in t["subjects"]}
    for sid in time:
        if sid not in titles:
            row = conn.execute("select title from syllabus_node where id = ?", (sid,)).fetchone()
            titles[sid] = row["title"] if row else sid
    rows = []
    for sid in sorted(titles, key=lambda s: (-weights.get(s, 0), s)):
        rows.append(
            {
                "subject_id": sid,
                "title": titles[sid],
                "weight_share_pct": weights.get(sid, 0),
                "time_share_pct": round(100 * time.get(sid, 0) / total_time) if total_time else 0,
                "verified_minutes": round(time.get(sid, 0)),
            }
        )
    alerts = []
    if enough:
        for r in rows:
            w, ts = r["weight_share_pct"], r["time_share_pct"]
            if w >= UNDER_SERVED_MIN_WEIGHT and ts < w / 2:
                alerts.append(
                    {
                        "subject_id": r["subject_id"],
                        "kind": "under_served",
                        "weight_share_pct": w,
                        "time_share_pct": ts,
                        "text": (
                            f"{r['title']} makes up {w}% of tagged PYQs but only {ts}% of your verified time "
                            "in the last 4 weeks. Try giving one of your next focus blocks to it."
                        ),
                    }
                )
            elif ts >= HEAVY_MIN_TIME and w < HEAVY_MAX_WEIGHT:
                alerts.append(
                    {
                        "subject_id": r["subject_id"],
                        "kind": "heavily_studied",
                        "weight_share_pct": w,
                        "time_share_pct": ts,
                        "text": (
                            f"{r['title']} took {ts}% of your verified time but is {w}% of tagged PYQs. "
                            "Keep going if you enjoy it; the next block could go to a higher-weight subject."
                        ),
                    }
                )
    return {
        "enough_data": enough,
        "message": (
            ("Your verified time and the exam's weightage are compared over the last 4 weeks.")
            if enough
            else NOT_ENOUGH
        ),
        "alerts": alerts,
        "rows": rows,
    }
