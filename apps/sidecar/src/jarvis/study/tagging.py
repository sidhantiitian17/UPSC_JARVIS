"""Tag a reading range with syllabus nodes: LLM first (task tag_chunk), deterministic keywords as fallback."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from jarvis.llm.client import AllProvidersFailed, LLMClient
from jarvis.llm.types import Message

MAX_TAGS = 3
MAX_PASSAGE_CHARS = 6000
MAX_CANDIDATES = 150
TAG_SCHEMA = {
    "type": "object",
    "required": ["node_ids"],
    "properties": {"node_ids": {"type": "array", "items": {"type": "string"}, "minItems": 0, "maxItems": 3}},
    "additionalProperties": False,
}
_SYSTEM = (
    "You map a reading passage from a UPSC study book to syllabus nodes. Choose 1 to 3 node ids from the "
    "candidate list that the passage is mainly about. Never invent ids. Reply with JSON only: "
    '{"node_ids": ["..."]}.'
)
_STOP = {"and", "the", "of", "for", "with", "their", "other", "from", "into", "india", "indian"}


@dataclass(frozen=True)
class Candidate:
    id: str
    title: str


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]{4,}", text.lower()) if t not in _STOP}


def candidate_nodes(conn: sqlite3.Connection, passage: str) -> list[Candidate]:
    """Leaf nodes of the syllabus tree (the most specific places a passage can belong)."""
    rows = conn.execute(
        "select id, title from syllabus_node n where not exists "
        "(select 1 from syllabus_node c where c.parent_id = n.id) order by rowid"
    ).fetchall()
    cands = [Candidate(r["id"], r["title"]) for r in rows]
    if len(cands) > MAX_CANDIDATES:  # keep the prompt small: prefilter lexically
        words = _tokens(passage)
        cands.sort(key=lambda c: -len(_tokens(c.title) & words))
        cands = cands[:MAX_CANDIDATES]
    return cands


def keyword_tag(passage: str, candidates: list[Candidate]) -> list[str]:
    words = _tokens(passage)
    scored = [(len(_tokens(c.title) & words), c.id) for c in candidates]
    best = sorted((s for s in scored if s[0] > 0), key=lambda s: -s[0])[:2]
    return [cid for _, cid in best]


def _clip(passage: str) -> str:
    if len(passage) <= MAX_PASSAGE_CHARS:
        return passage
    half = MAX_PASSAGE_CHARS // 2
    return passage[:half] + "\n[...]\n" + passage[-half:]


def tag_passage(llm: LLMClient, conn: sqlite3.Connection, passage: str) -> list[str]:
    cands = candidate_nodes(conn, passage)
    if not cands:
        return []
    valid = {c.id for c in cands}
    listing = "\n".join(
        f"- {c.id}: {c.title[:90]}" for c in cands
    )  # long official points: keep prompts small
    messages = [
        Message("system", _SYSTEM),
        Message("user", f"Candidates:\n{listing}\n\nPassage:\n{_clip(passage)}"),
    ]
    try:
        result = llm.complete(
            "tag_chunk", messages, json_schema=TAG_SCHEMA, prompt_version="tag-v1", timeout=20.0
        )
        ids = [i for i in (result.data or {}).get("node_ids", []) if i in valid]
        seen: list[str] = []
        for i in ids:
            if i not in seen:
                seen.append(i)
        if seen:
            return seen[:MAX_TAGS]
    except AllProvidersFailed:
        pass
    return keyword_tag(passage, cands)
