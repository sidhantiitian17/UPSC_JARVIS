"""WU-P01-005: LLMClient (specs/llm-gateway.feature). Providers are fakes; no network."""

import json

import httpx
import pytest

from jarvis.db.migrate import connect, migrate
from jarvis.llm.client import AllProvidersFailed, LLMClient
from jarvis.llm.config import RoutingConfig, load_routing
from jarvis.llm.providers import GeminiProvider, OpenAICompatProvider, build_providers
from jarvis.llm.secrets import SecretStore
from jarvis.llm.types import Message, ProviderError, ProviderResult

SCHEMA = {
    "type": "object",
    "required": ["answer"],
    "properties": {"answer": {"type": "integer"}},
    "additionalProperties": False,
}


class Fake:
    """Scripted provider: each call pops the next item (a ProviderResult-like text or an exception)."""

    def __init__(self, name, script, kind="recurring_free"):
        self.name, self.kind, self.script, self.calls = name, kind, list(script), []

    def complete(self, messages, *, model, json_schema=None, timeout=60.0):
        self.calls.append({"messages": list(messages), "model": model, "schema": json_schema})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return ProviderResult(text=item, tokens_in=11, tokens_out=7, model=model)


def routing(*steps, extra_providers=None):
    names = {p for p, _ in steps}
    providers = {
        n: {"type": "openai_compat", "kind": "recurring_free", "base_url": "http://x/v1"} for n in names
    }
    providers.update(extra_providers or {})
    return RoutingConfig.model_validate(
        {"providers": providers, "tasks": {"t": {"ladder": [{"provider": p, "model": m} for p, m in steps]}}}
    )


@pytest.fixture
def conn():
    c = connect(":memory:")
    migrate(c)
    yield c
    c.close()


def msgs(text="hello"):
    return [Message("user", text)]


def usage(conn):
    return [dict(r) for r in conn.execute("select * from llm_usage order by id")]


def rate_limit():
    return ProviderError("rate_limit", "429")


def test_identical_request_is_served_from_cache(conn):
    a = Fake("a", ["first answer"])
    client = LLMClient(conn, routing(("a", "m")), {"a": a})
    r1 = client.complete("t", msgs())
    r2 = client.complete("t", msgs())
    assert (r1.text, r2.text) == ("first answer", "first answer")
    assert len(a.calls) == 1 and r1.cache_hit is False and r2.cache_hit is True
    rows = usage(conn)
    assert [r["cache_hit"] for r in rows] == [0, 1]
    assert rows[0]["tokens_in"] == 11 and rows[0]["tokens_out"] == 7


def test_different_prompt_or_prompt_version_is_a_cache_miss(conn):
    a = Fake("a", ["x", "y", "z"])
    client = LLMClient(conn, routing(("a", "m")), {"a": a})
    client.complete("t", msgs("one"))
    client.complete("t", msgs("two"))
    client.complete("t", msgs("one"), prompt_version="v2")
    assert len(a.calls) == 3


def test_fallback_ladder_moves_to_the_next_tier(conn):
    a, b, c = (
        Fake("a", [rate_limit()]),
        Fake("b", [ProviderError("unavailable", "down")]),
        Fake("c", ["from c"]),
    )
    client = LLMClient(conn, routing(("a", "m1"), ("b", "m2"), ("c", "m3")), {"a": a, "b": b, "c": c})
    r = client.complete("t", msgs())
    assert (r.provider, r.model, r.text) == ("c", "m3", "from c")
    assert [(u["provider"], u["status"]) for u in usage(conn)] == [
        ("a", "rate_limit"),
        ("b", "unavailable"),
        ("c", "ok"),
    ]


def test_when_everything_fails_the_job_is_queued_only_if_asked(conn):
    a = Fake("a", [rate_limit(), rate_limit()])
    client = LLMClient(conn, routing(("a", "m")), {"a": a})
    with pytest.raises(AllProvidersFailed):
        client.complete("t", msgs("later"))
    assert conn.execute("select count(*) from llm_queue").fetchone()[0] == 0
    with pytest.raises(AllProvidersFailed):
        client.complete("t", msgs("later"), queue_on_failure=True)
    row = conn.execute("select task, status, request_json from llm_queue").fetchone()
    assert row["task"] == "t" and row["status"] == "pending" and "later" in row["request_json"]


def test_local_only_mode_never_touches_cloud_providers(conn):
    cloud, local = Fake("cloud", ["cloud"]), Fake("local", ["offline answer"], kind="local")
    cfg = routing(
        ("cloud", "m"),
        ("local", "m2"),
        extra_providers={"local": {"type": "openai_compat", "kind": "local", "base_url": "http://l/v1"}},
    )
    r = LLMClient(conn, cfg, {"cloud": cloud, "local": local}).complete("t", msgs(), local_only=True)
    assert r.provider == "local" and cloud.calls == []


def test_one_time_credit_providers_are_disabled_unless_enabled(conn):
    cfg = RoutingConfig.model_validate(
        {
            "providers": {
                "credit": {"type": "openai_compat", "kind": "one_time_credit", "base_url": "http://c/v1"},
                "free": {"type": "openai_compat", "kind": "recurring_free", "base_url": "http://f/v1"},
            },
            "tasks": {
                "t": {"ladder": [{"provider": "credit", "model": "m"}, {"provider": "free", "model": "m"}]}
            },
        }
    )
    assert cfg.providers["credit"].is_enabled is False and cfg.providers["free"].is_enabled is True
    credit, free = Fake("credit", ["paid"]), Fake("free", ["free answer"])
    r = LLMClient(conn, cfg, {"credit": credit, "free": free}).complete("t", msgs())
    assert r.provider == "free" and credit.calls == []


def test_structured_output_is_repaired_once(conn):
    a = Fake("a", ["not json", '{"answer": 3}'])
    r = LLMClient(conn, routing(("a", "m")), {"a": a}).complete("t", msgs(), json_schema=SCHEMA)
    assert r.data == {"answer": 3} and len(a.calls) == 2
    assert a.calls[1]["messages"][-1].role == "user" and "JSON" in a.calls[1]["messages"][-1].content
    assert a.calls[0]["schema"] == SCHEMA


def test_schema_violation_also_triggers_repair_then_falls_back_if_still_invalid(conn):
    a = Fake("a", ['{"answer": "three"}', '{"answer": "three"}'])
    b = Fake("b", ['{"answer": 4}'])
    r = LLMClient(conn, routing(("a", "m"), ("b", "m")), {"a": a, "b": b}).complete(
        "t", msgs(), json_schema=SCHEMA
    )
    assert r.provider == "b" and r.data == {"answer": 4}
    assert [u["status"] for u in usage(conn)] == ["schema_invalid", "ok"]


def test_invalid_output_is_never_cached(conn):
    a = Fake("a", ["bad", "still bad", '{"answer": 1}'])
    client = LLMClient(conn, routing(("a", "m")), {"a": a})
    with pytest.raises(AllProvidersFailed):
        client.complete("t", msgs(), json_schema=SCHEMA)
    assert conn.execute("select count(*) from llm_cache").fetchone()[0] == 0


def test_ledger_never_stores_prompt_text_or_keys(conn):
    secret = "sk-SECRET-123"
    a = Fake("a", ["ok"])
    LLMClient(conn, routing(("a", "m")), {"a": a}).complete("t", msgs(f"my private prompt {secret}"))
    dump = json.dumps(usage(conn))
    assert "private prompt" not in dump and secret not in dump


def test_unknown_task_and_missing_provider_are_clear_errors(conn):
    client = LLMClient(conn, routing(("a", "m")), {})
    with pytest.raises(KeyError):
        client.complete("nope", msgs())
    with pytest.raises(AllProvidersFailed) as e:
        client.complete("t", msgs())
    assert "no usable provider" in str(e.value)


def test_routing_yaml_loads_and_validates(tmp_path):
    p = tmp_path / "routing.yaml"
    p.write_text(
        "providers:\n  a: {type: openai_compat, kind: local, base_url: 'http://l/v1'}\n"
        "tasks:\n  ping: {ladder: [{provider: a, model: m}]}\n",
        encoding="utf-8",
    )
    assert load_routing(p).tasks["ping"].ladder[0].model == "m"
    p.write_text("providers: {}\ntasks:\n  t: {ladder: [{provider: ghost, model: m}]}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_routing(p)


def test_the_shipped_routing_config_is_valid_and_has_no_credit_provider_enabled():
    from pathlib import Path

    cfg = load_routing(Path(__file__).resolve().parents[3] / "config" / "routing.yaml")
    assert "ping" in cfg.tasks and "tag_chunk" in cfg.tasks and "gate_mcq" in cfg.tasks
    assert all(not (p.kind == "one_time_credit" and p.is_enabled) for p in cfg.providers.values())


def test_secret_store_hides_values():
    s = SecretStore()
    s.set("gemini_key", "abc123")
    assert s.get("gemini_key") == "abc123" and s.has("gemini_key") and not s.has("x")
    assert "abc123" not in repr(s) and "abc123" not in str(s)
    assert s.names() == ["gemini_key"]


# ---------- real provider request shapes (httpx MockTransport, no network) ----------


def http_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_openai_compat_request_and_response_mapping():
    seen = {}

    def handler(request):
        seen.update(
            url=str(request.url), auth=request.headers.get("authorization"), body=json.loads(request.content)
        )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "hi"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2},
            },
        )

    p = OpenAICompatProvider(
        "omniroute",
        "http://127.0.0.1:20128/v1/",
        "recurring_free",
        api_key="KEY",
        client=http_client(handler),
    )
    r = p.complete([Message("system", "s"), Message("user", "u")], model="auto", json_schema=SCHEMA)
    assert seen["url"] == "http://127.0.0.1:20128/v1/chat/completions" and seen["auth"] == "Bearer KEY"
    assert seen["body"]["model"] == "auto" and seen["body"]["messages"][1] == {"role": "user", "content": "u"}
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert (r.text, r.tokens_in, r.tokens_out) == ("hi", 5, 2)


@pytest.mark.parametrize(
    ("status", "kind"),
    [(429, "rate_limit"), (401, "auth"), (403, "auth"), (500, "unavailable"), (400, "bad_request")],
)
def test_openai_compat_maps_http_errors(status, kind):
    p = OpenAICompatProvider(
        "x", "http://x/v1", "local", client=http_client(lambda r: httpx.Response(status, text="no"))
    )
    with pytest.raises(ProviderError) as e:
        p.complete(msgs(), model="m")
    assert e.value.kind == kind


def test_connection_failure_is_unavailable():
    def boom(request):
        raise httpx.ConnectError("refused")

    p = OpenAICompatProvider("x", "http://x/v1", "local", client=http_client(boom))
    with pytest.raises(ProviderError) as e:
        p.complete(msgs(), model="m")
    assert e.value.kind == "unavailable"


def test_gemini_request_uses_header_key_not_url_and_maps_roles():
    seen = {}

    def handler(request):
        seen.update(
            url=str(request.url), key=request.headers.get("x-goog-api-key"), body=json.loads(request.content)
        )
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": '{"answer": 1}'}]}}],
                "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 4},
            },
        )

    p = GeminiProvider("gemini", "SECRET-KEY", client=http_client(handler))
    r = p.complete(
        [
            Message("system", "be brief"),
            Message("user", "q"),
            Message("assistant", "a"),
            Message("user", "q2"),
        ],
        model="gemini-x",
        json_schema=SCHEMA,
    )
    assert "SECRET-KEY" not in seen["url"] and seen["key"] == "SECRET-KEY"
    assert seen["url"].endswith("/models/gemini-x:generateContent")
    assert seen["body"]["systemInstruction"]["parts"][0]["text"] == "be brief"
    assert [c["role"] for c in seen["body"]["contents"]] == ["user", "model", "user"]
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert (r.text, r.tokens_in, r.tokens_out) == ('{"answer": 1}', 9, 4)


def test_build_providers_skips_providers_without_their_secret():
    cfg = RoutingConfig.model_validate(
        {
            "providers": {
                "gemini": {"type": "gemini", "kind": "recurring_free", "api_key_secret": "gemini_key"},
                "omniroute": {"type": "openai_compat", "kind": "recurring_free", "base_url": "http://o/v1"},
            },
            "tasks": {"t": {"ladder": [{"provider": "gemini", "model": "m"}]}},
        }
    )
    secrets = SecretStore()
    assert set(build_providers(cfg, secrets)) == {"omniroute"}
    secrets.set("gemini_key", "k")
    assert set(build_providers(cfg, secrets)) == {"omniroute", "gemini"}
