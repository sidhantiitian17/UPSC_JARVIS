"""Pure-Python checks for the laya spike (no torch needed). The spike data is SMOKE-TEST data hand-written for
this repo; it is NOT UPSC PYQ data and NOT a benchmark."""
from __future__ import annotations

import pytest

from brain.spike_data import DIRECTIVE_ITEMS, DIRECTIVES, MAX_OPTIONS, SUBJECT_ITEMS, SUBJECTS, build_question
from brain.stats import accuracy, majority_baseline, percentile, summarize_latency


def test_subject_dataset_is_balanced_and_valid():
    assert len(SUBJECT_ITEMS) == 36
    labels = [lab for _, lab in SUBJECT_ITEMS]
    assert set(labels) == set(SUBJECTS)
    assert all(labels.count(s) == 6 for s in SUBJECTS)


def test_directive_dataset_is_balanced_and_valid():
    assert len(DIRECTIVE_ITEMS) == 30
    labels = [lab for _, lab in DIRECTIVE_ITEMS]
    assert set(labels) == set(DIRECTIVES)
    assert all(labels.count(d) == 3 for d in DIRECTIVES)


def test_no_duplicate_texts_across_datasets():
    texts = [t for t, _ in SUBJECT_ITEMS + DIRECTIVE_ITEMS]
    assert len(texts) == len(set(texts))


def test_question_builder_makes_choice_with_criteria_under_option_limit():
    q = build_question("subject", "Which subject?", SUBJECTS)
    assert q["type"] == "choice" and set(q["criteria"]) == set(SUBJECTS)
    assert len(q["criteria"]) <= MAX_OPTIONS  # model card: keep choice questions under ~20 options
    with pytest.raises(ValueError):
        build_question("too_many", "x", {f"opt{i}": "d" for i in range(MAX_OPTIONS + 1)})


def test_percentile_and_latency_summary():
    xs = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentile(xs, 50) == 30.0
    assert percentile(xs, 0) == 10.0 and percentile(xs, 100) == 50.0
    s = summarize_latency([0.010, 0.020, 0.030])
    assert s["n"] == 3 and s["p50_ms"] == pytest.approx(20.0) and s["max_ms"] == pytest.approx(30.0)
    with pytest.raises(ValueError):
        summarize_latency([])


def test_accuracy_and_baselines():
    assert accuracy(["a", "b", "a"], ["a", "a", "a"]) == pytest.approx(2 / 3)
    assert majority_baseline(["a", "a", "b"]) == pytest.approx(2 / 3)
    with pytest.raises(ValueError):
        accuracy(["a"], ["a", "b"])
