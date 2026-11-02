from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from jarvis.privacy.service import CATEGORY_IDS, delete_category, summary
from jarvis.state import AppState


class CategoryOut(BaseModel):
    id: str
    title: str
    description: str
    warning: str
    count: int
    where: str
    retention: str


class LocationsOut(BaseModel):
    data_dir: str | None
    vault_path: str | None
    library_path: str | None


class PrivacyOut(BaseModel):
    categories: list[CategoryOut]
    locations: LocationsOut
    notes: list[str]


def build_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/privacy", tags=["privacy"])

    def current() -> dict:
        def setting(key: str):  # noqa: ANN202
            row = state.conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
            return json.loads(row["value_json"]) if row else None

        data_dir = str(state.data_dir) if state.data_dir else None
        return summary(state.conn, data_dir, setting("vault_path"), setting("library_path"))

    @router.get("/summary", response_model=PrivacyOut)
    def get_summary() -> dict:
        with state.lock:
            return current()

    @router.delete("/{category}", response_model=PrivacyOut)
    def delete(category: str, confirm: str = Query(default="")) -> dict:
        if category not in CATEGORY_IDS:
            raise HTTPException(status_code=404, detail="unknown category")
        if confirm != "yes":
            raise HTTPException(status_code=422, detail="Deleting needs explicit confirmation (confirm=yes).")
        with state.lock:
            delete_category(state.conn, category)
            return current()

    return router
