from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis.state import AppState
from jarvis.study.sessions import (
    SessionConflict,
    SessionError,
    active_session,
    cancel_session,
    end_session,
    set_manual_tags,
    start_session,
)


class Point(BaseModel):
    chunk_id: int
    page: int
    ordinal: int


class TagOut(BaseModel):
    id: str
    title: str


class BudgetAlert(BaseModel):
    node_id: str
    title: str
    sources: int


class SessionOut(BaseModel):
    id: int
    document_id: int
    document_title: str
    status: str
    started_at: str
    ended_at: str | None
    focused_seconds: int
    start: Point | None
    end: Point | None
    tags: list[TagOut]
    needs_tagging: bool
    source_budget: list[BudgetAlert]


class StartIn(BaseModel):
    document_id: int
    start_chunk_id: int


class EndIn(BaseModel):
    end_chunk_id: int
    focused_seconds: int | None = Field(default=None, ge=0, le=86400)


class TagsIn(BaseModel):
    node_ids: list[str] = Field(max_length=10)


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/sessions", tags=["sessions"])

    def guarded(fn):  # maps service errors onto HTTP statuses
        try:
            with state.lock:
                return fn()
        except KeyError as e:
            raise HTTPException(status_code=404, detail="session not found") from e
        except SessionConflict as e:
            raise HTTPException(
                status_code=409, detail={"message": str(e), "session_id": e.session_id}
            ) from e
        except SessionError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    @router.get("/active", response_model=SessionOut | None)
    def active() -> dict | None:
        return guarded(lambda: active_session(state.conn))

    @router.post("", response_model=SessionOut)
    def start(body: StartIn) -> dict:
        return guarded(lambda: start_session(state.conn, body.document_id, body.start_chunk_id))

    @router.post("/{session_id}/end", response_model=SessionOut)
    def end(session_id: int, body: EndIn) -> dict:
        return guarded(
            lambda: end_session(state.conn, state.llm, session_id, body.end_chunk_id, body.focused_seconds)
        )

    @router.put("/{session_id}/tags", response_model=SessionOut)
    def tags(session_id: int, body: TagsIn) -> dict:
        return guarded(lambda: set_manual_tags(state.conn, session_id, body.node_ids))

    @router.post("/{session_id}/cancel", response_model=SessionOut)
    def cancel(session_id: int) -> dict:
        return guarded(lambda: cancel_session(state.conn, session_id))

    return router
