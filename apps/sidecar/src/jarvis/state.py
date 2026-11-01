from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

from jarvis.db.migrate import connect, migrate
from jarvis.llm.client import LLMClient
from jarvis.llm.config import RoutingConfig, load_routing
from jarvis.llm.providers import build_providers
from jarvis.llm.secrets import SecretStore
from jarvis.llm.types import Provider

ProviderBuilder = Callable[[RoutingConfig, SecretStore], Mapping[str, Provider]]
DEFAULT_ROUTING = Path(__file__).resolve().parents[4] / "config" / "routing.yaml"


class AppState:
    """Process-wide state: one SQLite connection (guarded by `lock`), routing, secrets and the LLM client."""

    def __init__(
        self, conn: sqlite3.Connection, routing: RoutingConfig, provider_builder: ProviderBuilder
    ) -> None:
        self.conn = conn
        self.lock = threading.RLock()
        self.routing = routing
        self.secrets = SecretStore()
        self._builder = provider_builder
        self.llm = self._make_llm()

    def _make_llm(self) -> LLMClient:
        return LLMClient(self.conn, self.routing, dict(self._builder(self.routing, self.secrets)))

    def rebuild_llm(self) -> None:
        """Call after a secret changes so providers pick up (or drop) their keys."""
        self.llm = self._make_llm()

    @classmethod
    def create(
        cls,
        data_dir: Path | None = None,
        routing_path: Path | None = None,
        provider_builder: ProviderBuilder = build_providers,
    ) -> AppState:
        if data_dir is None:
            conn = connect(":memory:")
        else:
            data_dir.mkdir(parents=True, exist_ok=True)
            conn = connect(data_dir / "jarvis.db")
        migrate(conn)
        return cls(conn, load_routing(routing_path or DEFAULT_ROUTING), provider_builder)
