"""Import the Phase 0 PYQ Markdown dataset into SQLite. Idempotent; never overwrites the owner's work."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import yaml

from jarvis.pyq.service import PyqError

_Q_SPLIT = re.compile(r"^## Q\d+\s*$", re.MULTILINE)
_YAML_BLOCK = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
_RAW_BLOCK = re.compile(r"\*\*Raw text \(unparsed\):\*\*\s*```text\n(.*?)\n```", re.DOTALL)
_OPTION = re.compile(r"^- \(([a-d])\)\s?(.*)$")


def parse_paper(text: str) -> tuple[dict, list[dict]]:
    """Frontmatter dict and the list of question dicts of one paper file."""
    if not text.startswith("---\n"):
        raise PyqError("Not a PYQ dataset file (no frontmatter).")
    end = text.index("\n---\n", 4)
    meta = yaml.safe_load(text[4:end]) or {}
    body = text[end + 5 :]
    questions: list[dict] = []
    for block in _Q_SPLIT.split(body)[1:]:
        ym = _YAML_BLOCK.search(block)
        if not ym:
            continue
        q = yaml.safe_load(ym.group(1)) or {}
        rest = block[ym.end() :]
        raw = _RAW_BLOCK.search(rest)
        head = rest[: raw.start()] if raw else rest
        marker = head.find("**Question.**")
        text_part = head[marker + len("**Question.**") :] if marker >= 0 else ""
        stem_lines: list[str] = []
        options: list[str] = []
        in_options = False
        for line in text_part.splitlines():
            om = _OPTION.match(line)
            if om:
                in_options = True
                options.append(om.group(2).strip())
            elif in_options:
                if line.strip():
                    options[-1] += " " + line.strip()  # continuation of the previous option
            else:
                stem_lines.append(line)
        q["stem"] = "\n".join(stem_lines).strip()
        q["options"] = options
        q["raw_text"] = raw.group(1) if raw else None
        questions.append(q)
    return meta, questions


def _owner_touched(row: sqlite3.Row) -> bool:
    return row["status"] in ("reviewed", "verified") or row["answer_source"] == "owner-verified"


def _values(q: dict, meta: dict, now: str) -> dict:
    return {
        "id": q["id"],
        "phase": q["phase"],
        "year": q["year"],
        "paper": q["paper"],
        "number": q["number"],
        "page": q.get("page"),
        "marks": q.get("marks"),
        "negative_marks": q.get("negative_marks"),
        "source_url": meta.get("source_url"),
        "source_sha256": meta.get("source_sha256"),
        "updated_at": now,
        "stem": q["stem"],
        "options_json": json.dumps(q["options"]),
        "raw_text": q["raw_text"],
        "answer": q.get("answer"),
        "answer_source": q.get("answer_source", "none"),
        "suggested_answer": q.get("suggested_answer"),
        "status": q.get("status", "parsed"),
    }


def import_dataset(conn: sqlite3.Connection, root: Path) -> dict[str, int]:
    root = Path(root)
    if not root.is_dir():
        raise PyqError("The dataset folder does not exist.")
    stats = {"files": 0, "questions": 0, "inserted": 0, "updated": 0, "kept_owner_edits": 0}
    now = datetime.now(UTC).isoformat()
    conn.execute("begin")
    try:
        for path in sorted(root.rglob("*.md")):
            meta, questions = parse_paper(path.read_text(encoding="utf-8"))
            stats["files"] += 1
            for q in questions:
                stats["questions"] += 1
                v = _values(q, meta, now)
                row = conn.execute("select * from pyq where id = :id", v).fetchone()
                if row is None:
                    conn.execute(
                        "insert into pyq(id,phase,year,paper,number,page,marks,negative_marks,source_url,"
                        "source_sha256,updated_at,stem,options_json,raw_text,answer,answer_source,"
                        "suggested_answer,status) values (:id,:phase,:year,:paper,:number,:page,:marks,"
                        ":negative_marks,:source_url,:source_sha256,:updated_at,:stem,:options_json,:raw_text,"
                        ":answer,:answer_source,:suggested_answer,:status)",
                        v,
                    )
                    stats["inserted"] += 1
                elif _owner_touched(row):
                    # Keep the owner's text, answer, answer source and status: refresh provenance only.
                    conn.execute(
                        "update pyq set page=:page, source_url=:source_url, source_sha256=:source_sha256, "
                        "suggested_answer=:suggested_answer, updated_at=:updated_at where id=:id",
                        v,
                    )
                    stats["kept_owner_edits"] += 1
                else:
                    conn.execute(
                        "update pyq set phase=:phase, year=:year, paper=:paper, number=:number, page=:page, "
                        "marks=:marks, negative_marks=:negative_marks, source_url=:source_url, "
                        "source_sha256=:source_sha256, updated_at=:updated_at, stem=:stem, "
                        "options_json=:options_json, raw_text=:raw_text, answer=:answer, "
                        "answer_source=:answer_source, suggested_answer=:suggested_answer, status=:status "
                        "where id=:id",
                        v,
                    )
                    stats["updated"] += 1
        conn.execute("commit")
    except Exception:
        conn.execute("rollback")
        raise
    return stats
