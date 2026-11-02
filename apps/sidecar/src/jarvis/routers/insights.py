from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from jarvis.insights.service import truth
from jarvis.state import AppState


class Day(BaseModel):
    date: str
    claimed_hours: float
    verified_hours: float


class Weekly(BaseModel):
    days: list[Day]
    claimed_hours: float
    verified_hours: float
    verified_share: int | None


class Calibration(BaseModel):
    tag: str
    answers: int
    accuracy: int | None
    enough_data: bool
    expected: str


class Forecast(BaseModel):
    exam_date: str
    assumed_exam_date: bool
    days_left: int
    avg_daily_verified_minutes: int
    projected_verified_hours: int


class TruthOut(BaseModel):
    weekly: Weekly
    calibration: list[Calibration]
    forecast: Forecast
    report: list[str]


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/insights", tags=["insights"])

    @router.get("/truth", response_model=TruthOut)
    def get_truth() -> dict:
        with state.lock:
            return truth(state.conn)

    return router
