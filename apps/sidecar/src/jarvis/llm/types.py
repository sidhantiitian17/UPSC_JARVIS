from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    role: str  # system | user | assistant
    content: str


@dataclass
class ProviderResult:
    text: str
    tokens_in: int | None
    tokens_out: int | None
    model: str


class ProviderError(Exception):
    """kind: rate_limit | unavailable | auth | bad_request | bad_response"""

    def __init__(self, kind: str, message: str = ""):
        super().__init__(f"{kind}: {message}" if message else kind)
        self.kind = kind


class Provider(Protocol):
    name: str
    kind: str  # recurring_free | one_time_credit | local

    def complete(
        self, messages: list[Message], *, model: str, json_schema: dict | None = None, timeout: float = 60.0
    ) -> ProviderResult: ...
