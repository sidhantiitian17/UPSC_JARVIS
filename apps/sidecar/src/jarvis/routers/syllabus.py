from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis.state import AppState
from jarvis.syllabus.ontology import OntologyError, build_tree, load_ontology, sync_ontology


class SyllabusNodeOut(BaseModel):
    id: str
    parent_id: str | None
    title: str
    kind: str
    paper: str | None
    reviewed: bool
    source: str
    children: list[SyllabusNodeOut]


class ReloadOut(BaseModel):
    upserted: int
    pruned: int
    kept_linked: int


def build_router(state: AppState, syllabus_dir: Path) -> APIRouter:
    router = APIRouter(prefix="/syllabus", tags=["syllabus"])

    @router.get("/tree", response_model=list[SyllabusNodeOut])
    def tree() -> list[dict]:
        with state.lock:
            return build_tree(state.conn)

    @router.post("/reload", response_model=ReloadOut)
    def reload() -> dict[str, int]:
        try:
            nodes = load_ontology(syllabus_dir)
        except OntologyError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        with state.lock:
            stats = sync_ontology(state.conn, nodes)
            state.conn.commit()
        return stats

    return router
