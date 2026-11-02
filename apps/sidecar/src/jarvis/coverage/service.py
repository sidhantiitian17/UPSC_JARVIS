"""Honest coverage: only pages that were read AND remembered (passed gate) count, weighted by retention."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from jarvis.review.fsrs_service import stats as review_stats

HEATMAP_DAYS = 84
WEEK_DAYS = 7


def _verified_by_node(conn: sqlite3.Connection) -> tuple[dict[str, float], dict[str, int]]:
    """Per node: verified pages (each (document, page) once, at its best retention) and session count."""
    sessions = conn.execute(
        "select s.id, s.document_id, cs.page as first_page, ce.page as last_page, r.retention_pct "
        "from study_session s join gate_result r on r.session_id = s.id "
        "join chunk cs on cs.id = s.start_chunk_id join chunk ce on ce.id = s.end_chunk_id "
        "where r.passed = 1 and r.skipped = 0 and s.status = 'done'"
    ).fetchall()
    tags: dict[int, list[str]] = defaultdict(list)
    for r in conn.execute(
        "select src_id, dst_id from link where src_type='session' and dst_type='node' and kind='tag'"
    ):
        tags[int(r["src_id"])].append(r["dst_id"])

    pages: dict[str, dict[tuple[int, int], int]] = defaultdict(dict)
    counts: dict[str, int] = defaultdict(int)
    for s in sessions:
        for node_id in tags.get(s["id"], []):
            counts[node_id] += 1
            best = pages[node_id]
            for page in range(s["first_page"], s["last_page"] + 1):
                key = (s["document_id"], page)
                best[key] = max(best.get(key, 0), s["retention_pct"])
    verified = {n: sum(w) / 100 for n, w in ((n, pg.values()) for n, pg in pages.items())}
    return verified, dict(counts)


def coverage_nodes(conn: sqlite3.Connection) -> list[dict]:
    rows = [
        dict(r)
        for r in conn.execute("select id,parent_id,title,kind,target_pages from syllabus_node order by rowid")
    ]
    verified, counts = _verified_by_node(conn)
    children: dict[str | None, list[dict]] = defaultdict(list)
    for r in rows:
        children[r["parent_id"]].append(r)

    out: dict[str, dict] = {}

    def roll(node: dict) -> tuple[float, float, float, int]:
        """(verified pages, capped numerator, denominator, sessions) for the node and its descendants."""
        own_v = verified.get(node["id"], 0.0)
        own_t = node["target_pages"] or 0
        v, num, den, n = own_v, (min(own_v, own_t) if own_t else 0.0), float(own_t), counts.get(node["id"], 0)
        for child in children.get(node["id"], []):
            cv, cnum, cden, cn = roll(child)
            v, num, den, n = v + cv, num + cnum, den + cden, n + cn
        out[node["id"]] = {
            "id": node["id"],
            "parent_id": node["parent_id"],
            "title": node["title"],
            "kind": node["kind"],
            "verified_pages": round(v, 2),
            "target_pages": int(den) if den else None,
            "percent": min(100, round(100 * num / den)) if den else None,
            "sessions": n,
        }
        return v, num, den, n

    for root in children.get(None, []):
        roll(root)
    return [out[r["id"]] for r in rows if r["id"] in out]


def _local_date(iso: str) -> date:
    return datetime.fromisoformat(iso).astimezone().date()


def dashboard_today(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    at = (now or datetime.now(UTC)).astimezone(UTC)
    today = at.astimezone().date()
    minutes_by_day: dict[date, float] = defaultdict(float)
    for r in conn.execute(
        "select r.finished_at, s.focused_seconds from gate_result r "
        "join study_session s on s.id = r.session_id "
        "where r.passed = 1 and r.skipped = 0"
    ):
        minutes_by_day[_local_date(r["finished_at"])] += r["focused_seconds"] / 60

    heatmap = [
        {
            "date": (d := today - timedelta(days=HEATMAP_DAYS - 1 - i)).isoformat(),
            "minutes": round(minutes_by_day.get(d, 0)),
        }
        for i in range(HEATMAP_DAYS)
    ]
    week = sum(minutes_by_day.get(today - timedelta(days=i), 0) for i in range(WEEK_DAYS))

    last = conn.execute(
        "select d.id, d.title, d.last_page from study_session s join document d on d.id = s.document_id "
        "order by s.id desc limit 1"
    ).fetchone()
    waiting = conn.execute(
        "select id from study_session where status = 'gate' order by id desc limit 1"
    ).fetchone()
    rv = review_stats(conn, at)
    return {
        "verified_minutes_today": round(minutes_by_day.get(today, 0)),
        "verified_minutes_week": round(week),
        "heatmap": heatmap,
        "next_block": {"document_id": last["id"], "title": last["title"], "page": last["last_page"]}
        if last
        else None,
        "awaiting_gate_session_id": waiting["id"] if waiting else None,
        "due_cards": rv["due_now"],
        "review_remaining_today": rv["remaining_today"],
    }
