"""Scenarios: review sample and explicit verification."""
from __future__ import annotations

import pytest
from helpers import doc_from

from pyq.render import load_md, render_md
from pyq.review import make_review_sample, verify_questions


def test_review_sample_contains_all_failed_and_about_ten_percent(make_pdf):
    doc, pages = doc_from(make_pdf, n=50, broken=6)
    md = make_review_sample([doc], {doc.key(): pages}, seed=13, fraction=0.10)
    assert "PRE-2024-GS1-006" in md
    shown = md.count("### PRE-2024-GS1-")
    assert 1 + 5 <= shown <= 1 + 5 + 1  # failed + ~10% of the 49 others (ceil)
    assert md == make_review_sample([doc], {doc.key(): pages}, seed=13, fraction=0.10)  # deterministic


def test_verify_sets_status_updates_count_and_refuses_failed(make_pdf, tmp_path):
    doc, _ = doc_from(make_pdf, n=10, broken=6)
    path = tmp_path / "gs-paper-1.md"
    path.write_text(render_md(doc), encoding="utf-8")
    changed = verify_questions(path, ["PRE-2024-GS1-001", "PRE-2024-GS1-002"])
    assert changed == 2
    back = load_md(path.read_text(encoding="utf-8"))
    assert back.meta["verified_count"] == 2
    assert {q.id: q.status for q in back.questions}["PRE-2024-GS1-001"] == "verified"
    with pytest.raises(ValueError):
        verify_questions(path, ["PRE-2024-GS1-006"])  # failed parse cannot be verified
