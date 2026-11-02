"""PYQ review: browse, edit (owner only) and verify. No answer is ever filled by a model."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime


class PyqError(ValueError):
    """Invalid request; the message is safe to show to the owner."""


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["options"] = json.loads(d.pop("options_json"))
    return d


def _attach_tags(conn: sqlite3.Connection, rows: list[dict]) -> list[dict]:
    if not rows:
        return rows
    by_q: dict[str, list[dict]] = {r["id"]: [] for r in rows}
    marks = ",".join("?" * len(by_q))
    for t in conn.execute(
        "select t.pyq_id, t.node_id, n.title, t.status, t.source from pyq_tag t "
        f"join syllabus_node n on n.id = t.node_id where t.pyq_id in ({marks}) order by t.rowid",
        list(by_q),
    ):
        by_q[t["pyq_id"]].append(
            {"node_id": t["node_id"], "title": t["title"], "status": t["status"], "source": t["source"]}
        )
    for r in rows:
        r["tags"] = by_q[r["id"]]
    return rows


def get_question(conn: sqlite3.Connection, qid: str) -> dict:
    r = conn.execute("select * from pyq where id = ?", (qid,)).fetchone()
    if r is None:
        raise KeyError(qid)
    return _attach_tags(conn, [_row(r)])[0]


def list_papers(conn: sqlite3.Connection) -> list[dict]:
    out = []
    for r in conn.execute(
        "select phase, year, paper, count(*) as total, "
        "sum(status='parsed') as parsed, sum(status='failed') as failed, "
        "sum(status='reviewed') as reviewed, sum(status='verified') as verified "
        "from pyq group by phase, year, paper order by phase, year, paper"
    ):
        out.append({k: (r[k] or 0) if k not in ("phase", "paper") else r[k] for k in r.keys()})  # noqa: SIM118
    return out


def list_questions(
    conn: sqlite3.Connection,
    phase: str | None = None,
    year: int | None = None,
    paper: str | None = None,
    status: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    where, args = [], []
    for col, val in (("phase", phase), ("year", year), ("paper", paper), ("status", status)):
        if val is not None:
            where.append(f"{col} = ?")
            args.append(val)
    sql = "select * from pyq" + (f" where {' and '.join(where)}" if where else "")
    sql += " order by phase, year, paper, number limit ? offset ?"
    return _attach_tags(conn, [_row(r) for r in conn.execute(sql, (*args, limit, offset))])


def update_question(
    conn: sqlite3.Connection,
    qid: str,
    stem: str | None,
    options: list[str] | None,
    answer: str | None,
) -> dict:
    current = get_question(conn, qid)
    if options is not None and (
        len(options) != 4 or not all(isinstance(o, str) and o.strip() for o in options)
    ):
        raise PyqError("A question needs exactly four options, all non-empty.")
    if answer is not None and answer not in ("", "a", "b", "c", "d"):
        raise PyqError("The answer must be a, b, c or d (or empty to clear it).")

    sets: list[str] = ["updated_at = ?"]
    args: list = [datetime.now(UTC).isoformat()]
    content_changed = False
    if stem is not None and stem.strip() != current["stem"]:
        sets.append("stem = ?")
        args.append(stem.strip())
        content_changed = True
    if options is not None and [o.strip() for o in options] != current["options"]:
        sets.append("options_json = ?")
        args.append(json.dumps([o.strip() for o in options]))
        content_changed = True
    if answer is not None:
        if answer == "":
            sets += ["answer = NULL", "answer_source = 'none'"]
        else:
            sets += ["answer = ?", "answer_source = 'owner-verified'"]
            args.append(answer)
    if content_changed:
        sets.append("status = 'reviewed'")  # any text edit needs a fresh verification
    conn.execute(f"update pyq set {', '.join(sets)} where id = ?", (*args, qid))
    return get_question(conn, qid)


def mark_verified(conn: sqlite3.Connection, qid: str) -> dict:
    q = get_question(conn, qid)
    if not q["stem"].strip():
        raise PyqError("A verified question needs a stem. Fix the text first.")
    if len(q["options"]) != 4 or not all(o.strip() for o in q["options"]):
        raise PyqError("A verified question needs four options, all filled in.")
    if q["phase"] == "prelims" and q["page"] is None:
        raise PyqError("A verified Prelims question needs its page number.")
    if not q["source_url"] or not q["source_sha256"]:
        raise PyqError("A verified question needs its official source URL and source hash.")
    conn.execute(
        "update pyq set status = 'verified', updated_at = ? where id = ?",
        (datetime.now(UTC).isoformat(), qid),
    )
    return get_question(conn, qid)
