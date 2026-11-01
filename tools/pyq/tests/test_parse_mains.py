"""Scenarios: Mains/Essay/Sociology multi-part parsing."""
from __future__ import annotations

from pyq.extract import PageText
from pyq.parse_mains import parse_mains


def pages(text: str):
    return [PageText(1, text)]


SOC = """PAPER - I SOCIOLOGY
SECTION 'A'
1. Write short notes on each of the following in about 150 words each:
(a) Sociology as science 10
(b) Positivism and its critique 10
(c) Merton's middle range theory 10
2. Discuss the relationship between caste and class. 20
SECTION 'B'
3. Critically examine the role of the family in social change. 15
"""

GS = """1. Discuss the role of Vedic literature in shaping early society. (Answer in 150 words) 10
2. Examine the causes of the 1857 revolt. (Answer in 250 words) 15
"""


def test_sociology_parts_and_sections():
    doc = parse_mains(pages(SOC), year=2023, paper="sociology-1")
    q1, q2, q3 = doc.questions
    assert q1.id == "OPT-SOC-2023-SOC1-001"
    assert [p["label"] for p in q1.parts] == ["a", "b", "c"]
    assert [p["marks"] for p in q1.parts] == [10, 10, 10]
    assert q1.marks == 30 and q1.section == "A"
    assert q2.marks == 20 and q2.parts == [] and q2.section == "A"
    assert q3.section == "B" and q3.marks == 15
    assert q1.phase == "optional"


def test_word_limit_and_marks_for_gs():
    doc = parse_mains(pages(GS), year=2023, paper="gs-1")
    assert doc.questions[0].word_limit == 150 and doc.questions[0].marks == 10
    assert doc.questions[1].word_limit == 250 and doc.questions[1].marks == 15
    assert doc.questions[0].id == "MAINS-2023-GS1-001" and doc.questions[0].phase == "mains"


def test_mains_answers_are_never_invented():
    doc = parse_mains(pages(GS), year=2023, paper="gs-1")
    assert all(q.answer is None and q.answer_source == "none" for q in doc.questions)
