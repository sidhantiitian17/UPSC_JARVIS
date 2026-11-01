from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

Kind = Literal["recurring_free", "one_time_credit", "local"]


class ProviderSpec(BaseModel):
    type: Literal["openai_compat", "gemini"] = "openai_compat"
    kind: Kind
    base_url: str | None = None
    api_key_secret: str | None = None
    enabled: bool | None = None  # None => default by kind

    @property
    def is_enabled(self) -> bool:
        """One-time-credit providers are OFF unless explicitly enabled (silent paid-tier shift protection)."""
        return self.enabled if self.enabled is not None else self.kind != "one_time_credit"


class Step(BaseModel):
    provider: str
    model: str


class TaskSpec(BaseModel):
    ladder: list[Step] = Field(min_length=1)


class RoutingConfig(BaseModel):
    providers: dict[str, ProviderSpec]
    tasks: dict[str, TaskSpec]

    @model_validator(mode="after")
    def _ladders_reference_known_providers(self) -> RoutingConfig:
        for task, spec in self.tasks.items():
            for step in spec.ladder:
                if step.provider not in self.providers:
                    raise ValueError(f"task {task!r} uses unknown provider {step.provider!r}")
        return self


def load_routing(path: str | Path) -> RoutingConfig:
    return RoutingConfig.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
