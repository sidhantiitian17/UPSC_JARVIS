"""Scenarios: answers come only from official keys or the owner."""
from __future__ import annotations

import pytest
from helpers import doc_from

from pyq.extract import PageText
from pyq.keys import KeyError_, apply_key, parse_answer_key
from pyq.validate import validate_doc

KEY_TEXT = "Q.No. Answer\n1 B\n2 d\n3 A\n"


def test_official_key_applied_only_from_official_host(make_pdf):
    doc, _ = doc_from(make_pdf, n=3)
    key = parse_answer_key([PageText(1, KEY_TEXT)])
    assert key == {1: "b", 2: "d", 3: "a"}
    apply_key(doc, key, source_url="https://upsc.gov.in/keys/k.pdf")
    assert [q.answer for q in doc.questions] == ["b", "d", "a"]
    assert all(q.answer_source == "official-key" for q in doc.questions)
    doc2, _ = doc_from(make_pdf, n=3)
    with pytest.raises(KeyError_):
        apply_key(doc2, key, source_url="https://coaching.example.com/key.pdf")
    assert all(q.answer is None and q.answer_source == "none" for q in doc2.questions)


def test_llm_guess_lives_only_in_suggested_answer(make_pdf):
    doc, _ = doc_from(make_pdf, n=2)
    doc.questions[0].suggested_answer = "c"
    issues = validate_doc(doc, None)
    assert doc.questions[0].answer is None and doc.questions[0].answer_source == "none"
    assert not [i for i in issues if i.level == "error"]
    doc.questions[0].answer = "c"  # answer without a legitimate source must be rejected
    assert "answer-source" in {i.code for i in validate_doc(doc, None) if i.level == "error"}
