"""Tests run against a frozen starter ontology, not the shipped (and growing) config/syllabus data."""

from pathlib import Path

import pytest

FIXTURE_SYLLABUS = Path(__file__).parent / "fixtures" / "syllabus"


@pytest.fixture(autouse=True)
def _frozen_syllabus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_SYLLABUS_DIR", str(FIXTURE_SYLLABUS))
