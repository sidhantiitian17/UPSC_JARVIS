"""Deterministic Prelims MCQ segmentation. Heuristic; accuracy on REAL UPSC PDFs is unverified (Phase 0
exit gate requires an owner spot-check). Never repairs silently: unsegmentable questions become `failed`."""
from __future__ import annotations

import re

from pyq.extract import PageText, clean_text, page_for
from pyq.models import PaperDoc, Question, base_meta, make_id

_OPT = {k: re.compile(rf"(?m)(?:(?<=\s)|^)\({k}\)[ \t]*") for k in "abcd"}
_MARKS = re.compile(r"carries?\s+(\d+(?:\.\d+)?)\s+marks?", re.IGNORECASE)


def _qre(n: int) -> re.Pattern:
    return re.compile(rf"(?m)^[ \t]*{n}\.[ \t]+(?=\S)")


def clean_block(s: str) -> str:
    lines = [ln.rstrip() for ln in s.strip().splitlines()]
    out: list[str] = []
    for ln in lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln)
    return "\n".join(out).strip()


def _is_statement_run(text: str, s_end: int, cand_start: int, m: int) -> bool:
    """True if the candidate line `m.` merely continues a 1..m-1 numbered statement list of the current question."""
    j = 1
    for line in text[s_end:cand_start].splitlines():
        if j <= m - 1 and re.match(rf"^\s*{j}\.\s", line):
            j += 1
    return j > m - 1


def _find_start(text: str, n: int, pos: int):
    cands = list(_qre(n).finditer(text, pos))
    if n != 1:
        return cands[0] if cands else None
    for m in cands:  # skip numbered exam instructions: Q1 must be close to its first option
        a = _OPT["a"].search(text, m.end())
        if a and a.start() - m.end() < 1500:
            return m
    return cands[0] if cands else None


def _num(v: str) -> float | int:
    f = float(v)
    return int(f) if f.is_integer() else f


def parse_prelims(pages: list[PageText], year: int, paper: str) -> PaperDoc:
    text, starts = clean_text(pages)
    head = clean_text(pages[:3])[0]
    mm = _MARKS.search(head)
    marks = _num(mm.group(1)) if mm else None
    questions: list[Question] = []
    pos, n = 0, 1
    while True:
        m = _find_start(text, n, pos)
        if not m:
            break
        s_end = m.end()
        group = None
        a = _OPT["a"].search(text, s_end)
        if a:
            found, cur = [a], a.end()
            for k in "bcd":
                mo = _OPT[k].search(text, cur)
                if not mo:
                    found = None
                    break
                found.append(mo)
                cur = mo.end()
            group = found
        end, broken = len(text), False
        for c in _qre(n + 1).finditer(text, s_end):
            if group and c.start() > group[3].start():
                end = c.start()
                break
            if group and c.start() > group[0].start():
                continue  # inside this question's options
            if _is_statement_run(text, s_end, c.start(), n + 1):
                continue
            end, broken = c.start(), True
            break
        q = Question(id=make_id("prelims", year, paper, n), phase="prelims", year=year, paper=paper, number=n,
                     page=page_for(starts, m.start()), marks=marks)
        if group and not broken:
            q.stem = clean_block(text[s_end:group[0].start()])
            for i, k in enumerate("abcd"):
                s = group[i].end()
                e = group[i + 1].start() if i < 3 else end
                q.options[k] = " ".join(text[s:e].split())
        else:
            q.status = "failed"
            q.raw_text = text[s_end:end].strip()
        questions.append(q)
        pos, n = end, n + 1
    return PaperDoc(base_meta("prelims", year, paper, len(questions)), questions)
