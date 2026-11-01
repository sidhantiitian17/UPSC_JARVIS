from __future__ import annotations

import math
import os
import random
import re
from pathlib import Path

import yaml

from pyq.extract import PageText
from pyq.models import PaperDoc

_BLOCK = re.compile(r"(## Q\d+\n```yaml\n)(.*?)(\n```)", re.DOTALL)


def make_review_sample(docs: list[PaperDoc], pages_by_key: dict[str, list[PageText]], seed: int = 13,
                       fraction: float = 0.10) -> str:
    out = ["# Review sample", "",
           ("Compare the PARSED text with the SOURCE page text. If it is exact, run "
            "`uv run python -m pyq verify <id> [<id> ...]`. If not, fix the parser or edit the question."), ""]
    for d in sorted(docs, key=lambda d: d.key()):
        failed = [q for q in d.questions if q.status == "failed"]
        others = sorted((q for q in d.questions if q.status == "parsed"), key=lambda q: q.number)
        k = math.ceil(len(others) * fraction)
        picked = random.Random(f"{seed}:{d.key()}").sample(others, k) if others else []
        chosen = sorted(failed + picked, key=lambda q: q.number)
        out += [f"## {d.key()}  ({len(chosen)} to review of {len(d.questions)})", ""]
        pages = {p.number: p.text for p in pages_by_key.get(d.key(), [])}
        for q in chosen:
            out += [f"### {q.id}  (page {q.page}, status {q.status})", "", "**Parsed**", ""]
            if q.status == "failed":
                out += ["```text", q.raw_text, "```"]
            else:
                out += [q.stem, ""] + [f"- ({k}) {v}" for k, v in q.options.items()]
                out += [f"- ({p['label']}) {p['text']}  [{p['marks']}]" for p in q.parts]
            out += ["", "**Source page text**", "", "```text", pages.get(q.page, "(page text unavailable)"), "```", ""]
    return "\n".join(out) + "\n"


def verify_questions(path: Path, ids: list[str]) -> int:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    found: dict[str, tuple[int, int, dict]] = {}
    for m in _BLOCK.finditer(text):
        d = yaml.safe_load(m.group(2))
        found[d["id"]] = (m.start(2), m.end(2), d)
    for i in ids:
        if i not in found:
            raise ValueError(f"unknown question id: {i}")
        if found[i][2]["status"] == "failed":
            raise ValueError(f"{i} failed parsing and cannot be verified; fix it first")
    changed = 0
    for i in sorted(ids, key=lambda x: -found[x][0]):  # edit from the end so offsets stay valid
        s, e, d = found[i]
        if d["status"] == "verified":
            continue
        body = re.sub(r"(?m)^status: .*$", "status: verified", text[s:e])
        text = text[:s] + body + text[e:]
        changed += 1
    count = len(re.findall(r"(?m)^status: verified$", text))
    text = re.sub(r"(?m)^verified_count: \d+$", f"verified_count: {count}", text, count=1)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return changed
