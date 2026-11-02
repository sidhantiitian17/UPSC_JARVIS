"""Answering, scoring and the consequences of a recall gate (specs/gate-scoring.feature)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime, timedelta

from jarvis.review.fsrs_service import create_or_lapse_card, subject_for_session
from jarvis.study.sessions import SessionConflict

PASS_PERCENT = 70
PENALTY_MULTIPLIER = 2


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _gate_question(conn: sqlite3.Connection, session_id: int, question_id: int) -> sqlite3.Row:
    row = conn.execute(
        "select q.*, c.page as cpage, c.ordinal as cord from gate_question g "
        "join question q on q.id = g.question_id left join chunk c on c.id = q.source_chunk_id "
        "where g.session_id = ? and g.question_id = ? and q.status = 'active'",
        (session_id, question_id),
    ).fetchone()
    if row is None:
        raise KeyError(question_id)
    return row


def _reveal(q: sqlite3.Row, attempt: sqlite3.Row) -> dict:
    return {
        "question_id": q["id"],
        "correct": bool(attempt["correct"]),
        "chosen_index": attempt["chosen_index"],
        "answer_index": q["answer_index"],
        "explanation": q["explanation"] or "",
        "source_quote": q["source_quote"] or "",
        "chunk_id": q["source_chunk_id"],
        "page": q["cpage"],
        "ordinal": q["cord"],
    }


def _require_session(conn: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = conn.execute("select * from study_session where id = ?", (session_id,)).fetchone()
    if row is None:
        raise KeyError(session_id)
    return row


def answer_question(
    conn: sqlite3.Connection,
    session_id: int,
    question_id: int,
    chosen_index: int,
    confidence: str,
    time_ms: int | None,
) -> dict:
    _require_session(conn, session_id)
    q = _gate_question(conn, session_id, question_id)
    existing = conn.execute(
        "select * from attempt where session_id = ? and question_id = ?", (session_id, question_id)
    ).fetchone()
    if existing:
        return _reveal(q, existing)
    conn.execute(
        "insert into attempt(question_id,session_id,chosen_index,correct,confidence,time_ms,answered_at) "
        "values (?,?,?,?,?,?,?)",
        (
            question_id,
            session_id,
            chosen_index,
            int(chosen_index == q["answer_index"]),
            confidence,
            time_ms,
            _now(),
        ),
    )
    attempt = conn.execute(
        "select * from attempt where session_id = ? and question_id = ?", (session_id, question_id)
    ).fetchone()
    return _reveal(q, attempt)


def _restudy(conn: sqlite3.Connection, session_id: int, book: str) -> list[dict]:
    rows = conn.execute(
        "select q.source_chunk_id as chunk_id, q.source_quote as quote, c.page, c.ordinal "
        "from attempt a join question q on q.id = a.question_id join chunk c on c.id = q.source_chunk_id "
        "where a.session_id = ? and a.correct = 0 order by c.page, c.ordinal, a.id",
        (session_id,),
    ).fetchall()
    out: list[dict] = []
    seen: set[int] = set()
    for r in rows:
        if r["chunk_id"] in seen:
            continue
        seen.add(r["chunk_id"])
        out.append(
            {
                "chunk_id": r["chunk_id"],
                "book": book,
                "page": r["page"],
                "ordinal": r["ordinal"],
                "quote": r["quote"],
            }
        )
    return out


def _result_view(conn: sqlite3.Connection, session_id: int) -> dict:
    r = conn.execute("select * from gate_result where session_id = ?", (session_id,)).fetchone()
    s = conn.execute(
        "select d.title from study_session s join document d on d.id = s.document_id where s.id = ?",
        (session_id,),
    ).fetchone()
    tags = conn.execute(
        "select n.id, n.title from link l join syllabus_node n on n.id = l.dst_id "
        "where l.src_type='session' and l.src_id=? and l.dst_type='node' and l.kind='tag'",
        (str(session_id),),
    ).fetchall()
    return {
        "session_id": session_id,
        "total": r["total"],
        "correct": r["correct"],
        "retention_pct": r["retention_pct"],
        "passed": bool(r["passed"]),
        "skipped": bool(r["skipped"]),
        "xp": r["xp"],
        "pass_mark": PASS_PERCENT,
        "restudy": [] if r["passed"] or r["skipped"] else _restudy(conn, session_id, s["title"]),
        "nodes": [dict(t) for t in tags] if r["passed"] else [],
    }


def finish_gate(conn: sqlite3.Connection, session_id: int) -> dict:
    session = _require_session(conn, session_id)
    if conn.execute("select 1 from gate_result where session_id = ?", (session_id,)).fetchone():
        return _result_view(conn, session_id)
    total = conn.execute(
        "select count(*) from gate_question g join question q on q.id = g.question_id "
        "where g.session_id = ? and q.status = 'active'",
        (session_id,),
    ).fetchone()[0]
    answered = conn.execute(
        "select count(*), coalesce(sum(a.correct), 0) from attempt a "
        "join gate_question g on g.session_id = a.session_id and g.question_id = a.question_id "
        "join question q on q.id = a.question_id where a.session_id = ? and q.status = 'active'",
        (session_id,),
    ).fetchone()
    if total == 0 or session["status"] != "gate":
        raise SessionConflict(session_id, "There is no open recall gate for this session.")
    if answered[0] < total:
        raise SessionConflict(session_id, f"{total - answered[0]} unanswered question(s) remain.")
    correct = answered[1]
    passed = correct * 100 >= PASS_PERCENT * total
    xp = round(session["focused_seconds"] / 60 * correct / total) if passed else 0
    conn.execute(
        "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) "
        "values (?,?,?,?,?,0,?,?)",
        (session_id, total, correct, round(100 * correct / total), int(passed), xp, _now()),
    )
    conn.execute("update study_session set status = 'done' where id = ?", (session_id,))
    # Every wrongly answered question comes back through the FSRS review queue.
    subject = subject_for_session(conn, session_id)
    for w in conn.execute(
        "select question_id from attempt where session_id = ? and correct = 0", (session_id,)
    ).fetchall():
        create_or_lapse_card(conn, w["question_id"], subject)
    return _result_view(conn, session_id)


def skip_gate(
    conn: sqlite3.Connection, session_id: int, today: date | None = None, penalty: bool = True
) -> dict:
    session = _require_session(conn, session_id)
    if session["status"] != "gate":
        raise SessionConflict(session_id, "This session has no open recall gate to skip.")
    total = conn.execute("select count(*) from gate_question where session_id = ?", (session_id,)).fetchone()[
        0
    ]
    conn.execute(
        "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) "
        "values (?,?,0,0,0,1,0,?)",
        (session_id, total, _now()),
    )
    conn.execute("update study_session set status = 'skipped' where id = ?", (session_id,))
    # A gate that could not be built at all (no questions) is not the owner's fault: no penalty then.
    if penalty or total > 0:
        due = {
            "multiplier": PENALTY_MULTIPLIER,
            "from_date": ((today or date.today()) + timedelta(days=1)).isoformat(),
        }
        conn.execute(
            "insert into setting(key,value_json) values ('gate_penalty',?) "
            "on conflict(key) do update set value_json = excluded.value_json",
            (json.dumps(due),),
        )
    return _result_view(conn, session_id)


def awaiting_gate_session_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        "select id from study_session where status = 'gate' order by id desc limit 1"
    ).fetchone()
    return row["id"] if row else None
