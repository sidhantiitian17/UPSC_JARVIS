"""SQLite connection helper and a tiny, reversible SQL migration runner.

Migration files live in `migrations/NNNN_name.sql` and contain a `-- up` section and a `-- down` section.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import sqlite_vec

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_FILE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    up: list[str]
    down: list[str]


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a connection with foreign keys, WAL (file databases) and the sqlite-vec extension."""
    conn = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("pragma foreign_keys = on")
    conn.execute("pragma busy_timeout = 5000")
    if str(path) != ":memory:":
        conn.execute("pragma journal_mode = wal")
        conn.execute("pragma synchronous = normal")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("begin immediate")
    try:
        yield conn
    except BaseException:
        conn.execute("rollback")
        raise
    conn.execute("commit")


def _statements(sql: str) -> list[str]:
    """Split a SQL script into complete statements (triggers contain semicolons)."""
    out: list[str] = []
    buf = ""
    for line in sql.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                out.append(buf.strip())
            buf = ""
    if buf.strip():
        raise ValueError(f"incomplete SQL statement: {buf.strip()[:60]}")
    return out


def load_migrations() -> list[Migration]:
    result = []
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = _FILE.match(f.name)
        if not m:
            raise ValueError(f"bad migration file name: {f.name}")
        text = f.read_text(encoding="utf-8")
        parts = re.split(r"(?m)^-- (up|down)\s*$", text)
        sections = dict(zip(parts[1::2], parts[2::2], strict=False))
        if "up" not in sections or "down" not in sections:
            raise ValueError(f"{f.name} needs '-- up' and '-- down' sections")
        result.append(
            Migration(int(m.group(1)), m.group(2), _statements(sections["up"]), _statements(sections["down"]))
        )
    versions = [m.version for m in result]
    if versions != list(range(1, len(versions) + 1)):
        raise ValueError(f"migration versions must be 1..N without gaps, got {versions}")
    return result


def latest_version() -> int:
    return len(load_migrations())


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "create table if not exists schema_migrations("
        "version integer primary key, name text not null, applied_at text not null)"
    )


def current_version(conn: sqlite3.Connection) -> int:
    _ensure_table(conn)
    return conn.execute("select coalesce(max(version), 0) from schema_migrations").fetchone()[0]


def migrate(conn: sqlite3.Connection, target: int | None = None) -> int:
    """Move the database to `target` (default: latest). Each step is atomic. Returns the new version."""
    migrations = load_migrations()
    latest = len(migrations)
    target = latest if target is None else target
    if not 0 <= target <= latest:
        raise ValueError(f"unknown target version {target} (latest is {latest})")
    cur = current_version(conn)
    if target > cur:
        steps = [(m, m.up, True) for m in migrations if cur < m.version <= target]
    else:
        steps = [(m, m.down, False) for m in reversed(migrations) if target < m.version <= cur]
    for m, statements, going_up in steps:
        with transaction(conn):
            for stmt in statements:
                conn.execute(stmt)
            if going_up:
                conn.execute(
                    "insert into schema_migrations(version,name,applied_at) values (?,?,?)",
                    (m.version, m.name, datetime.now(UTC).isoformat()),
                )
            else:
                conn.execute("delete from schema_migrations where version = ?", (m.version,))
    return current_version(conn)
