"""FastAPI application factory. Every route requires the per-launch bearer token."""

from __future__ import annotations

import hmac
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel

from jarvis import __version__

MIN_TOKEN_LENGTH = 16


class Health(BaseModel):
    status: Literal["ok"]
    version: str


def create_app(token: str) -> FastAPI:
    if len(token) < MIN_TOKEN_LENGTH:
        raise ValueError(f"token must be at least {MIN_TOKEN_LENGTH} characters")

    def require_token(request: Request) -> None:
        header = request.headers.get("authorization", "")
        scheme, _, supplied = header.partition(" ")
        if (
            scheme.lower() != "bearer"
            or not supplied
            or not hmac.compare_digest(supplied.encode(), token.encode())
        ):
            raise HTTPException(
                status_code=401, detail="unauthorized", headers={"WWW-Authenticate": "Bearer"}
            )

    # No /docs, /redoc or /openapi.json: nothing is reachable without the token.
    app = FastAPI(
        title="UPSC JARVIS sidecar", version=__version__, docs_url=None, redoc_url=None, openapi_url=None
    )

    @app.get("/health", response_model=Health, dependencies=[Depends(require_token)])
    def health() -> Health:
        return Health(status="ok", version=__version__)

    return app
