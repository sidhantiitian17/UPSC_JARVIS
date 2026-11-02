"""Study sessions: start/end bookmarks (page + chunk), tagging links, Source Budget."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from jarvis.llm.client import LLMClient
from jarvis.study.tagging import tag_passage

SOURCE_BUDGET_LIMIT = 3


class SessionError(ValueError):
    """Invalid request; message is safe to show."""


class SessionConflict(Exception):
    def __init__(self, session_id: int, message: str):
        super().__init__(message)
        self.session_id = session_id


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _chunk(conn: sqlite3.Connection, chunk_id: int | None) -> dict | None:
    if chunk_id is None:
        return None
    r = conn.execute("select id, document_id, page, ordinal from chunk where id = ?", (chunk_id,)).fetchone()
    return dict(r) if r else None


def _pos(c: dict) -> tuple[int, int]:
    return (c["page"], c["ordinal"])


def _tags(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute(
        "select n.id, n.title from link l join syllabus_node n on n.id = l.dst_id "
        "where l.src_type='session' and l.src_id=? and l.dst_type='node' and l.kind='tag' order by l.rowid",
        (str(session_id),),
    ).fetchall()
    return [dict(r) for r in rows]


def _source_budget(conn: sqlite3.Connection, tags: list[dict]) -> list[dict]:
    out = []
    for t in tags:
        n = conn.execute(
            "select count(distinct s.document_id) from link l "
            "join study_session s on s.id = cast(l.src_id as integer) "
            "where l.src_type='session' and l.dst_type='node' and l.dst_id=? and l.kind='tag' "
            "and s.status in ('gate','done')",
            (t["id"],),
        ).fetchone()[0]
        if n > SOURCE_BUDGET_LIMIT:
            out.append({"node_id": t["id"], "title": t["title"], "sources": n})
    return out


def session_view(conn: sqlite3.Connection, session_id: int) -> dict:
    s = conn.execute(
        "select s.*, d.title as document_title from study_session s join document d on d.id = s.document_id "
        "where s.id = ?",
        (session_id,),
    ).fetchone()
    if s is None:
        raise KeyError(session_id)
    tags = _tags(conn, session_id)
    start, end = _chunk(conn, s["start_chunk_id"]), _chunk(conn, s["end_chunk_id"])

    def pt(c: dict | None) -> dict | None:
        return None if c is None else {"chunk_id": c["id"], "page": c["page"], "ordinal": c["ordinal"]}

    return {
        "id": s["id"],
        "document_id": s["document_id"],
        "document_title": s["document_title"],
        "status": s["status"],
        "started_at": s["started_at"],
        "ended_at": s["ended_at"],
        "focused_seconds": s["focused_seconds"],
        "start": pt(start),
        "end": pt(end),
        "tags": tags,
        "needs_tagging": s["status"] in ("gate", "done") and not tags,
        "source_budget": _source_budget(conn, tags),
    }


def active_session(conn: sqlite3.Connection) -> dict | None:
    r = conn.execute(
        "select id from study_session where status = 'running' order by id desc limit 1"
    ).fetchone()
    return session_view(conn, r["id"]) if r else None


def start_session(conn: sqlite3.Connection, document_id: int, start_chunk_id: int) -> dict:
    running = conn.execute("select id from study_session where status = 'running'").fetchone()
    if running:
        raise SessionConflict(running["id"], "A study session is already running.")
    chunk = _chunk(conn, start_chunk_id)
    if chunk is None or chunk["document_id"] != document_id:
        raise SessionError("That bookmark position does not belong to this document.")
    cur = conn.execute(
        "insert into study_session(document_id,start_chunk_id,started_at,status) values (?,?,?,'running')",
        (document_id, start_chunk_id, _now()),
    )
    return session_view(conn, cur.lastrowid)


def _range_text(conn: sqlite3.Connection, doc_id: int, start: dict, end: dict) -> str:
    rows = conn.execute(
        "select text from chunk where document_id = ? and (page > ? or (page = ? and ordinal >= ?)) "
        "and (page < ? or (page = ? and ordinal <= ?)) order by page, ordinal",
        (doc_id, start["page"], start["page"], start["ordinal"], end["page"], end["page"], end["ordinal"]),
    ).fetchall()
    return "\n\n".join(r["text"] for r in rows)


def _set_tags(conn: sqlite3.Connection, session_id: int, node_ids: list[str]) -> None:
    conn.execute(
        "delete from link where src_type='session' and src_id=? and dst_type='node' and kind='tag'",
        (str(session_id),),
    )
    for nid in node_ids:
        conn.execute(
            "insert or ignore into link(src_type,src_id,dst_type,dst_id,kind) "
            "values ('session',?,'node',?,'tag')",
            (str(session_id), nid),
        )


def end_session(
    conn: sqlite3.Connection,
    llm: LLMClient,
    session_id: int,
    end_chunk_id: int,
    focused_seconds: int | None,
) -> dict:
    row = conn.execute("select * from study_session where id = ?", (session_id,)).fetchone()
    if row is None:
        raise KeyError(session_id)
    if row["status"] != "running":
        raise SessionConflict(session_id, "This session has already ended.")
    start, end = _chunk(conn, row["start_chunk_id"]), _chunk(conn, end_chunk_id)
    if end is None or end["document_id"] != row["document_id"]:
        raise SessionError("The end bookmark must be in the same document as the start.")
    if start is None or _pos(end) < _pos(start):
        raise SessionError("The end bookmark cannot be before the start bookmark.")
    if focused_seconds is None:
        elapsed = datetime.now(UTC) - datetime.fromisoformat(row["started_at"])
        focused_seconds = max(0, int(elapsed.total_seconds()))
    conn.execute(
        "update study_session set end_chunk_id=?, ended_at=?, focused_seconds=?, status='gate' where id=?",
        (end_chunk_id, _now(), focused_seconds, session_id),
    )
    passage = _range_text(conn, row["document_id"], start, end)
    _set_tags(conn, session_id, tag_passage(llm, conn, passage))
    return session_view(conn, session_id)


def set_manual_tags(conn: sqlite3.Connection, session_id: int, node_ids: list[str]) -> dict:
    if conn.execute("select 1 from study_session where id=?", (session_id,)).fetchone() is None:
        raise KeyError(session_id)
    ids = list(dict.fromkeys(node_ids))
    known = {r["id"] for r in conn.execute("select id from syllabus_node")}
    unknown = [i for i in ids if i not in known]
    if unknown or not ids:
        raise SessionError(f"Unknown syllabus node(s): {', '.join(unknown) or 'none given'}.")
    _set_tags(conn, session_id, ids)
    return session_view(conn, session_id)


def cancel_session(conn: sqlite3.Connection, session_id: int) -> dict:
    row = conn.execute("select status from study_session where id=?", (session_id,)).fetchone()
    if row is None:
        raise KeyError(session_id)
    if row["status"] != "running":
        raise SessionConflict(session_id, "Only a running session can be cancelled.")
    conn.execute("update study_session set status='skipped', ended_at=? where id=?", (_now(), session_id))
    return session_view(conn, session_id)
