from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

import jsonschema

from jarvis.llm.config import RoutingConfig
from jarvis.llm.types import Message, Provider, ProviderError


class AllProvidersFailed(RuntimeError):
    def __init__(self, task: str, attempts: list[str]):
        detail = "; ".join(attempts) if attempts else "no usable provider"
        super().__init__(
            f"no usable provider for task {task!r}"
            if not attempts
            else f"all providers failed for {task!r}: {detail}"
        )
        self.task, self.attempts = task, attempts


@dataclass
class LLMResult:
    text: str
    data: object | None
    provider: str
    model: str
    cache_hit: bool


def _canon(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _validate(text: str, schema: dict) -> tuple[object | None, str | None]:
    try:
        data = json.loads(text)
    except ValueError as e:
        return None, f"not valid JSON ({e})"
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return None, f"does not match the schema ({e.message})"
    return data, None


def _add(a: int | None, b: int | None) -> int | None:
    return None if a is None and b is None else (a or 0) + (b or 0)


class LLMClient:
    """Single door for LLM calls: cache, per-task fallback ladder, schema repair, usage ledger, queue.

    Cache key = sha256(task + messages + schema + prompt_version). It deliberately excludes the provider so a
    cached answer is reused whichever tier produced it; routing.yaml decides the model family per task.
    """

    def __init__(
        self, conn: sqlite3.Connection, routing: RoutingConfig, providers: Mapping[str, Provider]
    ) -> None:
        self._conn, self._routing, self._providers = conn, routing, providers

    def _record(
        self, provider: str, model: str, task: str, tin: int | None, tout: int | None, status: str, hit: int
    ) -> None:
        # The ledger holds metadata only: never prompt text and never keys.
        self._conn.execute(
            "insert into llm_usage(ts,provider,model,task,tokens_in,tokens_out,status,cache_hit) "
            "values (?,?,?,?,?,?,?,?)",
            (_now(), provider, model, task, tin, tout, status, hit),
        )

    def complete(
        self,
        task: str,
        messages: list[Message],
        *,
        json_schema: dict | None = None,
        prompt_version: str = "v1",
        queue_on_failure: bool = False,
        local_only: bool = False,
        timeout: float = 60.0,
    ) -> LLMResult:
        ladder = self._routing.tasks[task].ladder  # KeyError for unknown tasks
        key = hashlib.sha256(
            _canon(
                {
                    "task": task,
                    "messages": [[m.role, m.content] for m in messages],
                    "schema": json_schema,
                    "v": prompt_version,
                }
            ).encode()
        ).hexdigest()

        row = self._conn.execute("select response_json from llm_cache where key = ?", (key,)).fetchone()
        if row:
            cached = json.loads(row["response_json"])
            self._conn.execute("update llm_cache set hits = hits + 1 where key = ?", (key,))
            self._record("cache", "-", task, None, None, "ok", 1)
            return LLMResult(cached["text"], cached["data"], cached["provider"], cached["model"], True)

        attempts: list[str] = []
        for step in ladder:
            spec = self._routing.providers[step.provider]
            provider = self._providers.get(step.provider)
            if provider is None or not spec.is_enabled or (local_only and spec.kind != "local"):
                continue
            outcome = self._try(provider, step.model, task, messages, json_schema, timeout)
            if isinstance(outcome, LLMResult):
                self._conn.execute(
                    "insert or replace into llm_cache(key,response_json,created_at,hits) values (?,?,?,0)",
                    (
                        key,
                        json.dumps(
                            {
                                "text": outcome.text,
                                "data": outcome.data,
                                "provider": outcome.provider,
                                "model": outcome.model,
                            }
                        ),
                        _now(),
                    ),
                )
                return outcome
            attempts.append(f"{step.provider}:{outcome}")

        if queue_on_failure:
            request = {
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "json_schema": json_schema,
                "prompt_version": prompt_version,
            }
            self._conn.execute(
                "insert into llm_queue(task,request_json,created_at) values (?,?,?)",
                (task, json.dumps(request), _now()),
            )
        raise AllProvidersFailed(task, attempts)

    def _try(
        self,
        provider: Provider,
        model: str,
        task: str,
        messages: list[Message],
        schema: dict | None,
        timeout: float,
    ) -> LLMResult | str:
        """Returns an LLMResult, or the failure status string (already written to the ledger)."""
        try:
            res = provider.complete(messages, model=model, json_schema=schema, timeout=timeout)
        except ProviderError as e:
            self._record(provider.name, model, task, None, None, e.kind, 0)
            return e.kind
        tin, tout, data = res.tokens_in, res.tokens_out, None
        if schema is not None:
            data, err = _validate(res.text, schema)
            if err:  # one repair attempt on the same provider
                repair = messages + [
                    Message("assistant", res.text),
                    Message(
                        "user",
                        f"Your reply {err}. Reply with ONLY valid JSON that matches this JSON Schema: "
                        f"{json.dumps(schema)}",
                    ),
                ]
                try:
                    res2 = provider.complete(repair, model=model, json_schema=schema, timeout=timeout)
                except ProviderError as e:
                    self._record(provider.name, model, task, tin, tout, e.kind, 0)
                    return e.kind
                tin, tout = _add(tin, res2.tokens_in), _add(tout, res2.tokens_out)
                res = res2
                data, err = _validate(res2.text, schema)
                if err:
                    self._record(provider.name, model, task, tin, tout, "schema_invalid", 0)
                    return "schema_invalid"
        self._record(provider.name, model, task, tin, tout, "ok", 0)
        return LLMResult(res.text, data, provider.name, model, False)
