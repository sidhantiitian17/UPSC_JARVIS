"""Prompt templates, output schemas and semantic checks for LLM tasks.

`gate_mcq` is the sample task that proves the golden harness; Phase 2 reuses it for the recall gate.
Rule (CLAUDE.md): an LLM-generated MCQ ships only with a source chunk, a verbatim source quote
and a passing validation step. `check_gate_mcq` is that validation step.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from jarvis.llm.types import Message

GATE_MCQ_PROMPT_VERSION = "v1"

GATE_MCQ_SCHEMA: dict = {
    "type": "object",
    "required": ["question", "options", "answer_index", "source_quote", "explanation"],
    "properties": {
        "question": {"type": "string", "minLength": 8},
        "options": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 4,
            "maxItems": 4,
        },
        "answer_index": {"type": "integer", "minimum": 0},
        "source_quote": {"type": "string", "minLength": 8},
        "explanation": {"type": "string"},
    },
    "additionalProperties": False,
}

_SYSTEM = (
    "You write one multiple-choice recall question for a UPSC aspirant from the passage the user gives. "
    "Use ONLY facts stated in the passage. Give exactly four distinct options and the zero-based "
    "index of the correct one. Copy `source_quote` verbatim from the passage "
    "(a contiguous span that supports the answer); "
    "never paraphrase it. Reply with JSON only."
)


def build_gate_mcq_messages(source_text: str) -> list[Message]:
    return [Message("system", _SYSTEM), Message("user", f"Passage:\n{source_text}")]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def check_gate_mcq(data: object, source_text: str) -> tuple[bool, str]:
    """Semantic validation beyond the JSON schema. Returns (ok, reason)."""
    if not isinstance(data, dict):
        return False, "output is not an object"
    options = data.get("options") or []
    idx = data.get("answer_index")
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(options):
        return False, f"answer_index {idx!r} is not a valid option position"
    if len({_norm(o) for o in options}) != len(options):
        return False, "options are not distinct"
    if _norm(data.get("source_quote", "")) not in _norm(source_text):
        return False, "source_quote is not verbatim from the source passage"
    return True, ""


@dataclass(frozen=True)
class TaskDef:
    schema: dict
    build_messages: Callable[[str], list[Message]]
    check: Callable[[object, str], tuple[bool, str]]


TASKS: dict[str, TaskDef] = {
    "gate_mcq": TaskDef(GATE_MCQ_SCHEMA, build_gate_mcq_messages, check_gate_mcq),
}
