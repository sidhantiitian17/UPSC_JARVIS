"""Build the recall gate for a finished session: bank questions + LLM batches + offline fallback."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime

from jarvis.brain.context_pack import build_context_pack
from jarvis.gate.fallback import cloze_questions
from jarvis.gate.questions import _norm, validate_batch
from jarvis.llm.client import AllProvidersFailed, LLMClient
from jarvis.llm.types import Message
from jarvis.study.sessions import SessionConflict

MIN_Q, MAX_Q = 10, 30
BATCH = 10
CHUNKS_PER_BATCH = 7
BANK_SHARE, APPLICATION_SHARE = 0.2, 0.1

BATCH_SCHEMA = {
    "type": "object",
    "required": ["questions"],
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["stem", "options", "answer_index", "source_quote", "explanation"],
                "properties": {
                    "stem": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
                    "answer_index": {"type": "integer", "minimum": 0},
                    "source_quote": {"type": "string"},
                    "explanation": {"type": "string"},
                    "style": {"type": "string", "enum": ["recall", "application"]},
                },
            },
        }
    },
    "additionalProperties": False,
}
_SYSTEM = (
    "You write multiple-choice recall questions for a UPSC aspirant from the passages the user gives. "
    "Use ONLY facts stated in the passages. Each question has exactly four distinct options and the "
    "zero-based index of the correct one. `source_quote` must be copied verbatim from ONE passage (a "
    "contiguous span that supports the answer); never paraphrase it. `style` is 'recall' for direct "
    "facts and "
    "'application' for a short scenario that applies a fact. Reply with JSON only.\n\n"
)


class GateError(ValueError):
    pass


def target_count(chunk_count: int, multiplier: int = 1) -> int:
    base = min(MAX_Q, max(MIN_Q, round(chunk_count * 0.8)))
    return min(MAX_Q, base * max(1, multiplier))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _range_chunks(conn: sqlite3.Connection, session: sqlite3.Row) -> list[dict]:
    s = conn.execute("select page, ordinal from chunk where id = ?", (session["start_chunk_id"],)).fetchone()
    e = conn.execute("select page, ordinal from chunk where id = ?", (session["end_chunk_id"],)).fetchone()
    rows = conn.execute(
        "select id, page, ordinal, text from chunk where document_id = ? "
        "and (page > ? or (page = ? and ordinal >= ?)) and (page < ? or (page = ? and ordinal <= ?)) "
        "order by page, ordinal",
        (session["document_id"], s["page"], s["page"], s["ordinal"], e["page"], e["page"], e["ordinal"]),
    ).fetchall()
    return [dict(r) for r in rows]


def _setting(conn: sqlite3.Connection, key: str):  # noqa: ANN202
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def _bank(conn: sqlite3.Connection, session_id: int, limit: int) -> list[sqlite3.Row]:
    if limit <= 0:
        return []
    return conn.execute(
        "select distinct q.* from question q "
        "join gate_question g on g.question_id = q.id and g.session_id != ? "
        "join link lo on lo.src_type='session' and lo.src_id = cast(g.session_id as text) "
        "and lo.dst_type='node' and lo.kind='tag' "
        "join link lc on lc.src_type='session' and lc.src_id = ? and lc.dst_type='node' "
        "and lc.kind='tag' and lc.dst_id = lo.dst_id "
        "where q.status = 'active' and q.source = 'generated' "
        "and q.id not in (select question_id from gate_question where session_id = ?) "
        "order by q.id limit ?",
        (session_id, str(session_id), session_id, limit),
    ).fetchall()


def _batches(chunks: list[dict], n_batches: int) -> list[list[dict]]:
    size = max(1, -(-len(chunks) // n_batches))
    groups = [chunks[i : i + size] for i in range(0, len(chunks), size)][:n_batches]
    out = []
    for g in groups:
        if len(g) > CHUNKS_PER_BATCH:  # evenly spaced sample keeps the prompt small
            step = len(g) / CHUNKS_PER_BATCH
            g = [g[int(i * step)] for i in range(CHUNKS_PER_BATCH)]
        out.append(g)
    return out


def _ask(llm: LLMClient, pack: str, group: list[dict], k: int, apps: int) -> list[dict]:
    passage = "\n\n".join(f"[chunk {c['id']} · page {c['page']}]\n{c['text']}" for c in group)
    user = f"Write exactly {k} questions ({apps} of them application-style).\n\nPassage:\n{passage}"
    result = llm.complete(
        "gate_mcq",
        [Message("system", _SYSTEM + pack), Message("user", user)],
        json_schema=BATCH_SCHEMA,
        prompt_version="gate-v1",
        timeout=45.0,
    )
    data = result.data if isinstance(result.data, dict) else {}
    return list(data.get("questions", []))


def _store(conn: sqlite3.Connection, q: dict, source: str, chunk_id: int | None = None) -> int:
    cur = conn.execute(
        "insert into question(kind,source,stem,options_json,answer_index,explanation,source_chunk_id,"
        "source_quote,status,created_at,style) values ('mcq',?,?,?,?,?,?,?,'active',?,?)",
        (
            source,
            q["stem"],
            json.dumps(q["options"]),
            q["answer_index"],
            q["explanation"],
            q.get("source_chunk_id", chunk_id),
            q["source_quote"],
            _now(),
            q.get("style", "recall"),
        ),
    )
    return cur.lastrowid


def gate_view(conn: sqlite3.Connection, session_id: int) -> dict:
    rows = conn.execute(
        "select q.*, g.interleaved, g.position, c.page as cpage, c.ordinal as cord from gate_question g "
        "join question q on q.id = g.question_id left join chunk c on c.id = q.source_chunk_id "
        "where g.session_id = ? and q.status = 'active' order by g.position",
        (session_id,),
    ).fetchall()
    meta = _setting(conn, f"gate_meta:{session_id}") or {}
    questions = [
        {
            "id": r["id"],
            "stem": r["stem"],
            "options": json.loads(r["options_json"]),
            "style": r["style"],
            "source": r["source"],
            "interleaved": bool(r["interleaved"]),
            "chunk_id": r["source_chunk_id"],
            "page": r["cpage"],
            "ordinal": r["cord"],
        }
        for r in rows
    ]
    return {
        "session_id": session_id,
        "questions": questions,
        "discarded": meta.get("discarded", 0),
        "fallback_used": meta.get("fallback_used", False),
        "short_range": meta.get("short_range", False),
    }


def build_gate(conn: sqlite3.Connection, llm: LLMClient, session_id: int, today: date | None = None) -> dict:
    session = conn.execute("select * from study_session where id = ?", (session_id,)).fetchone()
    if session is None:
        raise KeyError(session_id)
    if conn.execute("select 1 from gate_question where session_id = ? limit 1", (session_id,)).fetchone():
        return gate_view(conn, session_id)
    if session["status"] != "gate":
        raise SessionConflict(session_id, "The recall gate opens after the end bookmark is set.")

    chunks = _range_chunks(conn, session)
    if not chunks:
        raise GateError("This range has no readable text to build questions from.")
    penalty = _setting(conn, "gate_penalty") or {}
    due = bool(penalty) and (today or date.today()).isoformat() >= penalty.get("from_date", "9999-12-31")
    multiplier = int(penalty.get("multiplier", 1)) if due else 1
    n = target_count(len(chunks), multiplier)

    bank = _bank(conn, session_id, round(BANK_SHARE * n))
    needed = n - len(bank)
    apps = round(APPLICATION_SHARE * n)
    seen = {_norm(r["stem"]) for r in bank}
    pack = build_context_pack(conn)

    accepted: list[dict] = []
    discarded = 0
    fallback_used = False
    try:
        n_batches = -(-needed // BATCH)
        for gi, group in enumerate(_batches(chunks, n_batches)):
            k = needed // n_batches + (1 if gi < needed % n_batches else 0)
            if k <= 0:
                continue
            ok, bad = validate_batch(_ask(llm, pack, group, k, min(apps, k)), chunks, seen)
            accepted += ok[:k]
            discarded += len(bad) + max(0, len(ok) - k)
        if len(accepted) < needed:  # one top-up round for the shortfall
            gap = needed - len(accepted)
            ok, bad = validate_batch(_ask(llm, pack, chunks[:CHUNKS_PER_BATCH], gap + 2, 0), chunks, seen)
            accepted += ok[:gap]
            discarded += len(bad)
    except AllProvidersFailed:
        pass

    if len(bank) + len(accepted) < min(MIN_Q, n):
        fill = cloze_questions(chunks, n - len(bank) - len(accepted), seen, seed=session_id)
        if fill:
            fallback_used = True
        fb_ids = [(_store(conn, q, "fallback", _chunk_for(q, chunks)), q) for q in fill]
    else:
        fb_ids = []

    if len(bank) + len(accepted) + len(fb_ids) == 0:
        raise GateError("Jarvis could not build questions from this range. Try a longer reading range.")

    position = 0
    for r in bank:
        conn.execute(
            "insert into gate_question(session_id,question_id,position,interleaved) values (?,?,?,1)",
            (session_id, r["id"], position),
        )
        position += 1
    for q in accepted:
        qid = _store(conn, q, "generated")
        conn.execute(
            "insert into gate_question(session_id,question_id,position,interleaved) values (?,?,?,0)",
            (session_id, qid, position),
        )
        position += 1
    for qid, _ in fb_ids:
        conn.execute(
            "insert into gate_question(session_id,question_id,position,interleaved) values (?,?,?,0)",
            (session_id, qid, position),
        )
        position += 1

    if due:  # an emergency-skip penalty is used up by exactly one gate
        conn.execute("delete from setting where key = 'gate_penalty'")

    meta = {"discarded": discarded, "fallback_used": fallback_used, "short_range": position < MIN_Q}
    conn.execute(
        "insert into setting(key,value_json) values (?,?) "
        "on conflict(key) do update set value_json = excluded.value_json",
        (f"gate_meta:{session_id}", json.dumps(meta)),
    )
    return gate_view(conn, session_id)


def _chunk_for(q: dict, chunks: list[dict]) -> int | None:
    quote = _norm(q["source_quote"])
    for c in chunks:
        if quote in _norm(c["text"]):
            return c["id"]
    return None


def report_question(conn: sqlite3.Connection, question_id: int, reason: str) -> None:
    if conn.execute("select 1 from question where id = ?", (question_id,)).fetchone() is None:
        raise KeyError(question_id)
    conn.execute("update question set status = 'reported' where id = ?", (question_id,))
    conn.execute(
        "insert into question_report(question_id, reason, created_at) values (?,?,?)",
        (question_id, reason[:500], _now()),
    )
