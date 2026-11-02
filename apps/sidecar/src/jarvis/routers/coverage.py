from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from jarvis.coverage.service import coverage_nodes, dashboard_today
from jarvis.state import AppState


class NodeCoverage(BaseModel):
    id: str
    parent_id: str | None
    title: str
    kind: str
    verified_pages: float
    target_pages: int | None
    percent: int | None
    sessions: int


class HeatDay(BaseModel):
    date: str
    minutes: int


class NextBlock(BaseModel):
    document_id: int
    title: str
    page: int


class TodayOut(BaseModel):
    verified_minutes_today: int
    verified_minutes_week: int
    heatmap: list[HeatDay]
    next_block: NextBlock | None
    awaiting_gate_session_id: int | None
    due_cards: int
    review_remaining_today: int


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(tags=["coverage"])

    @router.get("/coverage/nodes", response_model=list[NodeCoverage])
    def nodes() -> list[dict]:
        with state.lock:
            return coverage_nodes(state.conn)

    @router.get("/dashboard/today", response_model=TodayOut)
    def today() -> dict:
        with state.lock:
            return dashboard_today(state.conn)

    return router
