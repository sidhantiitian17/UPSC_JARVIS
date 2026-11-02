"""FastAPI application factory. Every route requires the per-launch bearer token."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from jarvis import __version__
from jarvis.llm.providers import build_providers
from jarvis.routers import coverage as coverage_router
from jarvis.routers import gate as gate_router
from jarvis.routers import library as library_router
from jarvis.routers import review as review_router
from jarvis.routers import sessions as sessions_router
from jarvis.routers import settings as settings_router
from jarvis.routers import syllabus as syllabus_router
from jarvis.security import MIN_TOKEN_LENGTH, make_token_dependency
from jarvis.state import DEFAULT_SYLLABUS, AppState, ProviderBuilder
from jarvis.syllabus.ontology import OntologyError, load_ontology, sync_ontology

__all__ = ["MIN_TOKEN_LENGTH", "Health", "create_app"]


class Health(BaseModel):
    status: Literal["ok"]
    version: str


def create_app(
    token: str,
    *,
    data_dir: Path | None = None,
    routing_path: Path | None = None,
    provider_builder: ProviderBuilder = build_providers,
    syllabus_dir: Path | None = None,
) -> FastAPI:
    require_token = make_token_dependency(token)
    state = AppState.create(data_dir, routing_path, provider_builder)

    # No /docs, /redoc or /openapi.json: nothing is reachable without the token.
    app = FastAPI(
        title="UPSC JARVIS sidecar", version=__version__, docs_url=None, redoc_url=None, openapi_url=None
    )
    app.state.jarvis = state

    @app.get("/health", response_model=Health, dependencies=[Depends(require_token)])
    def health() -> Health:
        return Health(status="ok", version=__version__)

    app.include_router(settings_router.build_router(state), dependencies=[Depends(require_token)])
    app.include_router(library_router.build_router(state), dependencies=[Depends(require_token)])
    app.include_router(sessions_router.build_router(state), dependencies=[Depends(require_token)])
    app.include_router(gate_router.build_router(state), dependencies=[Depends(require_token)])
    app.include_router(review_router.build_router(state), dependencies=[Depends(require_token)])
    app.include_router(coverage_router.build_router(state), dependencies=[Depends(require_token)])
    env_dir = os.environ.get("JARVIS_SYLLABUS_DIR")
    syl_dir = syllabus_dir or (Path(env_dir) if env_dir else DEFAULT_SYLLABUS)
    try:  # a broken ontology must not stop the app; POST /syllabus/reload reports the error
        sync_ontology(state.conn, load_ontology(syl_dir))
    except OntologyError:
        pass
    app.include_router(syllabus_router.build_router(state, syl_dir), dependencies=[Depends(require_token)])
    return app
