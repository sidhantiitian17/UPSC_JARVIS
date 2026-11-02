"""Render sessions, cards and the daily note as Markdown into <vault>/JARVIS/…"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, date, datetime

from jarvis.vault.writer import VaultError, VaultWriter, safe_filename

ROOT = "JARVIS"
_PLAIN = re.compile(r"^[A-Za-z0-9 ._\-]+$")


def _scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    s = str(value)
    return s if _PLAIN.match(s) else json.dumps(s, ensure_ascii=False)


def _frontmatter(fields: dict[str, object]) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, list):
            lines.append(f"{k}: [" + ", ".join(_scalar(x) for x in v) + "]")
        else:
            lines.append(f"{k}: {_scalar(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _local_date(iso: str) -> date:
    return datetime.fromisoformat(iso).astimezone().date()


def _session_nodes(conn: sqlite3.Connection, session_id: int) -> list[str]:
    return [
        r["title"]
        for r in conn.execute(
            "select n.title from link l join syllabus_node n on n.id = l.dst_id "
            "where l.src_type='session' and l.src_id=? and l.dst_type='node' and l.kind='tag' "
            "order by l.rowid",
            (str(session_id),),
        )
    ]


def session_stem(conn: sqlite3.Connection, session_id: int) -> str | None:
    r = conn.execute(
        "select s.id, d.title, g.finished_at from study_session s join document d on d.id = s.document_id "
        "join gate_result g on g.session_id = s.id where s.id = ?",
        (session_id,),
    ).fetchone()
    if r is None:
        return None
    return f"{_local_date(r['finished_at']).isoformat()}-{r['id']}-{safe_filename(r['title'])}"


def mirror_session(conn: sqlite3.Connection, w: VaultWriter, session_id: int) -> None:
    r = conn.execute(
        "select s.*, d.title as book, g.total, g.correct, g.retention_pct, g.passed, g.skipped, g.xp, "
        "g.finished_at, cs.page as p1, ce.page as p2 from study_session s "
        "join document d on d.id = s.document_id join gate_result g on g.session_id = s.id "
        "join chunk cs on cs.id = s.start_chunk_id join chunk ce on ce.id = s.end_chunk_id where s.id = ?",
        (session_id,),
    ).fetchone()
    if r is None:
        return
    nodes = _session_nodes(conn, session_id)
    fm = {
        "type": "session",
        "session_id": r["id"],
        "date": _local_date(r["finished_at"]).isoformat(),
        "book": r["book"],
        "pages": f"{r['p1']}-{r['p2']}",
        "focused_minutes": round(r["focused_seconds"] / 60),
        "retention": r["retention_pct"],
        "passed": bool(r["passed"]),
        "skipped": bool(r["skipped"]),
        "xp": r["xp"],
    }
    body = [f"# Study session: {r['book']}, pages {r['p1']}-{r['p2']}", ""]
    if nodes:
        body += ["## Syllabus", *[f"- [[{n}]]" for n in nodes], ""]
    if r["skipped"]:
        body += ["## Result", "Gate skipped. No coverage was awarded.", ""]
    else:
        verdict = "Passed" if r["passed"] else "Not passed"
        body += [
            "## Result",
            f"{verdict}: {r['correct']} of {r['total']} correct, retention {r['retention_pct']}%.",
            "",
        ]
    if not r["passed"] and not r["skipped"]:
        wrong = conn.execute(
            "select q.source_quote, c.page, c.ordinal from attempt a join question q on q.id = a.question_id "
            "join chunk c on c.id = q.source_chunk_id where a.session_id = ? and a.correct = 0 "
            "order by c.page, c.ordinal",
            (session_id,),
        ).fetchall()
        body += ["## Restudy"]
        seen: set[tuple[int, int]] = set()
        for q in wrong:
            if (q["page"], q["ordinal"]) in seen:
                continue
            seen.add((q["page"], q["ordinal"]))
            body.append(f"- page {q['page']}, paragraph {q['ordinal'] + 1}: “{q['source_quote']}”")
        body.append("")
    stem = session_stem(conn, session_id)
    w.write(f"{ROOT}/Sessions/{stem}.md", _frontmatter(fm) + "\n".join(body))


def mirror_cards(conn: sqlite3.Connection, w: VaultWriter, session_id: int) -> None:
    rows = conn.execute(
        "select c.id as card_id, c.due, c.subject_id, q.*, ch.page, ch.ordinal, d.title as book "
        "from attempt a join question q on q.id = a.question_id join card c on c.question_id = q.id "
        "left join chunk ch on ch.id = q.source_chunk_id left join document d on d.id = ch.document_id "
        "where a.session_id = ? and a.correct = 0 group by q.id",
        (session_id,),
    ).fetchall()
    nodes = _session_nodes(conn, session_id)
    for q in rows:
        options = json.loads(q["options_json"])
        fm = {
            "type": "card",
            "question_id": q["id"],
            "subject": q["subject_id"] or "unknown",
            "due": q["due"],
            "source": q["source"],
        }
        body = [
            "## Question",
            q["stem"],
            "",
            *[f"- {chr(65 + i)}. {o}" for i, o in enumerate(options)],
            "",
            "## Answer",
            f"{chr(65 + q['answer_index'])}. {options[q['answer_index']]}",
            "",
        ]
        if q["explanation"]:
            body += ["## Explanation", q["explanation"], ""]
        body += [
            "## Source",
            f"“{q['source_quote']}”",
            f"{q['book']}, page {q['page']}, paragraph {q['ordinal'] + 1}" if q["page"] else "",
            "",
        ]
        if nodes:
            body += ["## Nodes", *[f"- [[{n}]]" for n in nodes], ""]
        try:
            w.write(f"{ROOT}/Cards/q-{q['id']}.md", _frontmatter(fm) + "\n".join(body))
        except VaultError:
            continue  # one unsafe card is skipped; the rest are still mirrored


def mirror_daily(conn: sqlite3.Connection, w: VaultWriter, at: datetime | None = None) -> None:
    day = (at or datetime.now(UTC)).astimezone().date()
    rows = [
        r
        for r in conn.execute(
            "select s.id, s.focused_seconds, d.title, g.finished_at, g.retention_pct, g.passed, g.skipped "
            "from gate_result g join study_session s on s.id = g.session_id "
            "join document d on d.id = s.document_id order by g.finished_at"
        )
        if _local_date(r["finished_at"]) == day
    ]
    verified = round(sum(r["focused_seconds"] for r in rows if r["passed"] and not r["skipped"]) / 60)
    body = [f"# {day.isoformat()}", "", f"Verified retained minutes: {verified}", "", "## Sessions"]
    for r in rows:
        stem = session_stem(conn, r["id"])
        result = "skipped" if r["skipped"] else ("passed" if r["passed"] else "not passed")
        body.append(f"- [[Sessions/{stem}]] {r['title']}, retention {r['retention_pct']}%, {result}")
    if not rows:
        body.append("- none yet")
    fm = {"type": "daily", "date": day.isoformat(), "verified_minutes": verified}
    w.write(f"{ROOT}/Daily/{day.isoformat()}.md", _frontmatter(fm) + "\n".join(body) + "\n")


def mirror_after_gate(conn: sqlite3.Connection, w: VaultWriter, session_id: int) -> None:
    """Everything a finished (or skipped) gate leaves in the vault. Callers swallow failures."""
    mirror_session(conn, w, session_id)
    mirror_cards(conn, w, session_id)
    mirror_daily(conn, w)
