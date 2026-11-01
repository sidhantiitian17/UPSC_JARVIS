"""Scenario: scanned PDFs are OCRed page by page when requested (Tesseract CLI, no extra Python deps)."""
from __future__ import annotations

import pytest
from conftest import write_pdf

from pyq import pipeline
from pyq.extract import ExtractError, extract_pdf, find_tesseract, load_pages, ocr_pages
from pyq.manifest import SourceRecord, save_manifest


class FakeRunner:
    def __init__(self):
        self.seen: list[str] = []

    def __call__(self, png) -> str:
        assert png.suffix == ".png" and png.stat().st_size > 1000
        self.seen.append(png.name)
        return f"OCR text for {png.stem} " + "question words " * 10


def test_ocr_pages_keeps_page_numbers_and_uses_runner(tmp_path):
    pdf = write_pdf(tmp_path / "blank.pdf", [[""], [""]])
    runner = FakeRunner()
    pages = ocr_pages(pdf, runner=runner)
    assert [p.number for p in pages] == [1, 2]
    assert all(p.text.startswith("OCR text for") for p in pages)
    assert len(runner.seen) == 2


def test_find_tesseract_fails_loudly_when_missing(monkeypatch):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr("pyq.extract.shutil.which", lambda _: None)
    monkeypatch.setattr("pyq.extract._WINDOWS_TESSERACT", [])
    with pytest.raises(ExtractError, match="tesseract"):
        find_tesseract()


def _scanned_manifest(tmp_path, write_pdf_fn):
    rel = "raw/2024/prelims/gs-paper-1-abc12345.pdf"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    write_pdf_fn(tmp_path / rel, [[""], [""]])
    save_manifest(tmp_path / "manifest.jsonl", [SourceRecord(
        url="https://www.upsc.gov.in/x.pdf", exam="cse", year=2024, phase="prelims", category="", title="t",
        paper="gs-paper-1", lang="en", status="downloaded", sha256="00", bytes=1, retrieved_at="t", local_path=rel)])
    return rel


def test_extract_all_ocr_is_cached_for_unchanged_files(tmp_path):
    rel = _scanned_manifest(tmp_path, write_pdf)
    runner = FakeRunner()
    notes = pipeline.extract_all(tmp_path, ocr=True, ocr_runner=runner)
    assert not any("scanned" in n for n in notes)
    pages, info = load_pages((tmp_path / rel).with_suffix(".pages.json"))
    assert info["ocr"] is True and info["scanned"] is False and "OCR text" in pages[0].text
    pipeline.extract_all(tmp_path, ocr=True, ocr_runner=runner)
    assert len(runner.seen) == 2  # second run reused the cache


def test_extract_all_only_filter_limits_files(tmp_path):
    _scanned_manifest(tmp_path, write_pdf)
    runner = FakeRunner()
    pipeline.extract_all(tmp_path, ocr=True, ocr_runner=runner, only="2019/")
    assert runner.seen == []


def test_real_tesseract_reads_rendered_text(tmp_path):
    try:
        find_tesseract()
    except ExtractError:
        pytest.skip("tesseract not installed")
    pdf = write_pdf(tmp_path / "t.pdf", [["Consider the following statements about Parliament"] * 12])
    assert extract_pdf(pdf)[0].text  # has a text layer; OCR must still read the rendered image
    text = ocr_pages(pdf)[0].text.lower()
    assert "parliament" in text and "statements" in text
