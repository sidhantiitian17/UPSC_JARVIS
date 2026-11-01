"""Scenario: official syllabus keeps provenance and refuses non-official sources."""
from __future__ import annotations

import pytest

from pyq.extract import PageText
from pyq.syllabus import syllabus_to_md


def test_syllabus_requires_official_source_and_keeps_provenance():
    pages = [PageText(1, "Paper I: Sociology fundamentals"), PageText(2, "Paper II: India")]
    md = syllabus_to_md(pages, title="Sociology syllabus", source_url="https://upsc.gov.in/s.pdf",
                        sha256="cd" * 32, retrieved_at="2026-11-01T00:00:00Z")
    assert "source_url: \"https://upsc.gov.in/s.pdf\"" in md and "Paper II: India" in md
    with pytest.raises(ValueError):
        syllabus_to_md(pages, title="x", source_url="https://coaching.example.com/s.pdf", sha256="0", retrieved_at="t")
