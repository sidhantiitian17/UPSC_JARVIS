from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from jarvis.gamification.service import progress
from jarvis.state import AppState


class Event(BaseModel):
    date: str
    kind: str
    text: str


class Comeback(BaseModel):
    active: bool
    lost_streak: int
    days_done: int
    days_needed: int


class ProgressOut(BaseModel):
    xp_total: int
    level: int
    xp_into_level: int
    xp_to_next_level: int
    streak: int
    best_streak: int
    freezes: int
    at_risk: bool
    today_minutes: int
    today_goal: int
    daily_goal_minutes: int
    bad_day_goal_minutes: int
    comeback: Comeback
    events: list[Event]


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(tags=["gamification"])

    @router.get("/gamification/progress", response_model=ProgressOut)
    def get_progress() -> dict:
        with state.lock:
            return progress(state.conn)

    return router
