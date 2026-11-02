from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from jarvis.planner.service import build_plan, commit_plan, planner_status
from jarvis.state import AppState


class PlanIn(BaseModel):
    free_hours: float = Field(ge=1, le=16)


class Block(BaseModel):
    kind: str
    subject_id: str | None
    subject: str | None
    minutes: int
    reason: str


class PlanOut(BaseModel):
    free_minutes: int
    planned_minutes: int
    blocks: list[Block]
    catch_up: bool
    notes: list[str]


class Committed(BaseModel):
    free_minutes: int
    study_minutes: int
    blocks: list[Block]


class Yesterday(BaseModel):
    committed_minutes: int
    verified_minutes: int
    missed: bool


class StatusOut(BaseModel):
    committed_today: Committed | None
    yesterday: Yesterday | None
    catch_up_due: bool


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/planner", tags=["planner"])

    @router.post("/plan", response_model=PlanOut)
    def plan(body: PlanIn) -> dict:
        with state.lock:
            return build_plan(state.conn, body.free_hours)

    @router.post("/commit", response_model=Committed)
    def commit(body: PlanIn) -> dict:
        with state.lock:
            return commit_plan(state.conn, build_plan(state.conn, body.free_hours))

    @router.get("/status", response_model=StatusOut)
    def status() -> dict:
        with state.lock:
            return planner_status(state.conn)

    return router
