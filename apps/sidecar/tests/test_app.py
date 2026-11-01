"""WU-P01-003: sidecar is loopback-only and every route needs the per-launch bearer token."""

import pytest
from fastapi.testclient import TestClient

from jarvis import __version__
from jarvis.app import create_app
from jarvis.main import build_uvicorn_config, load_token, parse_args

TOKEN = "t" * 32


def client() -> TestClient:
    return TestClient(create_app(TOKEN))


def auth(token: str = TOKEN) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_ok_with_token():
    r = client().get("/health", headers=auth())
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": __version__}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong"},
        {"Authorization": f"Basic {TOKEN}"},
        {"Authorization": "Bearer "},
        {"Authorization": TOKEN},
    ],
)
def test_health_rejects_missing_or_bad_token(headers):
    r = client().get("/health", headers=headers)
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").lower().startswith("bearer")


def test_no_unauthenticated_docs_or_schema_routes():
    c = client()
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert c.get(path).status_code == 404


def test_create_app_rejects_weak_token():
    with pytest.raises(ValueError):
        create_app("short")


def test_server_config_is_loopback_only():
    cfg = build_uvicorn_config(port=4321, token=TOKEN)
    assert cfg.host == "127.0.0.1" and cfg.port == 4321


def test_token_comes_from_environment_never_from_argv():
    assert not any("token" in a for a in vars(parse_args(["--port", "5"])))
    with pytest.raises(SystemExit):
        parse_args(["--token", "abc"])
    with pytest.raises(ValueError):
        load_token({})
    assert load_token({"JARVIS_TOKEN": TOKEN}) == TOKEN
