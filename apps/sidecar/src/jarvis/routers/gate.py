from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis.gate.generate import GateError, build_gate, gate_view, report_question
from jarvis.state import AppState
from jarvis.study.sessions import SessionConflict


class GateQuestion(BaseModel):
    id: int
    stem: str
    options: list[str]
    style: str
    source: str
    interleaved: bool
    chunk_id: int | None
    page: int | None
    ordinal: int | None


class GateOut(BaseModel):
    session_id: int
    questions: list[GateQuestion]
    discarded: int
    fallback_used: bool
    short_range: bool


class ReportIn(BaseModel):
    reason: str = Field(default="", max_length=500)


class ReportOut(BaseModel):
    question_id: int
    status: str


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(tags=["gate"])

    @router.post("/sessions/{session_id}/gate", response_model=GateOut)
    def create_gate(session_id: int) -> dict:
        try:
            with state.lock:
                return build_gate(state.conn, state.llm, session_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="session not found") from e
        except SessionConflict as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
        except GateError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    @router.get("/sessions/{session_id}/gate", response_model=GateOut)
    def read_gate(session_id: int) -> dict:
        with state.lock:
            if (
                state.conn.execute("select 1 from study_session where id = ?", (session_id,)).fetchone()
                is None
            ):
                raise HTTPException(status_code=404, detail="session not found")
            return gate_view(state.conn, session_id)

    @router.post("/questions/{question_id}/report", response_model=ReportOut)
    def report(question_id: int, body: ReportIn) -> dict:
        try:
            with state.lock:
                report_question(state.conn, question_id, body.reason)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="question not found") from e
        return {"question_id": question_id, "status": "reported"}

    return router
