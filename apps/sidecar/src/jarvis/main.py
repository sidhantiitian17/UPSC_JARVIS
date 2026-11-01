"""Sidecar entry point: `python -m jarvis --port N`; the token is read from JARVIS_TOKEN, never argv."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping

import uvicorn

from jarvis.app import MIN_TOKEN_LENGTH, create_app

LOOPBACK = "127.0.0.1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="jarvis", description="UPSC JARVIS sidecar (loopback only)")
    p.add_argument("--port", type=int, required=True, help="TCP port on 127.0.0.1")
    return p.parse_args(argv)


def load_token(env: Mapping[str, str]) -> str:
    token = env.get("JARVIS_TOKEN", "")
    if len(token) < MIN_TOKEN_LENGTH:
        raise ValueError(f"JARVIS_TOKEN must be set to at least {MIN_TOKEN_LENGTH} characters")
    return token


def build_uvicorn_config(port: int, token: str) -> uvicorn.Config:
    app = create_app(token)
    return uvicorn.Config(app, host=LOOPBACK, port=port, log_level="warning")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    uvicorn.Server(build_uvicorn_config(args.port, load_token(os.environ))).run()
