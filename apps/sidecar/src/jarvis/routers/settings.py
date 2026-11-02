from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis.db.migrate import current_version
from jarvis.llm.client import AllProvidersFailed
from jarvis.llm.types import Message
from jarvis.state import AppState


class ProviderInfo(BaseModel):
    name: str
    kind: str
    enabled: bool
    needs_key: bool
    key_set: bool
    secret_name: str | None = None


class SettingsOut(BaseModel):
    library_path: str | None
    vault_path: str | None
    focus_minutes: int
    break_minutes: int
    providers: list[ProviderInfo]
    db_version: int


class SettingsIn(BaseModel):
    library_path: str | None = None
    vault_path: str | None = None
    focus_minutes: int | None = Field(default=None, ge=5, le=180)
    break_minutes: int | None = Field(default=None, ge=1, le=60)


class SecretIn(BaseModel):
    value: str = Field(min_length=1, max_length=4096)


class SecretOut(BaseModel):
    name: str
    set: bool


class AiTestOut(BaseModel):
    ok: bool
    provider: str | None = None
    model: str | None = None
    text: str | None = None
    error: str | None = None


FOLDER_KEYS = ("library_path", "vault_path")
DEFAULT_FOCUS_MINUTES = 50
DEFAULT_BREAK_MINUTES = 10


def _get(state: AppState, key: str):  # noqa: ANN202 - JSON value (str or int)
    row = state.conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def _put(state: AppState, key: str, value: str | int) -> None:
    state.conn.execute(
        "insert into setting(key,value_json) values (?,?) "
        "on conflict(key) do update set value_json = excluded.value_json",
        (key, json.dumps(value)),
    )


def build_router(state: AppState) -> APIRouter:
    router = APIRouter()

    def snapshot() -> SettingsOut:
        providers = [
            ProviderInfo(
                name=name,
                kind=spec.kind,
                enabled=spec.is_enabled,
                needs_key=spec.api_key_secret is not None,
                key_set=bool(spec.api_key_secret and state.secrets.has(spec.api_key_secret)),
                secret_name=spec.api_key_secret,
            )
            for name, spec in state.routing.providers.items()
        ]
        return SettingsOut(
            library_path=_get(state, "library_path"),
            vault_path=_get(state, "vault_path"),
            focus_minutes=_get(state, "focus_minutes") or DEFAULT_FOCUS_MINUTES,
            break_minutes=_get(state, "break_minutes") or DEFAULT_BREAK_MINUTES,
            providers=providers,
            db_version=current_version(state.conn),
        )

    def allowed_secret_names() -> set[str]:
        return {s.api_key_secret for s in state.routing.providers.values() if s.api_key_secret}

    @router.get("/settings", response_model=SettingsOut)
    def get_settings() -> SettingsOut:
        with state.lock:
            return snapshot()

    @router.put("/settings", response_model=SettingsOut)
    def put_settings(body: SettingsIn) -> SettingsOut:
        with state.lock:
            for key in FOLDER_KEYS:
                if key not in body.model_fields_set:
                    continue
                value = getattr(body, key)
                if value is None:
                    continue
                folder = Path(value).expanduser()
                if not folder.is_dir():
                    raise HTTPException(status_code=422, detail=f"{key}: folder does not exist")
                _put(state, key, str(folder.resolve()))
            for key in ("focus_minutes", "break_minutes"):
                if getattr(body, key) is not None:
                    _put(state, key, getattr(body, key))
            return snapshot()

    @router.put("/secrets/{name}", response_model=SecretOut)
    def put_secret(name: str, body: SecretIn) -> SecretOut:
        if name not in allowed_secret_names():
            raise HTTPException(status_code=404, detail="unknown secret name")
        with state.lock:
            state.secrets.set(name, body.value)
            state.rebuild_llm()
        return SecretOut(name=name, set=True)

    @router.delete("/secrets/{name}", response_model=SecretOut)
    def delete_secret(name: str) -> SecretOut:
        if name not in allowed_secret_names():
            raise HTTPException(status_code=404, detail="unknown secret name")
        with state.lock:
            state.secrets.set(name, "")
            state.rebuild_llm()
        return SecretOut(name=name, set=False)

    @router.post("/llm/test", response_model=AiTestOut)
    def llm_test() -> AiTestOut:
        messages = [
            Message("system", "You are a connectivity test. Reply with exactly one word: pong."),
            Message("user", f"ping {uuid.uuid4().hex}"),  # unique prompt: never answered from the cache
        ]
        with state.lock:
            try:
                res = state.llm.complete("ping", messages)
            except KeyError:
                return AiTestOut(ok=False, error="task 'ping' is not configured in routing.yaml")
            except AllProvidersFailed as e:
                return AiTestOut(ok=False, error=str(e))
        return AiTestOut(ok=True, provider=res.provider, model=res.model, text=res.text.strip()[:200])

    return router
