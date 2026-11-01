"""Layout helpers for OCR: Tesseract word boxes -> reading-order lines, and column gutter detection.

Why: Tesseract often reports the small question number in the left margin as a separate block, so
plain text output loses the "12." that the parser needs at the start of a stem. Rebuilding lines from
word boxes by vertical position puts the number back on the line it belongs to.
"""
from __future__ import annotations

import itertools
import re
from statistics import median

from PIL import Image

MIN_CONF = 30.0  # words below this are junk (e.g. Hindi read by the English model)
_LINE_TOLERANCE = 0.6  # of the median word height
_GAP_FACTOR = 1.6  # a vertical gap above this many median line pitches is emitted as a blank line
_GUTTER_WINDOW = (0.35, 0.65)  # where a two-column gutter may sit (share of page width)
_MIN_GUTTER_SHARE = 0.015
_EMPTY_INK = 0.25  # a column is "empty" below this share of the strongest ink (margin numbers are faint)
_MIN_SIDE_INK = 0.2  # each side must hold this share of all inked columns


def _words(tsv: str) -> list[dict]:
    lines = tsv.splitlines()
    if len(lines) < 2:
        return []
    header = lines[0].split("\t")
    out: list[dict] = []
    for ln in lines[1:]:
        cells = ln.split("\t")
        if len(cells) < len(header):
            continue
        rec = dict(zip(header, cells, strict=False))
        if rec.get("level") != "5" or not rec.get("text", "").strip():
            continue
        try:
            conf = float(rec["conf"])
            box = (int(rec["left"]), int(rec["top"]), int(rec["width"]), int(rec["height"]))
        except ValueError:
            continue
        if conf < MIN_CONF:
            continue
        out.append({"left": box[0], "top": box[1], "h": box[3], "text": rec["text"].strip()})
    return out


def tsv_to_text(tsv: str) -> str:
    """Rebuild reading-order lines from Tesseract TSV word boxes (ignores Tesseract's own block order)."""
    words = _words(tsv)
    if not words:
        return ""
    tol = _LINE_TOLERANCE * median(w["h"] for w in words)
    lines: list[list[dict]] = []
    centres: list[float] = []
    for w in sorted(words, key=lambda w: (w["top"] + w["h"] / 2, w["left"])):
        cy = w["top"] + w["h"] / 2
        if lines and abs(cy - centres[-1]) <= tol:
            lines[-1].append(w)
            centres[-1] = sum(x["top"] + x["h"] / 2 for x in lines[-1]) / len(lines[-1])
        else:
            lines.append([w])
            centres.append(cy)
    texts = [" ".join(x["text"] for x in sorted(ln, key=lambda x: x["left"])) for ln in lines]
    if len(centres) < 3:
        return "\n".join(texts)
    pitch = median(b - a for a, b in itertools.pairwise(centres))
    out = [texts[0]]
    for gap, text in zip((b - a for a, b in itertools.pairwise(centres)), texts[1:], strict=True):
        if pitch > 0 and gap > _GAP_FACTOR * pitch:
            out.append("")  # layout gap: question / paragraph boundary
        out.append(text)
    return "\n".join(out)


_STOPWORDS = frozenset(
    ["the", "of", "and", "to", "in", "is", "are", "was", "were", "be", "been", "for", "with", "by", "on", "as", "at",
     "from", "that", "this", "which", "what", "who", "their", "its", "it", "or", "not", "no", "following",
     "statements", "statement", "given", "above", "below", "correct", "consider", "only", "both", "neither",
     "also", "have", "has", "had", "can", "may", "will", "shall", "would", "should", "one", "all", "any"]
)
_WORD = re.compile(r"[A-Za-z]{2,}")
_MIN_TOKENS_TO_JUDGE = 25
_MIN_STOPWORD_SHARE = 0.12


def is_english_page(text: str) -> bool:
    """False for pages that are not English (e.g. the Hindi pages of a bilingual booklet, which the English
    OCR model turns into Latin-looking junk with almost no real English words). Short pages are not judged."""
    tokens = [t.lower() for t in _WORD.findall(text)]
    if len(tokens) < _MIN_TOKENS_TO_JUDGE:
        return True
    return sum(1 for t in tokens if t in _STOPWORDS) / len(tokens) >= _MIN_STOPWORD_SHARE


def find_gutter(img: Image.Image) -> int | None:
    """x of the vertical white gutter of a two-column page, or None if the page is not two-column."""
    gray = img.convert("L")
    width = gray.width
    means = list(gray.resize((width, 1), Image.Resampling.BOX).tobytes())
    background = sorted(means)[int(0.95 * (width - 1))]
    ink = [max(0.0, background - m) for m in means]
    peak = sorted(ink)[int(0.9 * (width - 1))]
    if peak <= 0:
        return None
    empty = [v < _EMPTY_INK * peak for v in ink]
    inked = [i for i, e in enumerate(empty) if not e]
    if not inked:
        return None
    lo, hi = int(_GUTTER_WINDOW[0] * width), int(_GUTTER_WINDOW[1] * width)
    best: tuple[int, int] | None = None
    run_start: int | None = None
    for x in range(lo, hi + 1):
        if x < hi and empty[x]:
            run_start = x if run_start is None else run_start
            continue
        if run_start is not None and (best is None or x - run_start > best[1] - best[0]):
            best = (run_start, x)
        run_start = None
    if best is None or best[1] - best[0] < _MIN_GUTTER_SHARE * width:
        return None
    # Cut at the START of the empty run: a column of question numbers can sit right of the gutter and
    # is faint enough to count as "empty", so the middle of the run could land after those numbers.
    cut = best[0]
    left = sum(1 for i in inked if i < cut)
    right = len(inked) - left
    if left < _MIN_SIDE_INK * len(inked) or right < _MIN_SIDE_INK * len(inked):
        return None
    return cut
