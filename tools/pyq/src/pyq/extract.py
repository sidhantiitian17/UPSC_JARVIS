from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from PIL import Image, ImageOps

from pyq.ocr_layout import find_gutter, is_english_page, tsv_to_text


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
OCR_VERSION = 5  # bump when OCR changes so cached pages are redone (1 plain, 2 TSV+columns, 3 gutter+non-English, 4 white border, 5 psm 6 + upscale)
OCR_WORKERS = max(1, min(4, (os.cpu_count() or 2) // 2))  # Tesseract is single-threaded per process here
_CUT_PAD = 10  # px of overlap so a margin number at the cut is not clipped
OCR_BORDER = 60  # px of white around every image sent to Tesseract
OCR_SCALE = 4 / 3  # upscale before OCR: bold margin digits like "3." are misread as "8." at 300 dpi


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


def tesseract_runner(exe: str, lang: str = "eng", dpi: int = OCR_DPI) -> Callable[[Path], str]:
    """Run Tesseract on one image and rebuild reading-order lines from its word boxes (TSV)."""
    def run(png: Path) -> str:
        res = subprocess.run([exe, str(png), "stdout", "-l", lang, "--psm", "6", "--dpi", str(dpi), "tsv"],
                             capture_output=True, text=True, encoding="utf-8", check=False,
                             env={**os.environ, "OMP_THREAD_LIMIT": "1"})
        if res.returncode != 0:
            raise ExtractError(f"tesseract failed on {png.name}: {res.stderr.strip()[:200]}")
        return tsv_to_text(res.stdout)
    return run


def ocr_pages(path: Path, runner: Callable[[Path], str] | None = None, dpi: int = OCR_DPI) -> list[PageText]:
    """OCR every page of a (scanned) PDF: render to PNG with pdfplumber, read with the Tesseract CLI.
    Two-column pages (clear vertical gutter) are cut in two and read left column first."""
    runner = runner or tesseract_runner(find_tesseract(), dpi=round(dpi * OCR_SCALE))
    with pdfplumber.open(str(path)) as pdf, tempfile.TemporaryDirectory() as tmp:
        jobs: list[list[Path]] = []  # per page: its image file(s), left column first
        for i, page in enumerate(pdf.pages):
            img = page.to_image(resolution=dpi).original
            gutter = find_gutter(img)
            stem = f"page-{i + 1:03d}"
            if gutter is None:
                parts = [(stem, img)]
            else:
                parts = [(f"{stem}-c1", img.crop((0, 0, gutter, img.height))),
                         (f"{stem}-c2", img.crop((max(0, gutter - _CUT_PAD), 0, img.width, img.height)))]
            files = []
            for name, part in parts:
                png = Path(tmp) / f"{name}.png"
                # Tesseract misses glyphs that touch the image border (the margin question numbers)
                part = part.resize((round(part.width * OCR_SCALE), round(part.height * OCR_SCALE)), Image.Resampling.LANCZOS)
                ImageOps.expand(part, border=OCR_BORDER, fill="white").save(png)
                files.append(png)
            jobs.append(files)
        with ThreadPoolExecutor(max_workers=OCR_WORKERS) as pool:
            results = [[pool.submit(runner, f) for f in files] for files in jobs]
            pages = []
            for i, futs in enumerate(results):
                text = "\n".join(f.result() for f in futs)
                pages.append(PageText(i + 1, text if is_english_page(text) else ""))
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
