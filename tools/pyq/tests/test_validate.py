"""Scenarios: validation rules, coverage report, repository safety."""
from __future__ import annotations

from pathlib import Path

from helpers import doc_from

from pyq.validate import coverage_report, validate_doc


def test_validation_passes_clean_doc_and_flags_problems(make_pdf):
    doc, pages = doc_from(make_pdf, n=20)
    issues = validate_doc(doc, pages)
    assert [i for i in issues if i.level == "error"] == []
    assert any(i.code == "count-mismatch" and i.level == "warning" for i in issues)  # 20 != expected 100
    doc.questions[3].number = 99  # break continuity
    doc.questions[4].options.pop("d")
    codes = {i.code for i in validate_doc(doc, pages) if i.level == "error"}
    assert {"continuity", "options"} <= codes
    doc.questions[5].stem = "text that is not in the source"
    assert "not-in-source" in {i.code for i in validate_doc(doc, pages)}


def test_failed_questions_appear_in_coverage_report(make_pdf):
    doc, _pages = doc_from(make_pdf, n=10, broken=6)
    rep = coverage_report([doc], manifest=[])
    assert "PRE-2024-GS1-006" in rep and "failed" in rep


def test_public_repo_safety_raw_pdfs_are_gitignored():
    root = Path(__file__).resolve().parents[3]
    lines = [ln.strip() for ln in (root / ".gitignore").read_text().splitlines()]
    assert "datasets/pyq/raw/" in lines
