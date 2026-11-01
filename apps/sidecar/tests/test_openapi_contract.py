"""The committed OpenAPI file (source of the TypeScript client types) must match the live app."""

import json
from pathlib import Path

from jarvis.app import create_app

SNAPSHOT = Path(__file__).resolve().parents[3] / "packages" / "shared" / "openapi.json"


def test_committed_openapi_matches_app():
    assert SNAPSHOT.exists(), "run `pnpm --filter @jarvis/shared gen:api`"
    live = create_app("x" * 32).openapi()
    assert json.loads(SNAPSHOT.read_text(encoding="utf-8")) == json.loads(json.dumps(live)), (
        "openapi.json is stale: run `pnpm --filter @jarvis/shared gen:api`"
    )
