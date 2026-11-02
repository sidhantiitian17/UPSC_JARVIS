from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from jarvis.pyq.importer import import_dataset
from jarvis.pyq.service import (
    PyqError,
    get_question,
    list_papers,
    list_questions,
    mark_verified,
    update_question,
)
from jarvis.state import DEFAULT_PYQ, AppState


class PaperOut(BaseModel):
    phase: str
    year: int
    paper: str
    total: int
    parsed: int
    failed: int
    reviewed: int
    verified: int


class PyqOut(BaseModel):
    id: str
    phase: str
    year: int
    paper: str
    number: int
    page: int | None
    marks: float | None
    negative_marks: float | None
    stem: str
    options: list[str]
    raw_text: str | None
    answer: str | None
    answer_source: str
    suggested_answer: str | None
    status: str
    source_url: str | None
    source_sha256: str | None


class ImportIn(BaseModel):
    root: str | None = None


class ImportOut(BaseModel):
    files: int
    questions: int
    inserted: int
    updated: int
    kept_owner_edits: int


class EditIn(BaseModel):
    stem: str | None = None
    options: list[str] | None = None
    answer: str | None = None


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/pyq", tags=["pyq"])

    def guarded(fn):  # maps service errors onto HTTP statuses
        try:
            with state.lock:
                return fn()
        except KeyError as e:
            raise HTTPException(status_code=404, detail="question not found") from e
        except PyqError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    @router.post("/import", response_model=ImportOut)
    def import_(body: ImportIn | None = None) -> dict:
        root = Path(body.root) if body and body.root else DEFAULT_PYQ
        return guarded(lambda: import_dataset(state.conn, root))

    @router.get("/papers", response_model=list[PaperOut])
    def papers() -> list[dict]:
        return guarded(lambda: list_papers(state.conn))

    @router.get("/questions", response_model=list[PyqOut])
    def questions(
        phase: str | None = None,
        year: int | None = None,
        paper: str | None = None,
        status: str | None = None,
        limit: int = Query(200, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> list[dict]:
        return guarded(lambda: list_questions(state.conn, phase, year, paper, status, limit, offset))

    @router.get("/questions/{qid}", response_model=PyqOut)
    def one(qid: str) -> dict:
        return guarded(lambda: get_question(state.conn, qid))

    @router.put("/questions/{qid}", response_model=PyqOut)
    def edit(qid: str, body: EditIn) -> dict:
        return guarded(lambda: update_question(state.conn, qid, body.stem, body.options, body.answer))

    @router.post("/questions/{qid}/verify", response_model=PyqOut)
    def verify(qid: str) -> dict:
        return guarded(lambda: mark_verified(state.conn, qid))

    return router
