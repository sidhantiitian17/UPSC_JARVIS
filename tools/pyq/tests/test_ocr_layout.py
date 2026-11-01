"""Scenarios: OCR layout (word boxes -> lines, gutter detection). All data is synthetic."""
from __future__ import annotations

from PIL import Image, ImageDraw

from pyq.ocr_layout import find_gutter, is_english_page, tsv_to_text

HEAD = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"


def row(block, line, word, left, top, text, conf=90, width=60, height=20):
    return f"5\t1\t{block}\t1\t{line}\t{word}\t{left}\t{top}\t{width}\t{height}\t{conf}\t{text}"


def tsv(*rows):
    return "\n".join([HEAD, *rows]) + "\n"


def test_detached_margin_number_is_attached_to_its_line():
    data = tsv(
        row(1, 1, 1, 110, 52, "Consider"), row(1, 1, 2, 180, 52, "the"), row(1, 1, 3, 220, 52, "following"),
        row(1, 2, 1, 110, 90, "Statement-I"),
        row(2, 1, 1, 20, 54, "1."),  # separate block, left margin, same baseline as the first line
        row(3, 1, 1, 20, 92, "2."),
    )
    assert tsv_to_text(data).splitlines() == ["1. Consider the following", "2. Statement-I"]


def test_lines_are_in_vertical_order():
    data = tsv(row(1, 1, 1, 10, 200, "later"), row(2, 1, 1, 10, 20, "first"), row(3, 1, 1, 70, 22, "line"))
    assert tsv_to_text(data).splitlines() == ["first line", "later"]


def test_large_vertical_gap_becomes_a_blank_line_and_even_spacing_does_not():
    even = tsv(*[row(1, i, 1, 10, 20 + 25 * i, f"line{i}") for i in range(5)])
    assert "" not in tsv_to_text(even).splitlines()
    gap = tsv(row(1, 1, 1, 10, 20, "a"), row(1, 2, 1, 10, 45, "b"), row(1, 3, 1, 10, 70, "c"),
              row(2, 1, 1, 10, 150, "d"), row(2, 2, 1, 10, 175, "e"))
    assert tsv_to_text(gap).splitlines() == ["a", "b", "c", "", "d", "e"]


def test_low_confidence_words_are_dropped():
    data = tsv(row(1, 1, 1, 10, 20, "Which", conf=95), row(1, 1, 2, 80, 20, "xq#z", conf=12),
               row(1, 1, 3, 150, 20, "one", conf=91))
    assert tsv_to_text(data) == "Which one"


def test_empty_or_header_only_tsv_gives_empty_text():
    assert tsv_to_text(HEAD + "\n") == ""
    assert tsv_to_text("") == ""


def _page(two_columns: bool) -> Image.Image:
    img = Image.new("L", (600, 800), 255)
    d = ImageDraw.Draw(img)
    for y in range(40, 760, 24):
        if two_columns:
            d.rectangle((30, y, 280, y + 10), fill=0)
            d.rectangle((320, y, 570, y + 10), fill=0)
        else:
            d.rectangle((30, y, 570, y + 10), fill=0)
    return img


def test_gutter_found_on_two_column_page():
    x = find_gutter(_page(True))
    assert x is not None and 280 <= x <= 320


def test_cut_goes_before_the_right_columns_margin_numbers():
    img = _page(True)
    d = ImageDraw.Draw(img)
    d.rectangle((300, 0, 600, 800), fill=255)  # clear the right column, then redraw it with a number margin
    for y in range(40, 760, 24):
        d.rectangle((335, y, 570, y + 10), fill=0)  # right text starts at 335
    for y in (40, 280, 520):
        d.rectangle((292, y, 302, y + 10), fill=0)  # faint column of question numbers
    x = find_gutter(img)
    assert x is not None and 280 <= x <= 291  # numbers (292+) must fall on the right side of the cut


ENGLISH_PAGE = (
    "Consider the following statements about the Parliament of India. "
    "The Lok Sabha is the lower house and the Rajya Sabha is the upper house. "
    "Which of the statements given above is correct? (a) 1 only (b) 2 only (c) Both 1 and 2 "
) * 3
# Hindi page read by the English model: Latin-looking junk with almost no real English words
HINDI_AS_JUNK = (
    "fier aeft fares afeat wad bred art arent eH bert tsa meet ara seat fear fifi PATI SR ST awe att wa dl eo "
    "area faaar ast aa aiedion saat day Bat ai canes aed Hac UH SEM Hea aK ag Al are "
) * 3


def test_english_page_detection():
    assert is_english_page(ENGLISH_PAGE) is True
    assert is_english_page(HINDI_AS_JUNK) is False


def test_short_or_empty_pages_are_not_judged_as_non_english():
    assert is_english_page("") is True
    assert is_english_page("KSPC-P-GSPO (3-A)") is True


def test_no_gutter_on_full_width_page():
    assert find_gutter(_page(False)) is None


def test_blank_page_has_no_gutter():
    assert find_gutter(Image.new("L", (600, 800), 255)) is None
