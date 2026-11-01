"""Scenarios: markdown dataset round-trip and re-run identity."""
from __future__ import annotations

import hashlib

from helpers import doc_from

from pyq.render import load_md, render_md


def test_markdown_roundtrip_is_lossless_for_fields(make_pdf):
    doc, _ = doc_from(make_pdf)
    back = load_md(render_md(doc))
    assert [q.id for q in back.questions] == [q.id for q in doc.questions]
    assert back.questions[0].options == doc.questions[0].options
    assert back.questions[0].stem == doc.questions[0].stem
    assert back.meta["question_count"] == 20 and back.meta["verified_count"] == 0


def test_rerun_produces_identical_hashes(make_pdf):
    d1, _ = doc_from(make_pdf)
    d2, _ = doc_from(make_pdf)
    h = lambda d: hashlib.sha256(render_md(d).encode()).hexdigest()
    assert h(d1) == h(d2)
