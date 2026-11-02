"""Brain Context Pack v1: a compact, code-built student profile added to LLM prompts (no LLM involved)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

MAX_CHARS = 6000
MIN_ATTEMPTS_FOR_WEAK = 3


def _setting(conn: sqlite3.Connection, key: str) -> object:
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def build_context_pack(conn: sqlite3.Connection) -> str:
    exam = _setting(conn, "exam_target") or "not set"
    lines = [f"STUDENT: exam={exam}  medium=EN"]

    weak = conn.execute(
        "select n.title as title, count(*) as total, sum(a.correct) as right "
        "from attempt a join link l on l.src_type='session' and l.src_id = cast(a.session_id as text) "
        "and l.dst_type='node' and l.kind='tag' join syllabus_node n on n.id = l.dst_id "
        "group by n.id having total >= ? order by (1.0 * right / total) asc, total desc limit 5",
        (MIN_ATTEMPTS_FOR_WEAK,),
    ).fetchall()
    if weak:
        items = ", ".join(
            f"{r['title']} (ret {round(100 * r['right'] / r['total'])}%, {r['total']} answers)" for r in weak
        )
        lines.append(f"WEAK NODES (top 5): {items}")
    else:
        lines.append("WEAK NODES: no attempts yet")

    since = (datetime.now(UTC) - timedelta(days=14)).isoformat()
    kinds = conn.execute(
        "select mistake_type, count(*) as n from attempt where correct = 0 and mistake_type is not null "
        "and answered_at >= ? group by mistake_type order by n desc",
        (since,),
    ).fetchall()
    total = sum(r["n"] for r in kinds)
    if total:
        lines.append(
            "MISTAKES (last 14d): "
            + " · ".join(f"{r['mistake_type']} {round(100 * r['n'] / total)}%" for r in kinds)
        )
    else:
        lines.append("MISTAKES (last 14d): none recorded")

    lines.append("STYLE: no-mercy feedback; Hindi terms ok")
    return "\n".join(lines)[:MAX_CHARS]
