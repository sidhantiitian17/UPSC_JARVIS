from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jarvis.gate.generate import GateError, build_gate, gate_view, report_question
from jarvis.gate.scoring import answer_question, finish_gate, skip_gate
from jarvis.state import AppState
from jarvis.study.sessions import SessionConflict
from jarvis.vault.mirror import mirror_after_gate
from jarvis.vault.writer import VaultWriter


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


class AnswerIn(BaseModel):
    question_id: int
    chosen_index: int = Field(ge=0, le=3)
    confidence: str = Field(pattern="^[GAR]$")
    time_ms: int | None = Field(default=None, ge=0, le=3_600_000)


class AnswerOut(BaseModel):
    question_id: int
    correct: bool
    chosen_index: int
    answer_index: int
    explanation: str
    source_quote: str
    chunk_id: int | None
    page: int | None
    ordinal: int | None


class RestudyItem(BaseModel):
    chunk_id: int
    book: str
    page: int
    ordinal: int
    quote: str


class NodeRef(BaseModel):
    id: str
    title: str


class ResultOut(BaseModel):
    session_id: int
    total: int
    correct: int
    retention_pct: int
    passed: bool
    skipped: bool
    xp: int
    pass_mark: int
    restudy: list[RestudyItem]
    nodes: list[NodeRef]


class SkipIn(BaseModel):
    penalty: bool = True


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

    def run(fn):  # maps service errors onto HTTP statuses
        try:
            with state.lock:
                return fn()
        except KeyError as e:
            raise HTTPException(status_code=404, detail="not found") from e
        except SessionConflict as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @router.post("/sessions/{session_id}/gate/answer", response_model=AnswerOut)
    def answer(session_id: int, body: AnswerIn) -> dict:
        return run(
            lambda: answer_question(
                state.conn, session_id, body.question_id, body.chosen_index, body.confidence, body.time_ms
            )
        )

    def mirror(session_id: int) -> None:
        """Best-effort Obsidian mirror: a missing or broken vault must never break studying."""
        try:
            with state.lock:
                row = state.conn.execute("select value_json from setting where key='vault_path'").fetchone()
                if row is None:
                    return
                writer = VaultWriter(json.loads(row["value_json"]), secrets=state.secrets.values)
                mirror_after_gate(state.conn, writer, session_id)
        except Exception:  # noqa: BLE001 - deliberately swallow every mirror failure
            return

    @router.post("/sessions/{session_id}/gate/finish", response_model=ResultOut)
    def finish(session_id: int) -> dict:
        result = run(lambda: finish_gate(state.conn, session_id))
        mirror(session_id)
        return result

    @router.post("/sessions/{session_id}/gate/skip", response_model=ResultOut)
    def skip(session_id: int, body: SkipIn | None = None) -> dict:
        penalty = body.penalty if body else True
        result = run(lambda: skip_gate(state.conn, session_id, penalty=penalty))
        mirror(session_id)
        return result

    @router.post("/questions/{question_id}/report", response_model=ReportOut)
    def report(question_id: int, body: ReportIn) -> dict:
        try:
            with state.lock:
                report_question(state.conn, question_id, body.reason)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="question not found") from e
        return {"question_id": question_id, "status": "reported"}

    return router
