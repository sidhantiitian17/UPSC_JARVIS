"""PYQ <-> syllabus tags. A model only suggests; a tag counts once the owner accepts it."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from jarvis.llm.client import LLMClient
from jarvis.pyq.service import PyqError, get_question
from jarvis.study.tagging import tag_passage_detailed

TEXT_STATUSES = ("parsed", "reviewed", "verified")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def tags_for(conn: sqlite3.Connection, qid: str) -> list[dict]:
    rows = conn.execute(
        "select t.node_id, n.title, t.status, t.source from pyq_tag t "
        "join syllabus_node n on n.id = t.node_id "
        "where t.pyq_id = ? order by t.rowid",
        (qid,),
    ).fetchall()
    return [dict(r) for r in rows]


def _passage(q: dict) -> str:
    opts = "\n".join(f"({chr(97 + i)}) {o}" for i, o in enumerate(q["options"]))
    return f"{q['stem']}\n{opts}".strip()


def _link(conn: sqlite3.Connection, qid: str, node_id: str) -> None:
    conn.execute(
        "insert or ignore into link(src_type,src_id,dst_type,dst_id,kind) values ('pyq',?,'node',?,'tag')",
        (qid, node_id),
    )


def _unlink(conn: sqlite3.Connection, qid: str, node_id: str) -> None:
    conn.execute(
        "delete from link where src_type='pyq' and src_id=? and dst_type='node' and dst_id=? and kind='tag'",
        (qid, node_id),
    )


def suggest_tags(conn: sqlite3.Connection, llm: LLMClient, qid: str) -> list[dict]:
    q = get_question(conn, qid)
    if not q["stem"].strip():
        raise PyqError("This question has no text yet. Fix its text first, then ask for tags.")
    ids, source = tag_passage_detailed(llm, conn, _passage(q))
    decided = {
        r["node_id"]
        for r in conn.execute(
            "select node_id from pyq_tag where pyq_id = ? and status != 'suggested'", (qid,)
        )
    }
    conn.execute("delete from pyq_tag where pyq_id = ? and status = 'suggested'", (qid,))
    for node_id in ids:
        if node_id not in decided and source in ("llm", "keyword"):
            conn.execute(
                "insert into pyq_tag(pyq_id,node_id,status,source,created_at) values (?,?,'suggested',?,?)",
                (qid, node_id, source, _now()),
            )
    return tags_for(conn, qid)


def decide(conn: sqlite3.Connection, qid: str, node_id: str, decision: str) -> list[dict]:
    if decision not in ("accept", "reject"):
        raise PyqError("The decision must be accept or reject.")
    get_question(conn, qid)
    row = conn.execute("select 1 from pyq_tag where pyq_id = ? and node_id = ?", (qid, node_id)).fetchone()
    if row is None:
        raise KeyError(node_id)
    if decision == "accept":
        conn.execute(
            "update pyq_tag set status = 'accepted' where pyq_id = ? and node_id = ?", (qid, node_id)
        )
        _link(conn, qid, node_id)
    else:
        conn.execute(
            "update pyq_tag set status = 'rejected' where pyq_id = ? and node_id = ?", (qid, node_id)
        )
        _unlink(conn, qid, node_id)
    return tags_for(conn, qid)


def add_manual(conn: sqlite3.Connection, qid: str, node_id: str) -> list[dict]:
    get_question(conn, qid)
    if conn.execute("select 1 from syllabus_node where id = ?", (node_id,)).fetchone() is None:
        raise PyqError(f"Unknown syllabus node: {node_id}.")
    conn.execute(
        "insert into pyq_tag(pyq_id,node_id,status,source,created_at) values (?,?,'accepted','owner',?) "
        "on conflict(pyq_id,node_id) do update set status='accepted', source='owner'",
        (qid, node_id, _now()),
    )
    _link(conn, qid, node_id)
    return tags_for(conn, qid)


def suggest_batch(conn: sqlite3.Connection, llm: LLMClient, limit: int) -> dict[str, int]:
    marks = ",".join("?" * len(TEXT_STATUSES))
    no_text = conn.execute("select count(*) from pyq where trim(stem) = ''").fetchone()[0]
    tagged = conn.execute(
        f"select count(*) from pyq where trim(stem) != '' and status in ({marks}) "
        "and id in (select pyq_id from pyq_tag)",
        TEXT_STATUSES,
    ).fetchone()[0]
    todo = [
        r["id"]
        for r in conn.execute(
            f"select id from pyq where trim(stem) != '' and status in ({marks}) "
            "and id not in (select pyq_id from pyq_tag) order by phase, year, paper, number",
            TEXT_STATUSES,
        )
    ]
    for qid in todo[:limit]:
        suggest_tags(conn, llm, qid)
    done = min(limit, len(todo))
    return {
        "tagged": done,
        "skipped_no_text": no_text,
        "already_tagged": tagged,
        "remaining": len(todo) - done,
    }
