"""Golden evaluation harness for prompt templates (specs/llm-eval.feature).

Offline by default (scripted providers + in-memory DB). `python -m jarvis.llm.evals --live` runs the
same cases against the providers in config/routing.yaml using keys from JARVIS_SECRET_<NAME> env vars.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from jarvis.db.migrate import connect, migrate
from jarvis.llm.client import AllProvidersFailed, LLMClient
from jarvis.llm.config import load_routing
from jarvis.llm.providers import build_providers
from jarvis.llm.secrets import SecretStore
from jarvis.llm.tasks import TASKS


@dataclass
class GoldenCase:
    id: str
    task: str
    source_text: str
    prompt_version: str = "v1"
    canned: dict | None = None  # scripted output used for offline replay
    expect_pass: bool = True  # what offline replay of `canned` must produce
    expect_reason: str | None = None


@dataclass
class CaseResult:
    id: str
    task: str
    passed: bool
    reason: str = ""


@dataclass
class Report:
    results: list[CaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return sum(r.passed for r in self.results) / len(self.results) if self.results else 0.0


def load_cases(root: Path) -> list[GoldenCase]:
    cases: list[GoldenCase] = []
    for path in sorted(Path(root).glob("*/cases.json")):
        for raw in json.loads(path.read_text(encoding="utf-8")):
            cases.append(GoldenCase(**raw))
    return cases


def run_cases(client: LLMClient, cases: list[GoldenCase], *, local_only: bool = False) -> Report:
    report = Report()
    for c in cases:
        task = TASKS[c.task]
        try:
            result = client.complete(
                c.task,
                task.build_messages(c.source_text),
                json_schema=task.schema,
                prompt_version=c.prompt_version,
                local_only=local_only,
            )
        except AllProvidersFailed as e:
            report.results.append(CaseResult(c.id, c.task, False, str(e)))
            continue
        ok, reason = task.check(result.data, c.source_text)
        report.results.append(CaseResult(c.id, c.task, ok, reason))
    return report


def render_report(report: Report) -> str:
    per_task: dict[str, list[CaseResult]] = defaultdict(list)
    for r in report.results:
        per_task[r.task].append(r)
    lines = ["# Golden eval report", "", "| task | passed | total | pass rate |", "|---|---|---|---|"]
    for task, rs in sorted(per_task.items()):
        n = sum(r.passed for r in rs)
        lines.append(f"| {task} | {n} | {len(rs)} | {round(100 * n / len(rs))}% |")
    failures = [r for r in report.results if not r.passed]
    if failures:
        lines += ["", "## Failures", ""]
        lines += [f"- `{r.id}` ({r.task}): {r.reason}" for r in failures]
    return "\n".join(lines) + "\n"


def _live_client(routing_path: Path) -> LLMClient:
    routing = load_routing(routing_path)
    secrets = SecretStore()
    for spec in routing.providers.values():
        if spec.api_key_secret and (v := os.environ.get(f"JARVIS_SECRET_{spec.api_key_secret.upper()}")):
            secrets.set(spec.api_key_secret, v)
    conn = connect(":memory:")  # never the owner's database
    migrate(conn)
    return LLMClient(conn, routing, build_providers(routing, secrets))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run golden LLM evals against live providers.")
    ap.add_argument(
        "--live", action="store_true", required=True, help="required: offline replay runs under pytest"
    )
    ap.add_argument("--golden", type=Path, default=Path("tests/golden"))
    ap.add_argument("--routing", type=Path, default=Path("../../config/routing.yaml"))
    ap.add_argument("--local-only", action="store_true")
    args = ap.parse_args(argv)
    report = run_cases(_live_client(args.routing), load_cases(args.golden), local_only=args.local_only)
    print(render_report(report))
    return 0 if report.results and all(r.passed or False for r in report.results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
