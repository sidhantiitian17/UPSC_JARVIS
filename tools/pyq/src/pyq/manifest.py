from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SourceRecord:
    url: str
    exam: str
    year: int | None
    phase: str
    category: str
    title: str
    paper: str | None
    lang: str
    status: str  # downloaded|unchanged|skipped|out-of-scope|unclassified|blocked-non-official|blocked-by-robots|failed
    sha256: str | None = None
    bytes: int | None = None
    retrieved_at: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    local_path: str | None = None
    note: str | None = None


def _sort_key(r: SourceRecord):
    return (r.year or 0, r.phase, r.paper or "", r.url)


def save_manifest(path: Path, records: list[SourceRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(asdict(r), sort_keys=True, ensure_ascii=False) for r in sorted(records, key=_sort_key)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")


def load_manifest(path: Path) -> list[SourceRecord]:
    if not Path(path).exists():
        return []
    return [SourceRecord(**json.loads(ln)) for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]
