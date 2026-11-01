"""Shared fixtures. All PDFs/HTML here are SYNTHETIC: they model the structure assumed in
docs/07-PYQ-DATASET.md and are NOT copies of UPSC papers."""
from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).parent / "fixtures"


def write_pdf(path: Path, pages: list[list[str]]) -> Path:
    c = canvas.Canvas(str(path), pagesize=A4)
    for lines in pages:
        y = 800
        c.setFont("Helvetica", 9)
        for line in lines:
            c.drawString(40, y, line)
            y -= 11
        c.showPage()
    c.save()
    return path


def write_two_column_pdf(path: Path, pages: list[tuple[list[str], list[str]]]) -> Path:
    """Each page = (left column lines, right column lines); lines at equal heights are interleaved by a
    naive top-to-bottom reader, which is what the extractor must not do."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for left, right in pages:
        c.setFont("Helvetica", 9)
        for col_x, lines in ((40, left), (320, right)):
            y = 800
            for line in lines:
                c.drawString(col_x, y, line)
                y -= 11
        c.showPage()
    c.save()
    return path


def prelims_lines(n: int = 100, statements_in: int = 4, broken: int | None = None) -> list[str]:
    """Synthetic Prelims text. Question `statements_in` has 5 numbered statements (1.-5.) to
    exercise the 'numbered statements vs question numbers' ambiguity."""
    lines = ["Test Booklet Series A", "GENERAL STUDIES (PAPER - I)", "Each item carries 2 marks.", ""]
    for q in range(1, n + 1):
        lines.append(f"{q}. With reference to topic {q}, consider the following statements:")
        if q == statements_in:
            for s in range(1, 6):
                lines.append(f"{s}. Statement {s} about topic {q} is claimed")
        else:
            lines.append("1. First claim about the topic")
            lines.append("2. Second claim about the topic")
        lines.append("Which of the statements given above is/are correct?")
        if broken == q:
            lines.append("Answer unclear here")
        else:
            lines += ["(a) 1 only", "(b) 2 only", "(c) Both 1 and 2", "(d) Neither 1 nor 2"]
        lines.append("")
    return lines


def paginate(lines: list[str], per_page: int = 60) -> list[list[str]]:
    return [lines[i : i + per_page] for i in range(0, len(lines), per_page)]


@pytest.fixture
def make_pdf(tmp_path):
    def _make(name: str, pages: list[list[str]]) -> Path:
        return write_pdf(tmp_path / name, pages)

    return _make
