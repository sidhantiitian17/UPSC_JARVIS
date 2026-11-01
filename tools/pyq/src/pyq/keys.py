"""Answer keys: ONLY from official sources. LLM guesses belong in `suggested_answer`, never in `answer`."""
from __future__ import annotations

import re

from pyq.extract import PageText
from pyq.fetch import is_official
from pyq.models import PaperDoc


class KeyError_(Exception):
    pass


_ROW = re.compile(r"(?<![\w.])(\d{1,3})\s*[-:.)]?\s+([A-Da-d])(?![\w])")


def parse_answer_key(pages: list[PageText]) -> dict[int, str]:
    key: dict[int, str] = {}
    for p in pages:
        for m in _ROW.finditer(p.text):
            n, letter = int(m.group(1)), m.group(2).lower()
            if n in key and key[n] != letter:
                raise KeyError_(f"conflicting answers for question {n}")
            key[n] = letter
    return key


def apply_key(doc: PaperDoc, key: dict[int, str], source_url: str) -> int:
    if not is_official(source_url):
        raise KeyError_(f"refusing answer key from non-official source: {source_url}")
    applied = 0
    for q in doc.questions:
        if q.number in key:
            q.answer, q.answer_source = key[q.number], "official-key"
            applied += 1
    return applied
