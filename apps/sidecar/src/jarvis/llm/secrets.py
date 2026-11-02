from __future__ import annotations


class SecretStore:
    """In-memory secrets (API keys). Never persisted by the sidecar and never printed."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def set(self, name: str, value: str) -> None:
        self._values[name] = value

    def get(self, name: str) -> str | None:
        return self._values.get(name)

    def has(self, name: str) -> bool:
        return bool(self._values.get(name))

    def values(self) -> list[str]:
        """Non-empty secret values, for guards that must never let one leak into a file."""
        return [v for v in self._values.values() if v]

    def names(self) -> list[str]:
        return sorted(n for n, v in self._values.items() if v)

    def __repr__(self) -> str:
        return f"SecretStore(names={self.names()})"

    __str__ = __repr__
