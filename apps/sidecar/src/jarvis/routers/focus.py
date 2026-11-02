from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from jarvis.focus.service import add_samples, summary
from jarvis.state import AppState


class Sample(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a window title can never be sent, so it can never be stored

    ts: str | None = None
    category: Literal["study", "neutral", "distraction"]
    app: str = Field(min_length=1, max_length=80)


class SamplesIn(BaseModel):
    samples: list[Sample] = Field(max_length=200)


class StoredOut(BaseModel):
    stored: int


class DayOut(BaseModel):
    date: str
    study_minutes: float
    neutral_minutes: float
    distraction_minutes: float


class TotalsOut(BaseModel):
    study_minutes: float
    neutral_minutes: float
    distraction_minutes: float


class AppMinutes(BaseModel):
    app: str
    minutes: float


class FocusSummaryOut(BaseModel):
    enabled: bool
    days: list[DayOut]
    totals: TotalsOut
    top_distraction_apps: list[AppMinutes]


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/focus", tags=["focus"])

    def enabled() -> bool:
        row = state.conn.execute(
            "select value_json from setting where key = 'focus_guard_enabled'"
        ).fetchone()
        return bool(row and json.loads(row["value_json"]))

    @router.post("/samples", response_model=StoredOut)
    def post_samples(body: SamplesIn) -> dict:
        with state.lock:
            if not enabled():
                raise HTTPException(status_code=409, detail="Focus Guard is off, so no samples are stored.")
            return {"stored": add_samples(state.conn, [s.model_dump() for s in body.samples])}

    @router.get("/summary", response_model=FocusSummaryOut)
    def get_summary(days: int = Query(7, ge=1, le=31)) -> dict:
        with state.lock:
            return {"enabled": enabled(), **summary(state.conn, days)}

    return router
