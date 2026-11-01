from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from pyq.extract import PageText, clean_text, normalize_ws
from pyq.manifest import SourceRecord
from pyq.models import PaperDoc
from pyq.render import question_dict

SCHEMA_PATH = Path(os.environ.get("PYQ_SCHEMA", Path(__file__).resolve().parents[4] / "datasets/pyq/schema/question.schema.json"))
_validator: Draft202012Validator | None = None


def _schema() -> Draft202012Validator:
    global _validator
    if _validator is None:
        _validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    return _validator


@dataclass
class Issue:
    level: str  # error | warning
    code: str
    message: str
    qid: str | None = None


def validate_doc(doc: PaperDoc, pages: list[PageText] | None) -> list[Issue]:
    issues: list[Issue] = []
    qs = doc.questions
    for q in qs:
        for err in _schema().iter_errors(question_dict(q)):
            issues.append(Issue("error", "schema", err.message, q.id))
        if q.answer is not None and q.answer_source not in ("official-key", "owner-verified"):
            issues.append(Issue("error", "answer-source", "answer set without an official key or owner verification", q.id))
        if not q.id.endswith(f"-{q.number:03d}"):
            issues.append(Issue("error", "id-number", f"id {q.id} does not match number {q.number}", q.id))
    if [q.number for q in qs] != list(range(1, len(qs) + 1)):
        issues.append(Issue("error", "continuity", "question numbers are not exactly 1..N"))
    ids = [q.id for q in qs]
    if len(set(ids)) != len(ids):
        issues.append(Issue("error", "duplicate-id", "duplicate question ids"))
    if doc.meta.get("phase") == "prelims":
        for q in qs:
            if q.status != "failed" and sorted(q.options) != ["a", "b", "c", "d"]:
                issues.append(Issue("error", "options", "expected exactly options a-d", q.id))
    for q in qs:
        if q.status == "failed":
            issues.append(Issue("warning", "failed", "question could not be segmented", q.id))
    exp = doc.meta.get("expected_question_count")
    if exp and exp != len(qs):
        issues.append(Issue("warning", "count-mismatch", f"parsed {len(qs)} questions, expected about {exp}"))
    if pages is not None:
        source = normalize_ws(clean_text(pages)[0])
        for q in qs:
            if q.status == "failed":
                continue
            texts = [q.stem, *q.options.values(), *(p["text"] for p in q.parts)]
            if any(t and normalize_ws(t) not in source for t in texts):
                issues.append(Issue("error", "not-in-source", "parsed text not found in extracted source text", q.id))
    return issues


def coverage_report(docs: list[PaperDoc], manifest: list[SourceRecord]) -> str:
    lines = ["# PYQ coverage report", "", "## Parsed papers", "",
             "| phase | year | paper | questions | parsed | failed | verified |", "|---|---|---|---|---|---|---|"]
    failed_ids: list[str] = []
    for d in sorted(docs, key=lambda d: (d.meta["phase"], d.meta["year"], d.meta["paper"])):
        by_status = Counter(q.status for q in d.questions)
        lines.append(f"| {d.meta['phase']} | {d.meta['year']} | {d.meta['paper']} | {len(d.questions)} | "
                     f"{by_status['parsed']} | {by_status['failed']} | {by_status['verified']} |")
        failed_ids += [q.id for q in d.questions if q.status == "failed"]
    lines += ["", "## Failed questions (need manual attention)", ""]
    lines += [f"- {i} (status: failed)" for i in failed_ids] or ["- none"]
    if manifest:
        counts: dict[str, int] = {}
        for r in manifest:
            counts[r.status] = counts.get(r.status, 0) + 1
        lines += ["", "## Source inventory by status", ""] + [f"- {k}: {v}" for k, v in sorted(counts.items())]
        lines += ["", "## Not downloaded (needs a decision)", ""]
        lines += [f"- {r.year} {r.phase} {r.title} -> {r.status}" for r in manifest
                  if r.status in ("unclassified", "failed", "blocked-by-robots", "blocked-non-official")] or ["- none"]
    return "\n".join(lines) + "\n"
