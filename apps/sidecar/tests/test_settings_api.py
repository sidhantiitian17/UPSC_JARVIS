"""WU-P01-006: settings, secrets and the Test-AI endpoint (all token-protected, secrets never echoed)."""

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.llm.types import ProviderResult

TOKEN = "t" * 32
H = {"Authorization": f"Bearer {TOKEN}"}


class FakeProvider:
    def __init__(self, name, kind="local", text="pong"):
        self.name, self.kind, self.text, self.calls = name, kind, text, 0

    def complete(self, messages, *, model, json_schema=None, timeout=60.0):
        self.calls += 1
        return ProviderResult(self.text, 3, 1, model)


def make_client(tmp_path, providers=None):
    holder = {} if providers is None else providers

    def builder(routing, secrets):
        return dict(holder)

    app = create_app(TOKEN, data_dir=tmp_path, provider_builder=builder)
    return TestClient(app), holder


def test_defaults_list_providers_without_keys(tmp_path):
    c, _ = make_client(tmp_path)
    body = c.get("/settings", headers=H).json()
    assert body["library_path"] is None and body["vault_path"] is None
    names = {p["name"]: p for p in body["providers"]}
    assert {"ollama", "omniroute", "gemini"} <= set(names)
    assert names["gemini"]["needs_key"] is True and names["gemini"]["key_set"] is False
    assert names["ollama"]["needs_key"] is False and names["ollama"]["kind"] == "local"
    assert body["db_version"] >= 2


def test_folders_must_exist_and_are_persisted(tmp_path):
    c, _ = make_client(tmp_path)
    lib = tmp_path / "library"
    assert c.put("/settings", headers=H, json={"library_path": str(lib)}).status_code == 422
    lib.mkdir()
    r = c.put("/settings", headers=H, json={"library_path": str(lib)})
    assert r.status_code == 200 and r.json()["library_path"] == str(lib.resolve())
    # a new app on the same data directory sees the saved value
    c2, _ = make_client(tmp_path)
    assert c2.get("/settings", headers=H).json()["library_path"] == str(lib.resolve())


def test_partial_update_keeps_other_folder(tmp_path):
    c, _ = make_client(tmp_path)
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    c.put("/settings", headers=H, json={"library_path": str(tmp_path / "a")})
    r = c.put("/settings", headers=H, json={"vault_path": str(tmp_path / "b")})
    assert r.json()["library_path"] == str((tmp_path / "a").resolve())
    assert r.json()["vault_path"] == str((tmp_path / "b").resolve())


def test_secrets_are_write_only(tmp_path):
    c, _ = make_client(tmp_path)
    secret = "SECRET-VALUE-123"
    r = c.put("/secrets/gemini_key", headers=H, json={"value": secret})
    assert r.status_code == 200 and r.json() == {"name": "gemini_key", "set": True}
    assert secret not in r.text
    settings = c.get("/settings", headers=H)
    assert secret not in settings.text
    gem = next(p for p in settings.json()["providers"] if p["name"] == "gemini")
    assert gem["key_set"] is True
    assert c.delete("/secrets/gemini_key", headers=H).json() == {"name": "gemini_key", "set": False}
    gem = next(p for p in c.get("/settings", headers=H).json()["providers"] if p["name"] == "gemini")
    assert gem["key_set"] is False


def test_only_known_secret_names_are_accepted(tmp_path):
    c, _ = make_client(tmp_path)
    assert c.put("/secrets/not_a_provider_key", headers=H, json={"value": "x"}).status_code == 404
    assert c.put("/secrets/gemini_key", headers=H, json={"value": ""}).status_code == 422


def test_secret_change_rebuilds_providers(tmp_path):
    built = []

    def builder(routing, secrets):
        built.append(secrets.has("gemini_key"))
        return {}

    c = TestClient(create_app(TOKEN, data_dir=tmp_path, provider_builder=builder))
    c.put("/secrets/gemini_key", headers=H, json={"value": "k"})
    assert built[-1] is True


def test_llm_test_success_bypasses_the_cache(tmp_path):
    p = FakeProvider("ollama")
    c, _ = make_client(tmp_path, {"ollama": p})
    r1 = c.post("/llm/test", headers=H).json()
    r2 = c.post("/llm/test", headers=H).json()
    assert r1["ok"] is True and r1["provider"] == "ollama" and r1["text"] == "pong"
    assert r2["ok"] is True and p.calls == 2  # a real test every time, never a cached answer


def test_llm_test_reports_failure_without_crashing(tmp_path):
    c, _ = make_client(tmp_path, {})
    r = c.post("/llm/test", headers=H)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False and "no usable provider" in body["error"]


@pytest.mark.parametrize(
    ("method", "path", "kw"),
    [
        ("GET", "/settings", {}),
        ("PUT", "/settings", {"json": {}}),
        ("PUT", "/secrets/gemini_key", {"json": {"value": "x"}}),
        ("DELETE", "/secrets/gemini_key", {}),
        ("POST", "/llm/test", {}),
    ],
)
def test_every_route_needs_the_token(tmp_path, method, path, kw):
    c, _ = make_client(tmp_path)
    assert c.request(method, path, **kw).status_code == 401
