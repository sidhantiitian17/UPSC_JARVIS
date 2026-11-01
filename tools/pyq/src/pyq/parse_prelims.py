"""OCR-tolerant Prelims MCQ segmentation. Heuristic; accuracy on REAL UPSC PDFs is unverified (Phase 0
exit gate requires an owner spot-check). Never repairs silently: anything not cleanly segmentable becomes `failed`
with its raw text.

Method (not "find 1., 2., 3. in order", which one lost digit derails): locate every complete option group
(a)(b)(c)(d) first; the text between two groups holds the last option's tail and the next stem. A question is
`parsed` only if its own number, stem and four options were all found; a lost number, a misread option letter or
an unclear boundary fails that one question and parsing continues.
"""
from __future__ import annotations

import itertools
import re

from pyq.extract import PageText, clean_text, page_for
from pyq.models import PaperDoc, Question, base_meta, make_id

# Text layers and OCR garble the markers: "( d)", "{b)", "fa)", "jc}", "(6)", "(dq)" and junk before numbers.
# A marker is judged by its position in the group (1st..4th), not only by its letter.
_MARKER = re.compile(r"^[\s.'|!:;,~_-]*(?:[A-Za-z]{1,2}\s+)?[(\[{|fFjJiIl!]?\s*([A-Za-z@¢©&0-9]{1,2})\s*[)}\]]\s*(.*)$")
_POSITION_TOKENS = (
    frozenset({"a", "A", "@"}),
    frozenset({"b", "B", "6", "h"}),
    frozenset({"c", "C", "¢", "e", "ec", "cc", "©", "o"}),
    frozenset({"d", "D", "a", "q", "dq", "cl", "qd", "da"}),
)
_ANY_TOKEN = frozenset().union(*_POSITION_TOKENS)
# OCR turns digits into lookalikes: "ll." (11), "1Z." (12), "14," (14). A capital "I" is never a digit (Roman numerals).
_NUM = re.compile(r"^\s*(?:[^\W\d_]{1,2}\s+|[|!'.,]\s*)?([0-9lO|oZ]{1,3})[.,]\s+(\S.*)$")
_DIGIT_LOOKALIKES = str.maketrans("lO|oZ", "11002")
_MARKS = re.compile(r"carries?\s+(\d+(?:\.\d+)?)\s+marks?", re.IGNORECASE)
_LETTERS = "abcd"
_MAX_GROUP_SPAN = 60  # lines between (a) and (d)
_Q1_WINDOW = 1500  # Question 1 must start within this many characters of its first option
_MAX_TAIL_LINES = 4  # wrapped lines allowed after option (d)
_MAX_RESYNC = 3  # a number may skip ahead by this many, but only if the NEXT question confirms it


def clean_block(s: str) -> str:
    lines = [ln.rstrip() for ln in s.strip().splitlines()]
    out: list[str] = []
    for ln in lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln)
    return "\n".join(out).strip()


def _num(v: str) -> float | int:
    f = float(v)
    return int(f) if f.is_integer() else f


def _marker(line: str) -> tuple[str, str] | None:
    """(marker token, text after it) if the line starts like an option line, else None."""
    m = _MARKER.match(line)
    return (m.group(1), m.group(2)) if m and m.group(1) in _ANY_TOKEN else None


def _number(line: str) -> tuple[int, str] | None:
    """(question number, text after it) if the line starts with a number the OCR may have garbled."""
    m = _NUM.match(line)
    return (int(m.group(1).translate(_DIGIT_LOOKALIKES)), m.group(2)) if m else None


def _find_groups(lines: list[str]) -> list[tuple[int, int, int, int]]:
    """Complete groups of four option markers in order (each marker must fit its position); any other sequence
    is not a group."""
    groups: list[tuple[int, int, int, int]] = []
    i = 0
    while i < len(lines):
        m = _marker(lines[i])
        if not (m and m[0] in _POSITION_TOKENS[0]):
            i += 1
            continue
        idx, want, j = [i], 1, i + 1
        while j < len(lines) and j - i <= _MAX_GROUP_SPAN and want < 4:
            mm = _marker(lines[j])
            if mm:
                if mm[0] not in _POSITION_TOKENS[want]:
                    break
                idx.append(j)
                want += 1
            elif _number(lines[j]):  # a numbered line is the next stem: a group never crosses it
                break
            j += 1
        if want == 4:
            groups.append((idx[0], idx[1], idx[2], idx[3]))
            i = idx[3] + 1
        else:
            i += 1
    return groups


def _tail(lines: list[str], d_idx: int) -> tuple[list[str], int, bool]:
    """Lines that continue option (d): up to a blank line, a numbered line or an option marker.
    Returns (tail lines, index of the first line after it, ambiguous)."""
    out: list[str] = []
    j = d_idx + 1
    while j < len(lines):
        ln = lines[j]
        if not ln.strip() or _number(ln) or _marker(ln):
            return out, j, False
        if len(out) >= _MAX_TAIL_LINES:
            return out, j, True  # no gap and no number: cannot tell where the next stem starts
        out.append(ln)
        j += 1
    return out, j, False


def _is_statement_run(lines: list[str], lo: int, hi: int, v: int) -> bool:
    """True if lines[lo:hi] hold no option marker and their numbered lines count up to v-1 (e.g. "2.", "3." before
    "4."): then line `hi` is another statement of the question above, whose first "1." was misread ("k Claim")."""
    if any(_marker(lines[k]) for k in range(lo, hi)):
        return False
    nums = [n[0] for n in (_number(lines[k]) for k in range(lo, hi)) if n]
    return bool(nums) and nums[-1] == v - 1 and all(b == a + 1 for a, b in itertools.pairwise(nums))


def _starts(lines: list[str], lo: int, hi: int, expected: int) -> list[tuple[int, int]]:
    """Question-number lines in lines[lo:hi] as (line index, number). A numbered statement run that begins at
    "1." is never a question start, even if one of its numbers equals the expected question number."""
    starts: list[tuple[int, int]] = []
    exp, run = expected, None
    for i in range(lo, hi):
        n = _number(lines[i])
        if not n:
            continue
        v = n[0]
        if v == 1 and not (exp == 1 and not starts):
            run = 1
            continue
        if run is not None and v == run + 1:
            run = v
            continue
        run = None
        if v == exp:  # no jumps: a misread digit ("93." read as "98.") must not shift every later number
            if starts and _is_statement_run(lines, starts[-1][0] + 1, i, v):
                continue
            starts.append((i, v))
            exp = v + 1
    return starts


def _first_question_lo(lines: list[str], first_a: int) -> int:
    """Skip numbered exam instructions: Question 1 starts at a "1." close to the first option group."""
    for i in range(first_a):
        n = _number(lines[i])
        if n and n[0] == 1 and sum(len(ln) + 1 for ln in lines[i:first_a]) < _Q1_WINDOW:
            return i
    return 0


def _option_text(chunk: list[str]) -> str:
    first = _marker(chunk[0])
    return " ".join(" ".join([first[1] if first else chunk[0], *chunk[1:]]).split())


def parse_prelims(pages: list[PageText], year: int, paper: str) -> PaperDoc:
    text, page_starts = clean_text(pages)
    head = clean_text(pages[:3])[0]
    mm = _MARKS.search(head)
    marks = _num(mm.group(1)) if mm else None
    lines = text.split("\n")
    offsets, off = [], 0
    for ln in lines:
        offsets.append(off)
        off += len(ln) + 1

    def question(n: int, at: int) -> Question:
        return Question(id=make_id("prelims", year, paper, n), phase="prelims", year=year, paper=paper, number=n,
                        page=page_for(page_starts, offsets[min(at, len(lines) - 1)]), marks=marks)

    def failed(n: int, at: int, raw: list[str]) -> Question:
        q = question(n, at)
        q.status, q.raw_text = "failed", "\n".join(raw).strip()
        return q

    questions: list[Question] = []
    groups = _find_groups(lines)
    lo, expected, force_fail = 0, 1, False
    for k, (a, b, c, d) in enumerate(groups):
        if k == 0:
            lo = _first_question_lo(lines, a)
        tail, after, ambiguous = _tail(lines, d)
        starts = _starts(lines, lo, a, expected)
        if not starts and k + 1 < len(groups):  # a whole question may be lost: resync only if the next one confirms
            for j in range(1, _MAX_RESYNC + 1):
                cand = _starts(lines, lo, a, expected + j)
                nxt = _starts(lines, d + 1 if ambiguous else after, groups[k + 1][0], cand[-1][1] + 1) if cand else []
                if cand and nxt:
                    starts = cand
                    break
        for (s, v), (s2, _) in itertools.pairwise(starts):  # earlier starts: questions without options
            questions.append(failed(v, s, lines[s:s2]))
        if starts:
            s, n = starts[-1]
        else:
            s, n = lo, expected
        if starts and not force_fail and not ambiguous:
            q = question(n, s)
            first = _number(lines[s])
            q.stem = clean_block("\n".join([first[1], *lines[s + 1 : a]]))
            pieces = [lines[a:b], lines[b:c], lines[c:d], [lines[d], *tail]]
            q.options = {letter: _option_text(chunk) for letter, chunk in zip(_LETTERS, pieces, strict=True)}
            if not all(q.options.values()):  # an option whose text was not recognised
                q = failed(n, s, [*lines[s:a], *lines[a : d + 1], *tail])
        else:
            q = failed(n, s, [*lines[s:a], *lines[a : d + 1], *tail])
        questions.append(q)
        expected = n + 1
        force_fail = ambiguous
        lo = d + 1 if ambiguous else after
    return PaperDoc(base_meta("prelims", year, paper, len(questions)), questions)
