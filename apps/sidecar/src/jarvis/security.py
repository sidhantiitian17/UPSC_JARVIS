from __future__ import annotations

import hmac
from collections.abc import Callable

from fastapi import HTTPException, Request

MIN_TOKEN_LENGTH = 16


def make_token_dependency(token: str) -> Callable[[Request], None]:
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

    return require_token
