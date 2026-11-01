from __future__ import annotations

import re
from pathlib import Path

import yaml

from pyq.models import PaperDoc, Question

FM_ORDER = ["dataset", "schema_version", "exam", "phase", "year", "paper", "paper_title", "lang", "source_url",
            "source_sha256", "retrieved_at", "page_count", "parser", "question_count",
            "expected_question_count", "verified_count"]


def _dump(d: dict) -> str:
    return yaml.safe_dump(d, sort_keys=False, allow_unicode=True, default_flow_style=False, width=10_000).rstrip("\n")


def question_dict(q: Question) -> dict:
    d = {"id": q.id, "phase": q.phase, "year": q.year, "paper": q.paper, "number": q.number, "page": q.page,
         "marks": q.marks, "negative_marks": q.negative_marks}
    if q.word_limit is not None:
        d["word_limit"] = q.word_limit
    if q.section:
        d["section"] = q.section
    if q.parts:
        d["parts"] = q.parts
    d.update(answer=q.answer, answer_source=q.answer_source, suggested_answer=q.suggested_answer,
             status=q.status, tags=list(q.tags))
    return d


def md_path(root: Path, meta: dict) -> Path:
    ph, y, paper = meta["phase"], meta["year"], meta["paper"]
    if ph == "optional":
        return Path(root) / "md" / "optional" / "sociology" / str(y) / f"paper-{paper.rsplit('-', 1)[1]}.md"
    return Path(root) / "md" / ph / str(y) / f"{paper}.md"


def render_md(doc: PaperDoc) -> str:
    meta = dict(doc.meta)
    meta["question_count"] = len(doc.questions)
    meta["verified_count"] = sum(1 for q in doc.questions if q.status == "verified")
    ordered = {k: meta[k] for k in FM_ORDER if k in meta}
    ordered.update({k: v for k, v in meta.items() if k not in ordered})
    title = f"{meta['exam'].upper()} {meta['phase'].capitalize()} {meta['year']} — {meta['paper_title']}"
    out = [f"---\n{_dump(ordered)}\n---\n", f"# {title}\n"]
    for q in doc.questions:
        out.append(f"## Q{q.number}\n```yaml\n{_dump(question_dict(q))}\n```\n")
        body = f"**Question.** {q.stem}\n"
        if q.parts:
            body += "\n" + "\n".join(f"- ({p['label']}) {p['text']}" for p in q.parts) + "\n"
        for k, v in q.options.items():
            body += ("\n" if k == "a" else "") + f"- ({k}) {v}\n"
        if q.status == "failed":
            body += f"\n**Raw text (unparsed):**\n```text\n{q.raw_text}\n```\n"
        out.append(body)
    return "\n".join(out)


_FM = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_QBLOCK = re.compile(r"^## Q(\d+)\n```yaml\n(.*?)\n```\n(.*?)(?=^## Q\d+\n```yaml\n|\Z)", re.DOTALL | re.MULTILINE)
_OPTLINE = re.compile(r"^- \(([a-d])\) (.*)$", re.MULTILINE)


def load_md(text: str) -> PaperDoc:
    fm = _FM.match(text)
    meta = yaml.safe_load(fm.group(1)) if fm else {}
    questions: list[Question] = []
    for m in _QBLOCK.finditer(text):
        d = yaml.safe_load(m.group(2))
        body = m.group(3).strip()
        raw = ""
        rm = re.search(r"\*\*Raw text \(unparsed\):\*\*\n```text\n(.*?)\n```", body, re.DOTALL)
        if rm:
            raw, body = rm.group(1), body[: rm.start()].strip()
        stem = body.removeprefix("**Question.**")
        cut = re.search(r"\n\n- \(", stem)
        options: dict[str, str] = {}
        if cut:
            if d["phase"] == "prelims":
                options = {k: v for k, v in _OPTLINE.findall(stem[cut.start():])}
            stem = stem[: cut.start()]
        questions.append(Question(
            id=d["id"], phase=d["phase"], year=d["year"], paper=d["paper"], number=d["number"], page=d.get("page"),
            stem=stem.strip(), options=options, marks=d.get("marks"), negative_marks=d.get("negative_marks"),
            word_limit=d.get("word_limit"), section=d.get("section"), parts=d.get("parts") or [],
            answer=d.get("answer"), answer_source=d.get("answer_source", "none"),
            suggested_answer=d.get("suggested_answer"), status=d.get("status", "parsed"),
            tags=d.get("tags") or [], raw_text=raw))
    return PaperDoc(meta, questions)
