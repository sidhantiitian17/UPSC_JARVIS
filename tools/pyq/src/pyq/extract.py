from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pdfplumber


class ExtractError(RuntimeError):
    pass


@dataclass
class PageText:
    number: int
    text: str


_MAX_CROSSING_SHARE = 0.03  # words straddling the midline before a page counts as full width
_MIN_COLUMN_SHARE = 0.2


def _is_two_column(words: list[dict], mid: float) -> bool:
    if len(words) < 20:
        return False
    crossing = sum(1 for w in words if w["x0"] < mid < w["x1"])
    left = sum(1 for w in words if w["x1"] <= mid)
    right = sum(1 for w in words if w["x0"] >= mid)
    n = len(words)
    return crossing / n <= _MAX_CROSSING_SHARE and left / n >= _MIN_COLUMN_SHARE and right / n >= _MIN_COLUMN_SHARE


def _page_text(page) -> str:
    """Two-column pages are read left column first, then right; others top to bottom."""
    mid = page.width / 2
    if not _is_two_column(page.extract_words(), mid):
        return page.extract_text() or ""
    left = page.crop((0, 0, mid, page.height)).extract_text() or ""
    right = page.crop((mid, 0, page.width, page.height)).extract_text() or ""
    return left + "\n" + right


def extract_pdf(path: Path) -> list[PageText]:
    with pdfplumber.open(str(path)) as pdf:
        return [PageText(i + 1, _page_text(p)) for i, p in enumerate(pdf.pages)]


def is_scanned(pages: list[PageText], min_chars: int = 50, share: float = 0.5) -> bool:
    if not pages:
        return False
    empty = sum(1 for p in pages if len(p.text.strip()) < min_chars)
    return empty / len(pages) >= share


def detect_lang(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    dev = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    return "hi" if dev / len(letters) > 0.3 else "en"


def normalize_ws(s: str) -> str:
    return " ".join(s.split())


_WINDOWS_TESSERACT = [
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
]
OCR_DPI = 300


def find_tesseract() -> str:
    """TESSERACT_CMD, then PATH, then the usual Windows install folders."""
    env = os.environ.get("TESSERACT_CMD")
    if env and Path(env).exists():
        return env
    found = shutil.which("tesseract")
    if found:
        return found
    for cand in _WINDOWS_TESSERACT:
        if cand.exists():
            return str(cand)
    raise ExtractError("tesseract is not installed (winget install UB-Mannheim.TesseractOCR) or set TESSERACT_CMD")


def tesseract_runner(exe: str, lang: str = "eng") -> Callable[[Path], str]:
    def run(png: Path) -> str:
        res = subprocess.run([exe, str(png), "stdout", "-l", lang, "--psm", "3"], capture_output=True,
                             text=True, encoding="utf-8", check=False)
        if res.returncode != 0:
            raise ExtractError(f"tesseract failed on {png.name}: {res.stderr.strip()[:200]}")
        return res.stdout
    return run


def ocr_pages(path: Path, runner: Callable[[Path], str] | None = None, dpi: int = OCR_DPI) -> list[PageText]:
    """OCR every page of a (scanned) PDF: render to PNG with pdfplumber, read with the Tesseract CLI."""
    runner = runner or tesseract_runner(find_tesseract())
    pages: list[PageText] = []
    with pdfplumber.open(str(path)) as pdf, tempfile.TemporaryDirectory() as tmp:
        for i, page in enumerate(pdf.pages):
            png = Path(tmp) / f"page-{i + 1:03d}.png"
            page.to_image(resolution=dpi).original.save(png)
            pages.append(PageText(i + 1, runner(png)))
    return pages


_NOISE = [
    re.compile(r"^\s*Test Booklet Series\b", re.IGNORECASE),
    re.compile(r"^\s*www\.upsc\.gov\.in\s*$", re.IGNORECASE),
    re.compile(r"^\s*Page\s+\d+(\s+of\s+\d+)?\s*$", re.IGNORECASE),
]


def clean_text(pages: list[PageText]) -> tuple[str, list[tuple[int, int]]]:
    """Join pages into one text, dropping header/footer noise lines.
    Returns (text, [(start_offset, page_number)])."""
    out: list[str] = []
    starts: list[tuple[int, int]] = []
    offset = 0
    for p in pages:
        starts.append((offset, p.number))
        lines = [ln.rstrip() for ln in p.text.splitlines() if not any(rx.match(ln) for rx in _NOISE)]
        chunk = "\n".join(lines) + "\n"
        out.append(chunk)
        offset += len(chunk)
    return "".join(out), starts


def page_for(starts: list[tuple[int, int]], offset: int) -> int | None:
    page = None
    for start, number in starts:
        if start <= offset:
            page = number
        else:
            break
    return page


def save_pages(path: Path, pages: list[PageText], **extra) -> None:
    data = {"pages": [{"number": p.number, "text": p.text} for p in pages], **extra}
    Path(path).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8", newline="\n")


def load_pages(path: Path) -> tuple[list[PageText], dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [PageText(p["number"], p["text"]) for p in data["pages"]], {k: v for k, v in data.items() if k != "pages"}
