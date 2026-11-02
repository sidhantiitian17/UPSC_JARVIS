"""Offline fill-in-the-blank quiz built from the range itself (used when no LLM provider answers)."""

from __future__ import annotations

import random
import re

_SENT = re.compile(r"(?<=[.!?])\s+")
_CAP = re.compile(r"\b[A-Z][a-z]{3,}\b")
_NUM = re.compile(r"\b\d[\d,.]*\b")


def _sentences(chunks: list[dict]) -> list[tuple[int, str]]:
    out = []
    for c in chunks:
        flat = " ".join(c["text"].split())
        for s in _SENT.split(flat):
            words = s.split()
            if 7 <= len(words) <= 40:
                out.append((c["id"], s.strip()))
    return out


def _answer_term(sentence: str) -> tuple[str, str] | None:
    """(term, kind) to blank out: a number, else a capitalised word that is not the first word."""
    m = _NUM.search(sentence)
    if m:
        return m.group(0).rstrip(".,"), "num"
    for m in _CAP.finditer(sentence):
        if m.start() > 0:
            return m.group(0), "cap"
    return None


def cloze_questions(chunks: list[dict], n: int, seen_stems: set[str], seed: int) -> list[dict]:
    rng = random.Random(seed)
    candidates = []
    for chunk_id, sentence in _sentences(chunks):
        term = _answer_term(sentence)
        if term:
            candidates.append((chunk_id, sentence, term[0], term[1]))
    pools: dict[str, list[str]] = {"num": [], "cap": []}
    for _, _, term, kind in candidates:
        if term not in pools[kind]:
            pools[kind].append(term)

    out: list[dict] = []
    for _chunk_id, sentence, term, kind in candidates:
        if len(out) >= n:
            break
        distractors = [t for t in pools[kind] if t.casefold() != term.casefold()]
        if len(distractors) < 3:
            continue
        stem = "Fill in the blank: " + sentence.replace(term, "_____", 1)
        if stem.casefold() in seen_stems:
            continue
        options = [term, *rng.sample(distractors, 3)]
        rng.shuffle(options)
        out.append(
            {
                "stem": stem,
                "options": options,
                "answer_index": options.index(term),
                "explanation": f"From the text: {sentence}",
                "source_quote": sentence,
                "style": "recall",
            }
        )
        seen_stems.add(stem.casefold())
    return out
