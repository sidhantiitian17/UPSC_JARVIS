"""Mains / Essay / Sociology (optional) question segmentation. Heuristic; real-PDF accuracy unverified.
Marks are read from trailing numbers or '[10 marks]' and MUST be spot-checked by the owner."""
from __future__ import annotations

import re

from pyq.extract import PageText, clean_text, page_for
from pyq.models import PaperDoc, Question, base_meta, make_id
from pyq.parse_prelims import clean_block

_SECTION = re.compile(r"(?im)^\s*SECTION\s*[-–:]?\s*['‘\"’]?([AB])['’\"]?\b")
_PART = re.compile(r"(?m)^[ \t]*\(([a-h])\)[ \t]+")
_WORDS = re.compile(r"(\d{2,3})\s*words", re.IGNORECASE)
_TRAIL = [
    re.compile(r"\[(\d{1,2}(?:\.\d+)?)\s*marks?\]\s*$", re.IGNORECASE),
    re.compile(r"(?:\s|\()(\d{1,2}(?:\.\d+)?)\)?\s*$"),
]


def _qstart(n: int) -> re.Pattern:
    return re.compile(rf"(?m)^[ \t]*(?:Q\.?[ \t]*)?{n}[.)][ \t]+(?=\S)")


def split_trailing_marks(s: str) -> tuple[float | int | None, str]:
    s = s.strip()
    for rx in _TRAIL:
        m = rx.search(s)
        if m:
            v = float(m.group(1))
            return (int(v) if v.is_integer() else v), s[: m.start()].rstrip()
    return None, s


def parse_mains(pages: list[PageText], year: int, paper: str) -> PaperDoc:
    phase = "optional" if paper.startswith("sociology") else "mains"
    text, starts = clean_text(pages)
    headers = [(m.start(), m.group(1).upper()) for m in _SECTION.finditer(text)]
    questions: list[Question] = []
    pos, n = 0, 1
    while True:
        m = _qstart(n).search(text, pos)
        if not m:
            break
        nxt = _qstart(n + 1).search(text, m.end())
        end = nxt.start() if nxt else len(text)
        block = "\n".join(ln for ln in text[m.end():end].splitlines() if not _SECTION.match(ln))
        q = Question(id=make_id(phase, year, paper, n), phase=phase, year=year, paper=paper, number=n,
                     page=page_for(starts, m.start()))
        sec = [letter for off, letter in headers if off < m.start()]
        q.section = sec[-1] if sec else None
        w = _WORDS.search(block)
        q.word_limit = int(w.group(1)) if w else None
        parts = list(_PART.finditer(block))
        if parts:
            q.stem = clean_block(block[: parts[0].start()])
            for i, pm in enumerate(parts):
                body = block[pm.end(): parts[i + 1].start() if i + 1 < len(parts) else len(block)]
                marks, txt = split_trailing_marks(body)
                q.parts.append({"label": pm.group(1), "marks": marks, "text": " ".join(txt.split())})
            ms = [p["marks"] for p in q.parts]
            q.marks = sum(ms) if all(x is not None for x in ms) else None
        else:
            q.marks, txt = split_trailing_marks(block)
            q.stem = clean_block(txt)
        questions.append(q)
        pos, n = end, n + 1
    return PaperDoc(base_meta(phase, year, paper, len(questions)), questions)
