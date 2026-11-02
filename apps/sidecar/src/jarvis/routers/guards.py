from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from jarvis.guards.service import set_bad_day, status
from jarvis.state import AppState


class SleepOut(BaseModel):
    enabled: bool
    start: str
    end: str
    active: bool
    minutes_until_end: int | None


class BurnoutOut(BaseModel):
    focused_hours_today: float
    warning: bool
    heavy_stretch: bool


class BadDayOut(BaseModel):
    today_active: bool
    note: str


class GuardOut(BaseModel):
    sleep: SleepOut
    burnout: BurnoutOut
    bad_day: BadDayOut
    messages: list[str]


class BadDayIn(BaseModel):
    active: bool


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/guard", tags=["guard"])

    @router.get("/status", response_model=GuardOut)
    def get_status() -> dict:
        with state.lock:
            return status(state.conn)

    @router.put("/bad-day", response_model=GuardOut)
    def put_bad_day(body: BadDayIn) -> dict:
        with state.lock:
            return set_bad_day(state.conn, body.active)

    return router
