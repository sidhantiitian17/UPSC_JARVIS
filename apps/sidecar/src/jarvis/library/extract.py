"""PDF text extraction (pypdfium2: BSD-3-Clause/Apache-2.0) and chunking with exact page offsets."""

from __future__ import annotations

import re
from pathlib import Path

import pypdfium2 as pdfium

MAX_CHUNK_CHARS = 900
_PARA = re.compile(r"\n\s*\n")
_SENT = re.compile(r"(?<=[.!?])\s+")


class ExtractError(Exception):
    pass


def extract_pages(path: Path) -> list[str]:
    """Text of each page with line endings normalised to '\\n' (offsets refer to this exact text)."""
    try:
        pdf = pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError as e:
        raise ExtractError(f"could not read this PDF ({e})") from e
    try:
        pages: list[str] = []
        for page in pdf:
            textpage = page.get_textpage()
            try:
                pages.append(textpage.get_text_range().replace("\r\n", "\n").replace("\r", "\n"))
            finally:
                textpage.close()
                page.close()
        return pages
    finally:
        pdf.close()


def _hard_split(start: int, end: int, text: str, max_chars: int) -> list[tuple[int, int, str]]:
    out = []
    pos = start
    while pos < end:
        stop = min(pos + max_chars, end)
        if stop < end:  # prefer to break at whitespace
            ws = text.rfind(" ", pos + max_chars // 2, stop)
            if ws > pos:
                stop = ws
        piece = text[pos:stop]
        lead = len(piece) - len(piece.lstrip())
        trimmed = piece.strip()
        if trimmed:
            out.append((pos + lead, pos + lead + len(trimmed), trimmed))
        pos = stop
    return out


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[tuple[int, int, str]]:
    """Paragraph-aware chunks as (char_start, char_end, text) with text == page_text[char_start:char_end]."""
    chunks: list[tuple[int, int, str]] = []
    cursor = 0
    bounds = [(m.start(), m.end()) for m in _PARA.finditer(text)]
    segments = []
    for b_start, b_end in bounds:
        segments.append((cursor, b_start))
        cursor = b_end
    segments.append((cursor, len(text)))

    for seg_start, seg_end in segments:
        raw = text[seg_start:seg_end]
        lead = len(raw) - len(raw.lstrip())
        body = raw.strip()
        if not body:
            continue
        start = seg_start + lead
        end = start + len(body)
        if len(body) <= max_chars:
            chunks.append((start, end, body))
            continue
        # pack sentences greedily, contiguous spans only
        sentences = []
        pos = start
        for m in _SENT.finditer(text, start, end):
            sentences.append((pos, m.start()))
            pos = m.end()
        sentences.append((pos, end))
        cur_s, cur_e = None, None
        for s, e in sentences:
            if e - s > max_chars:
                if cur_s is not None:
                    chunks.append((cur_s, cur_e, text[cur_s:cur_e]))
                    cur_s = cur_e = None
                chunks.extend(_hard_split(s, e, text, max_chars))
            elif cur_s is None:
                cur_s, cur_e = s, e
            elif e - cur_s <= max_chars:
                cur_e = e
            else:
                chunks.append((cur_s, cur_e, text[cur_s:cur_e]))
                cur_s, cur_e = s, e
        if cur_s is not None:
            chunks.append((cur_s, cur_e, text[cur_s:cur_e]))
    return chunks
