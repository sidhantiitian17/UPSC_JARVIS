"""Write the sidecar's OpenAPI schema to packages/shared/openapi.json (source for the TS client types)."""

import json
from pathlib import Path

from jarvis.app import create_app

OUT = Path(__file__).resolve().parents[3] / "packages" / "shared" / "openapi.json"

if __name__ == "__main__":
    OUT.write_text(
        json.dumps(create_app("x" * 32).openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT}")
