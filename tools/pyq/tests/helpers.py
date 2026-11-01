"""Shared synthetic-document helpers for tests (no real UPSC content)."""
from __future__ import annotations

from conftest import paginate, prelims_lines

from pyq.extract import extract_pdf
from pyq.parse_prelims import parse_prelims

SRC = {"source_url": "https://upsc.gov.in/x.pdf", "source_sha256": "ab" * 32, "retrieved_at": "2026-11-01T00:00:00Z"}


def doc_from(make_pdf, n=20, broken=None):
    pages = extract_pdf(make_pdf("d.pdf", paginate(prelims_lines(n, broken=broken))))
    doc = parse_prelims(pages, year=2024, paper="gs-paper-1")
    doc.meta.update(SRC, page_count=len(pages), lang="en")
    return doc, pages
