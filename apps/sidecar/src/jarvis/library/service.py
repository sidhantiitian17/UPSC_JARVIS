"""Library: add PDFs (sha256 dedupe), store page chunks with offsets, full-text search (FTS5)."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from jarvis.library.extract import ExtractError, chunk_text, extract_pages

SCANNED_MIN_CHARS_PER_PAGE = 25


class LibraryError(ValueError):
    """The file cannot be added; the message is safe to show to the owner."""


def _doc_row(conn: sqlite3.Connection, doc_id: int) -> dict:
    r = conn.execute(
        "select d.*, (select count(*) from chunk c where c.document_id = d.id) as chunks "
        "from document d where d.id = ?",
        (doc_id,),
    ).fetchone()
    return {**dict(r), "scanned": bool(r["scanned"])}


def list_documents(conn: sqlite3.Connection) -> list[dict]:
    ids = [r["id"] for r in conn.execute("select id from document order by id")]
    return [_doc_row(conn, i) for i in ids]


def get_document(conn: sqlite3.Connection, doc_id: int) -> dict | None:
    if not conn.execute("select 1 from document where id = ?", (doc_id,)).fetchone():
        return None
    return _doc_row(conn, doc_id)


def add_pdf(conn: sqlite3.Connection, path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise LibraryError("That file does not exist.")
    if not path.is_file():
        raise LibraryError("That path is a folder, not a PDF file.")
    if path.suffix.lower() != ".pdf":
        raise LibraryError("Only PDF files can be added.")

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    existing = conn.execute("select id from document where sha256 = ?", (digest,)).fetchone()
    if existing:
        doc = _doc_row(conn, existing["id"])
        return {**doc, "duplicate": True, "warning": None}

    try:
        pages = extract_pages(path)
    except ExtractError as e:
        raise LibraryError(f"This PDF could not be read: {e}") from e

    text_chars = sum(len(re.sub(r"\s", "", p)) for p in pages)
    scanned = len(pages) == 0 or text_chars < SCANNED_MIN_CHARS_PER_PAGE * len(pages)
    warning = (
        "This looks like a scanned PDF (no readable text). It was added, but it cannot be searched, "
        "tagged or used for recall questions until it is OCR'd."
        if scanned
        else None
    )

    conn.execute("begin")
    try:
        cur = conn.execute(
            "insert into document(sha256,path,title,kind,page_count,scanned,added_at) values (?,?,?,?,?,?,?)",
            (digest, str(path), path.stem, "pdf", len(pages), int(scanned), datetime.now(UTC).isoformat()),
        )
        doc_id = cur.lastrowid
        if not scanned:
            for page_no, text in enumerate(pages, start=1):
                for ordinal, (start, end, body) in enumerate(chunk_text(text)):
                    conn.execute(
                        "insert into chunk(document_id,page,ordinal,text,char_start,char_end) "
                        "values (?,?,?,?,?,?)",
                        (doc_id, page_no, ordinal, body, start, end),
                    )
        conn.execute("commit")
    except Exception:
        conn.execute("rollback")
        raise
    return {**_doc_row(conn, doc_id), "duplicate": False, "warning": warning}


def search(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    if not tokens:
        return []
    fts = " OR ".join(f'"{t}"' for t in tokens)
    rows = conn.execute(
        "select c.id, c.document_id, c.page, c.char_start, c.char_end, c.text "
        "from chunk_fts f join chunk c on c.id = f.rowid "
        "where chunk_fts match ? order by bm25(chunk_fts) limit ?",
        (fts, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def set_position(conn: sqlite3.Connection, doc_id: int, page: int) -> dict:
    doc = get_document(conn, doc_id)
    if doc is None:
        raise KeyError(doc_id)
    if not 1 <= page <= (doc["page_count"] or 0):
        raise LibraryError(f"Page {page} is outside this document (1 to {doc['page_count']}).")
    conn.execute("update document set last_page = ? where id = ?", (page, doc_id))
    return _doc_row(conn, doc_id)


def page_chunks(conn: sqlite3.Connection, doc_id: int, page: int) -> list[dict]:
    rows = conn.execute(
        "select id, page, ordinal, text, char_start, char_end from chunk "
        "where document_id = ? and page = ? order by ordinal",
        (doc_id, page),
    ).fetchall()
    return [dict(r) for r in rows]
