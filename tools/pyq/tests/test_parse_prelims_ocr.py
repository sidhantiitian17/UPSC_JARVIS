"""Scenarios: the Prelims parser tolerates OCR defects (missing numbers, numbered statements, bad option letters).
All text is synthetic."""
from __future__ import annotations

from pyq.extract import PageText, clean_text
from pyq.parse_prelims import parse_prelims


def block(n, number=True, subs=0, options=("1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"),
          letters="abcd", d_tail=None):
    lines = [f"{n}. " if number else ""]
    lines[0] += f"With reference to topic {n}, consider the following:"
    lines += [f"{i}. Claim {i} about topic {n}" for i in range(1, subs + 1)]
    lines.append("Which of the above is correct?")
    for letter, text in zip(letters, options, strict=True):
        lines.append(f"({letter}) {text}")
    if d_tail:
        lines.append(d_tail)
    lines.append("")  # layout gap between questions
    return lines


def doc(*blocks):
    lines = [ln for b in blocks for ln in b]
    return parse_prelims([PageText(1, "\n".join(lines) + "\n")], year=2024, paper="gs-paper-1")


def by_number(d):
    return {q.number: q for q in d.questions}


def test_one_missing_number_fails_only_that_question():
    d = doc(*[block(n, number=(n != 5)) for n in range(1, 9)])
    qs = by_number(d)
    assert sorted(qs) == list(range(1, 9))
    assert qs[5].status == "failed" and "topic 5" in qs[5].raw_text and qs[5].options == {}
    for n in (1, 2, 3, 4, 6, 7, 8):
        assert qs[n].status == "parsed", n
        assert f"topic {n}," in qs[n].stem
        assert qs[n].options["d"] == "Neither 1 nor 2"


def test_numbered_statement_is_not_taken_for_the_missing_question_number():
    d = doc(block(1), block(2), block(3, number=False, subs=4), block(4, subs=2), block(5))
    qs = by_number(d)
    assert sorted(qs) == [1, 2, 3, 4, 5]
    assert qs[3].status == "failed" and "Claim 3 about topic 3" in qs[3].raw_text
    assert qs[4].status == "parsed" and "topic 4," in qs[4].stem and "Claim 2 about topic 4" in qs[4].stem
    assert qs[5].status == "parsed"


def test_misread_option_letter_fails_only_its_own_question():
    d = doc(block(1), block(2, letters="abca"), block(3), block(4))
    qs = by_number(d)
    assert sorted(qs) == [1, 2, 3, 4]
    assert qs[2].status == "failed" and "topic 2" in qs[2].raw_text
    assert all(qs[n].status == "parsed" for n in (1, 3, 4))


def test_misread_larger_number_does_not_shift_the_following_questions():
    blocks = [block(n) for n in range(1, 8)]
    blocks[4][0] = blocks[4][0].replace("5.", "8.", 1)  # Q5 was read as "8."
    qs = by_number(doc(*blocks))
    assert sorted(qs) == list(range(1, 8))
    assert qs[5].status == "failed" and "topic 5" in qs[5].raw_text
    assert all(qs[n].status == "parsed" and f"topic {n}," in qs[n].stem for n in (1, 2, 3, 4, 6, 7))


def test_question_with_an_empty_option_is_failed():
    d = doc(block(1), block(2, options=("1 only", "", "Both 1 and 2", "Neither 1 nor 2")), block(3))
    qs = by_number(d)
    assert qs[2].status == "failed" and qs[2].options == {} and "topic 2" in qs[2].raw_text
    assert qs[1].status == "parsed" and qs[3].status == "parsed"


def test_wrapped_last_option_stays_together_and_next_stem_is_separate():
    d = doc(block(1), block(2, d_tail="holds until the gap"), block(3))
    qs = by_number(d)
    assert qs[2].options["d"] == "Neither 1 nor 2 holds until the gap"
    assert qs[3].stem.startswith("With reference to topic 3")


def test_numbered_statements_with_the_expected_number_inside_own_question_are_kept():
    d = doc(block(1), block(2, subs=5), block(3))
    qs = by_number(d)
    assert qs[2].status == "parsed" and "Claim 5 about topic 2" in qs[2].stem
    assert qs[3].status == "parsed"


def test_exam_instruction_numbers_before_question_one_are_skipped():
    filler = " ".join(["Read every instruction on this booklet carefully before you begin."] * 12)
    instructions = [f"1. You have to enter your roll number. {filler}", f"2. Fill the circles. {filler}",
                    f"3. Do not fold. {filler}", ""]
    d = doc(instructions, block(1), block(2))
    qs = by_number(d)
    assert sorted(qs) == [1, 2] and "topic 1," in qs[1].stem


def test_booklet_footer_code_is_removed_by_clean_text():
    pages = [PageText(1, "ordinary line\nKSPC-P-GSPO (3-A)\nKSPC-P-GSPO -(3-\nXDTG-F-GST/62A 3\nnext line\n")]
    text, _ = clean_text(pages)
    assert "KSPC" not in text and "XDTG" not in text
    assert "ordinary line" in text and "next line" in text
