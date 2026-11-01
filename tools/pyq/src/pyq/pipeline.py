"""Offline stages over an output directory (default datasets/pyq): extract -> parse -> validate -> review."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pyq.extract import (
    OCR_VERSION,
    PageText,
    detect_lang,
    extract_pdf,
    is_scanned,
    load_pages,
    ocr_pages,
    save_pages,
)
from pyq.manifest import SourceRecord, load_manifest
from pyq.models import PaperDoc
from pyq.ocr_layout import is_english_page
from pyq.parse_mains import parse_mains
from pyq.parse_prelims import parse_prelims
from pyq.render import load_md, md_path, render_md
from pyq.review import make_review_sample
from pyq.validate import Issue, coverage_report, validate_doc

READY = ("downloaded", "unchanged")


def doc_phase(rec: SourceRecord) -> str:
    return "optional" if (rec.paper or "").startswith("sociology") else rec.phase


def _ready(out: Path) -> list[SourceRecord]:
    return [r for r in load_manifest(out / "manifest.jsonl")
            if r.status in READY and r.local_path and r.paper and r.year and (out / r.local_path).exists()]


def pages_path(out: Path, rec: SourceRecord) -> Path:
    return (out / rec.local_path).with_suffix(".pages.json")


def _already_ocred(path: Path, rec: SourceRecord) -> bool:
    if not path.exists():
        return False
    _, info = load_pages(path)
    return bool(info.get("ocr")) and info.get("source_sha256") == rec.sha256 and info.get("ocr_version") == OCR_VERSION


def extract_all(out: Path, ocr: bool = False, ocr_runner: Callable[[Path], str] | None = None,
                only: str | None = None) -> list[str]:
    """`only` keeps records whose local_path contains the substring (e.g. "2024/prelims")."""
    notes: list[str] = []
    for rec in _ready(out):
        if only and only not in rec.local_path.replace("\\", "/"):
            continue
        pdf = out / rec.local_path
        target = pages_path(out, rec)
        if _already_ocred(target, rec):  # never downgrade existing OCR text, with or without --ocr
            continue
        pages = extract_pdf(pdf)
        scanned = is_scanned(pages)
        ocred = False
        if scanned and ocr:
            pages = ocr_pages(pdf, runner=ocr_runner)
            ocred = True
            scanned = is_scanned(pages)
        if not scanned and not ocred:  # text layer: Hindi pages of a bilingual booklet come out garbled
            pages = [PageText(p.number, p.text if is_english_page(p.text) else "") for p in pages]
        blank = [p.number for p in pages if not p.text.strip()] if (ocred or not scanned) else []
        if blank:
            notes.append(f"{rec.url}: {len(blank)} page(s) blank or not English (e.g. Hindi pages): {blank[:12]}")
        scanned = scanned and not (ocred and len(blank) < len(pages))
        if scanned:
            notes.append(f"{rec.url}: scanned PDF, no text layer (run with --ocr after installing tesseract)")
        lang = detect_lang(" ".join(p.text for p in pages[:5])[:5000])
        save_pages(target, pages, scanned=scanned, ocr=ocred, ocr_version=OCR_VERSION if ocred else None,
                   blank_pages=blank, lang=lang, source_sha256=rec.sha256)
    return notes


def parse_all(out: Path) -> list[str]:
    notes: list[str] = []
    for rec in _ready(out):
        pp = pages_path(out, rec)
        if not pp.exists():
            notes.append(f"{rec.url}: not extracted yet")
            continue
        pages, info = load_pages(pp)
        if info.get("scanned"):
            notes.append(f"{rec.url}: skipped (scanned PDF)")
            continue
        if info.get("lang") == "hi":
            notes.append(f"{rec.url}: skipped (text is Hindi although listed as English)")
            continue
        if rec.phase == "prelims":
            doc = parse_prelims(pages, rec.year, rec.paper)
        else:
            doc = parse_mains(pages, rec.year, rec.paper)
        doc.meta.update(source_url=rec.url, source_sha256=rec.sha256, retrieved_at=rec.retrieved_at,
                        page_count=len(pages), lang="en")
        dest = md_path(out, doc.meta)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_md(doc), encoding="utf-8", newline="\n")
    return notes


def load_docs(out: Path) -> list[PaperDoc]:
    return [load_md(p.read_text(encoding="utf-8")) for p in sorted((out / "md").rglob("*.md"))]


def pages_by_key(out: Path) -> dict[str, list[PageText]]:
    res: dict[str, list[PageText]] = {}
    for rec in _ready(out):
        pp = pages_path(out, rec)
        if pp.exists():
            res[f"{doc_phase(rec)}/{rec.year}/{rec.paper}"] = load_pages(pp)[0]
    return res


def validate_all(out: Path) -> tuple[list[PaperDoc], dict[str, list[Issue]]]:
    docs, by_key = load_docs(out), pages_by_key(out)
    issues = {d.key(): validate_doc(d, by_key.get(d.key())) for d in docs}
    rep = out / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    (rep / "coverage.md").write_text(coverage_report(docs, load_manifest(out / "manifest.jsonl")),
                                     encoding="utf-8", newline="\n")
    return docs, issues


def review_all(out: Path, seed: int = 13, fraction: float = 0.10) -> Path:
    docs = load_docs(out)
    rep = out / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    dest = rep / "review-sample.md"
    dest.write_text(make_review_sample(docs, pages_by_key(out), seed, fraction), encoding="utf-8", newline="\n")
    return dest
