"""Sidecar entry point: `python -m jarvis --port N`; the token is read from JARVIS_TOKEN, never argv."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from pathlib import Path

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


def build_uvicorn_config(port: int, token: str, env: Mapping[str, str] | None = None) -> uvicorn.Config:
    env = os.environ if env is None else env
    data_dir = Path(env["JARVIS_DATA_DIR"]) if env.get("JARVIS_DATA_DIR") else None
    routing = Path(env["JARVIS_ROUTING"]) if env.get("JARVIS_ROUTING") else None
    app = create_app(token, data_dir=data_dir, routing_path=routing)
    return uvicorn.Config(app, host=LOOPBACK, port=port, log_level="warning")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    uvicorn.Server(build_uvicorn_config(args.port, load_token(os.environ))).run()
