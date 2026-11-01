"""Scenarios: extraction, scanned detection, language detection."""
from __future__ import annotations

from conftest import paginate

from pyq.extract import PageText, detect_lang, extract_pdf, is_scanned


def test_extract_pdf_gives_page_numbers_and_text(make_pdf):
    pages = extract_pdf(make_pdf("p.pdf", paginate(["Hello world", "Second line"])))
    assert pages[0].number == 1 and "Hello world" in pages[0].text


def test_scanned_detection_flags_pages_without_text():
    pages = [PageText(1, ""), PageText(2, "  "), PageText(3, "x" * 400)]
    assert is_scanned(pages) is True
    assert is_scanned([PageText(1, "x" * 400), PageText(2, "y" * 400)]) is False


def test_language_detection_separates_hindi():
    assert detect_lang("This is an English question paper") == "en"
    assert detect_lang("यह एक हिन्दी प्रश्न पत्र है जिसमें कई प्रश्न हैं") == "hi"
