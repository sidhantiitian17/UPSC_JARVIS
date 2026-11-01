from __future__ import annotations

from dataclasses import dataclass, field

PAPER_CODES = {
    "gs-paper-1": "GS1", "csat": "CSAT", "gs-1": "GS1", "gs-2": "GS2", "gs-3": "GS3", "gs-4": "GS4",
    "essay": "ESSAY", "sociology-1": "SOC1", "sociology-2": "SOC2",
}
PAPER_TITLES = {
    "gs-paper-1": "General Studies Paper I", "csat": "General Studies Paper II (CSAT)",
    "gs-1": "General Studies Paper I", "gs-2": "General Studies Paper II",
    "gs-3": "General Studies Paper III", "gs-4": "General Studies Paper IV", "essay": "Essay",
    "sociology-1": "Sociology (Optional) Paper I", "sociology-2": "Sociology (Optional) Paper II",
}
# Expected counts are WARNING-level hints only (docs/07 section 6).
EXPECTED_COUNTS = {("prelims", "gs-paper-1"): 100, ("prelims", "csat"): 80}
ID_PREFIX = {"prelims": "PRE", "mains": "MAINS", "optional": "OPT-SOC"}


def make_id(phase: str, year: int, paper: str, number: int) -> str:
    return f"{ID_PREFIX[phase]}-{year}-{PAPER_CODES[paper]}-{number:03d}"


@dataclass
class Question:
    id: str
    phase: str
    year: int
    paper: str
    number: int
    page: int | None = None
    stem: str = ""
    options: dict[str, str] = field(default_factory=dict)
    marks: float | None = None
    negative_marks: float | None = None
    word_limit: int | None = None
    section: str | None = None
    parts: list[dict] = field(default_factory=list)
    answer: str | None = None
    answer_source: str = "none"
    suggested_answer: str | None = None
    status: str = "parsed"
    tags: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class PaperDoc:
    meta: dict
    questions: list[Question]

    def key(self) -> str:
        return f"{self.meta['phase']}/{self.meta['year']}/{self.meta['paper']}"


def base_meta(phase: str, year: int, paper: str, n: int) -> dict:
    return {
        "dataset": "upsc-pyq", "schema_version": 1, "exam": "cse", "phase": phase, "year": year,
        "paper": paper, "paper_title": PAPER_TITLES[paper], "lang": "en", "parser": "pyq-tools 0.1.0",
        "question_count": n, "expected_question_count": EXPECTED_COUNTS.get((phase, paper)),
        "verified_count": 0,
    }
