from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from jarvis.library.service import (
    LibraryError,
    add_pdf,
    get_document,
    list_documents,
    search,
    set_position,
)
from jarvis.state import AppState


class DocumentOut(BaseModel):
    id: int
    title: str
    path: str
    page_count: int | None
    scanned: bool
    chunks: int
    last_page: int


class AddDocumentIn(BaseModel):
    path: str = Field(min_length=1, max_length=4096)


class AddDocumentOut(DocumentOut):
    duplicate: bool
    warning: str | None = None


class PositionIn(BaseModel):
    page: int


class SearchHit(BaseModel):
    id: int
    document_id: int
    page: int
    char_start: int
    char_end: int
    text: str


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/library", tags=["library"])

    @router.get("/documents", response_model=list[DocumentOut])
    def documents() -> list[dict]:
        with state.lock:
            return list_documents(state.conn)

    @router.post("/documents", response_model=AddDocumentOut)
    def add_document(body: AddDocumentIn) -> dict:
        try:
            with state.lock:
                return add_pdf(state.conn, Path(body.path))
        except LibraryError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    @router.get("/documents/{doc_id}", response_model=DocumentOut)
    def document(doc_id: int) -> dict:
        with state.lock:
            doc = get_document(state.conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="document not found")
        return doc

    @router.get("/documents/{doc_id}/file")
    def document_file(doc_id: int) -> Response:
        with state.lock:
            doc = get_document(state.conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="document not found")
        path = Path(doc["path"])
        if not path.is_file():
            raise HTTPException(
                status_code=410, detail="The PDF file has been moved or deleted. Add it to the library again."
            )
        return Response(content=path.read_bytes(), media_type="application/pdf")

    @router.put("/documents/{doc_id}/position", response_model=DocumentOut)
    def position(doc_id: int, body: PositionIn) -> dict:
        try:
            with state.lock:
                return set_position(state.conn, doc_id, body.page)
        except KeyError as e:
            raise HTTPException(status_code=404, detail="document not found") from e
        except LibraryError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    @router.get("/search", response_model=list[SearchHit])
    def search_chunks(q: str = Query(max_length=300), limit: int = Query(20, ge=1, le=100)) -> list[dict]:
        with state.lock:
            return search(state.conn, q, limit)

    return router
