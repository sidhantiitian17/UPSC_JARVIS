from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis.review.fsrs_service import queue, rate_card, stats
from jarvis.state import AppState


class ReviewCard(BaseModel):
    card_id: int
    question_id: int
    subject: str
    due: str
    stem: str
    options: list[str]
    answer_index: int
    explanation: str
    source_quote: str


class ReviewStats(BaseModel):
    due_now: int
    daily_limit: int
    reviewed_today: int
    remaining_today: int
    total_cards: int


class RateIn(BaseModel):
    rating: int


class RateOut(BaseModel):
    card_id: int
    due: str
    interval_days: float


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/review", tags=["review"])

    @router.get("/queue", response_model=list[ReviewCard])
    def get_queue() -> list[dict]:
        with state.lock:
            return queue(state.conn)

    @router.get("/stats", response_model=ReviewStats)
    def get_stats() -> dict:
        with state.lock:
            return stats(state.conn)

    @router.post("/cards/{card_id}/rate", response_model=RateOut)
    def rate(card_id: int, body: RateIn) -> dict:
        try:
            with state.lock:
                return rate_card(state.conn, card_id, body.rating)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="card not found") from e
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    return router
