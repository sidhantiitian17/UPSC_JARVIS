"""Privacy panel: what is stored, where, for how long, and deletion per category (specs/privacy.feature)."""

from __future__ import annotations

import sqlite3

CATEGORY_IDS = ("library", "study_history", "review", "ai_cache", "focus")
RETENTION = "Kept until you delete it."

_CATEGORIES = {
    "library": {
        "title": "Library text",
        "description": "Titles and the text extracted from your PDFs, split into searchable chunks. The PDF files stay where you keep them.",
        "warning": "Deleting this also removes the sessions tied to those books (their gate results and answers too).",
    },
    "study_history": {
        "title": "Study history",
        "description": "Reading sessions, recall gate questions, your answers and confidence tags, results and syllabus tags.",
        "warning": "Your coverage and streak are rebuilt from this, so they reset.",
    },
    "review": {
        "title": "Review cards",
        "description": "Spaced-repetition cards and the log of every review.",
        "warning": "Cards for questions you got wrong will no longer come back.",
    },
    "focus": {
        "title": "Focus Guard samples",
        "description": "Only the category (study, neutral, distraction) and the app name, sampled every 5 seconds during focus blocks while Focus Guard is on. Window titles and web addresses are never stored.",
        "warning": "Your focus summary on Insights will start again from zero.",
    },
    "ai_cache": {
        "title": "AI cache and usage log",
        "description": "Saved AI answers (these can contain passages from your books), a metadata-only usage log and queued AI work.",
        "warning": "AI answers will be requested again next time.",
    },
}
NOTES = [
    "API keys are stored encrypted by your operating system on this PC only, never in the database or the vault.",
    "Nothing leaves this PC except the AI requests you trigger, sent to the providers you configured.",
    "These deletes never touch your syllabus, your settings or the files in your Obsidian vault.",
]


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return conn.execute(sql).fetchone()[0]


def _counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "library": _count(conn, "select count(*) from document"),
        "study_history": _count(conn, "select count(*) from study_session"),
        "review": _count(conn, "select count(*) from card"),
        "ai_cache": _count(conn, "select count(*) from llm_cache")
        + _count(conn, "select count(*) from llm_usage"),
        "focus": _count(conn, "select count(*) from focus_sample"),
    }


def summary(
    conn: sqlite3.Connection, data_dir: str | None, vault_path: str | None, library_path: str | None
) -> dict:
    counts = _counts(conn)
    return {
        "categories": [
            {
                "id": cid,
                "title": _CATEGORIES[cid]["title"],
                "description": _CATEGORIES[cid]["description"],
                "warning": _CATEGORIES[cid]["warning"],
                "count": counts[cid],
                "where": "The database file in your JARVIS data folder (this PC only).",
                "retention": RETENTION,
            }
            for cid in CATEGORY_IDS
        ],
        "locations": {"data_dir": data_dir, "vault_path": vault_path, "library_path": library_path},
        "notes": NOTES,
    }


def _delete_study_history(conn: sqlite3.Connection) -> None:
    conn.execute("delete from link where src_type = 'session'")
    conn.execute("delete from attempt where session_id is not null")
    conn.execute("delete from gate_question")
    conn.execute("delete from gate_result")
    conn.execute("delete from study_session")
    conn.execute("delete from setting where key like 'gate_meta:%' or key = 'gate_penalty'")


def delete_category(conn: sqlite3.Connection, category: str) -> None:
    if category not in CATEGORY_IDS:
        raise KeyError(category)
    conn.execute("begin")
    try:
        if category == "study_history":
            _delete_study_history(conn)
        elif category == "library":
            _delete_study_history(conn)
            conn.execute("delete from document")
        elif category == "review":
            conn.execute("delete from review_log")
            conn.execute("delete from card")
        elif category == "focus":
            conn.execute("delete from focus_sample")
        else:
            conn.execute("delete from llm_cache")
            conn.execute("delete from llm_usage")
            conn.execute("delete from llm_queue")
        conn.execute("commit")
    except Exception:
        conn.execute("rollback")
        raise
