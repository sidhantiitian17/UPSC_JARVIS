"""Scenarios: Prelims parsing keeps source text intact and flags failures."""
from __future__ import annotations

from conftest import paginate, prelims_lines

from pyq.extract import PageText, extract_pdf, normalize_ws
from pyq.parse_prelims import clean_text, parse_prelims


def pages_from(make_pdf, lines):
    return extract_pdf(make_pdf("p.pdf", paginate(lines)))


def test_parser_returns_100_questions_with_four_options_each(make_pdf):
    pages = pages_from(make_pdf, prelims_lines(100))
    doc = parse_prelims(pages, year=2024, paper="gs-paper-1")
    nums = [q.number for q in doc.questions]
    assert nums == list(range(1, 101))
    assert all(q.status == "parsed" for q in doc.questions)
    assert all(sorted(q.options) == ["a", "b", "c", "d"] for q in doc.questions)
    assert doc.questions[0].id == "PRE-2024-GS1-001" and doc.questions[99].id == "PRE-2024-GS1-100"


def test_numbered_statements_are_not_mistaken_for_question_numbers(make_pdf):
    pages = pages_from(make_pdf, prelims_lines(10, statements_in=4))
    doc = parse_prelims(pages, year=2024, paper="gs-paper-1")
    assert [q.number for q in doc.questions] == list(range(1, 11))
    q4 = doc.questions[3]
    assert "Statement 5 about topic 4" in q4.stem  # all five statements stayed inside Q4
    assert "topic 5, consider" in doc.questions[4].stem


def test_parsed_text_is_a_substring_of_source_text(make_pdf):
    pages = pages_from(make_pdf, prelims_lines(20))
    doc = parse_prelims(pages, year=2024, paper="gs-paper-1")
    source = normalize_ws(clean_text(pages)[0])
    for q in doc.questions:
        assert normalize_ws(q.stem) in source
        for text in q.options.values():
            assert normalize_ws(text) in source


def test_unsegmentable_question_is_flagged_not_repaired(make_pdf):
    pages = pages_from(make_pdf, prelims_lines(10, broken=6))
    doc = parse_prelims(pages, year=2024, paper="gs-paper-1")
    q6 = next(q for q in doc.questions if q.number == 6)
    assert q6.status == "failed" and "Answer unclear here" in q6.raw_text
    assert q6.options == {}
    assert [q.number for q in doc.questions] == list(range(1, 11))  # parsing continued


def test_marks_read_from_instructions_else_none(make_pdf):
    pages = pages_from(make_pdf, prelims_lines(3))
    assert parse_prelims(pages, year=2024, paper="gs-paper-1").questions[0].marks == 2
    no_marks = [PageText(1, "1. Q text\n(a) a\n(b) b\n(c) c\n(d) d\n")]
    assert parse_prelims(no_marks, year=2024, paper="csat").questions[0].marks is None


def test_answers_default_to_none_with_source_none(make_pdf):
    pages = pages_from(make_pdf, prelims_lines(3))
    for q in parse_prelims(pages, year=2024, paper="gs-paper-1").questions:
        assert q.answer is None and q.answer_source == "none" and q.suggested_answer is None
