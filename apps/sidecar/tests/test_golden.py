"""WU-P01-008: golden eval harness (specs/llm-eval.feature). Offline: scripted providers, in-memory DB."""

import json
from pathlib import Path

import pytest

from jarvis.db.migrate import connect, migrate
from jarvis.llm.client import LLMClient
from jarvis.llm.config import RoutingConfig
from jarvis.llm.evals import GoldenCase, load_cases, render_report, run_cases
from jarvis.llm.tasks import GATE_MCQ_SCHEMA, build_gate_mcq_messages, check_gate_mcq
from jarvis.llm.types import ProviderResult

GOLDEN = Path(__file__).parent / "golden"

GOOD = {
    "question": "Which Article guarantees equality before law?",
    "options": ["Article 14", "Article 19", "Article 21", "Article 32"],
    "answer_index": 0,
    "source_quote": "Article 14 guarantees equality before law",
    "explanation": "Article 14.",
}
SOURCE = "Article 14 guarantees equality before law."


class Canned:
    name, kind = "canned", "local"

    def __init__(self, outputs):
        self.outputs = list(outputs)

    def complete(self, messages, *, model, json_schema=None, timeout=60.0):
        out = self.outputs.pop(0)
        return ProviderResult(
            text=out if isinstance(out, str) else json.dumps(out), tokens_in=1, tokens_out=1, model=model
        )


@pytest.fixture
def client_for():
    conns = []

    def make(*outputs):
        conn = connect(":memory:")
        migrate(conn)
        conns.append(conn)
        routing = RoutingConfig.model_validate(
            {
                "providers": {
                    "canned": {"type": "openai_compat", "kind": "local", "base_url": "http://x/v1"}
                },
                "tasks": {"gate_mcq": {"ladder": [{"provider": "canned", "model": "m"}]}},
            }
        )
        return LLMClient(conn, routing, {"canned": Canned(outputs)})

    yield make
    for c in conns:
        c.close()


def case(**kw):
    base = dict(id="c", task="gate_mcq", prompt_version="v1", source_text=SOURCE)
    base.update(kw)
    return GoldenCase(**base)


def test_valid_output_passes(client_for):
    report = run_cases(client_for(GOOD), [case()])
    assert report.results[0].passed and report.pass_rate == 1.0


def test_non_json_output_fails_with_reason(client_for):
    report = run_cases(client_for("not json", "not json"), [case()])
    r = report.results[0]
    assert not r.passed and ("json" in r.reason.lower() or "providers" in r.reason.lower())


def test_schema_break_fails(client_for):
    bad = {**GOOD, "options": ["only one"]}
    r = run_cases(client_for(bad, bad), [case()]).results[0]
    assert not r.passed


def test_fabricated_quote_is_not_verbatim():
    ok, reason = check_gate_mcq({**GOOD, "source_quote": "made up words"}, SOURCE)
    assert not ok and "source_quote is not verbatim" in reason


def test_quote_matching_ignores_whitespace_and_case_differences_only():
    ok, _ = check_gate_mcq({**GOOD, "source_quote": "ARTICLE 14   guarantees\nequality before law"}, SOURCE)
    assert ok


def test_answer_index_must_be_within_options():
    ok, reason = check_gate_mcq({**GOOD, "answer_index": 4}, SOURCE)
    assert not ok and "answer_index" in reason


def test_options_must_be_distinct():
    ok, reason = check_gate_mcq({**GOOD, "options": ["A", "A", "B", "C"]}, SOURCE)
    assert not ok and "distinct" in reason


def test_schema_requires_four_options_and_quote():
    import jsonschema

    jsonschema.validate(GOOD, GATE_MCQ_SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({k: v for k, v in GOOD.items() if k != "source_quote"}, GATE_MCQ_SCHEMA)


def test_prompt_contains_source_and_demands_verbatim_quote():
    msgs = build_gate_mcq_messages(SOURCE)
    joined = " ".join(m.content for m in msgs)
    assert SOURCE in joined and "verbatim" in joined.lower()


def test_report_is_markdown_with_pass_rate_per_task(client_for):
    report = run_cases(
        client_for(GOOD, {**GOOD, "answer_index": 9}, {**GOOD, "answer_index": 9}),
        [case(id="a"), case(id="b", source_text=SOURCE + " ")],
    )
    md = render_report(report)
    assert "| gate_mcq |" in md and "50%" in md and "answer_index" in md


@pytest.mark.golden
def test_golden_fixtures_behave_as_declared(client_for):
    """Replays tests/golden/*/cases.json with canned output (live: python -m jarvis.llm.evals --live)."""
    cases = load_cases(GOLDEN)
    assert cases, "no golden fixtures found"
    for c in cases:
        report = run_cases(client_for(c.canned, c.canned), [c])
        r = report.results[0]
        assert r.passed is c.expect_pass, f"{c.id}: {r.reason}"
        if c.expect_reason:
            assert c.expect_reason in r.reason, f"{c.id}: {r.reason}"


def test_eval_uses_in_memory_db_only(client_for, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_cases(client_for(GOOD), [case()])
    assert list(tmp_path.iterdir()) == []
