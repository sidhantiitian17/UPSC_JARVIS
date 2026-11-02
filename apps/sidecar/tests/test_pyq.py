"""WU-P04-001: PYQ corpus importer + review (specs/pyq-corpus.feature)."""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.db.migrate import connect, migrate
from jarvis.pyq.importer import import_dataset, parse_paper
from jarvis.pyq.service import (
    PyqError,
    get_question,
    list_papers,
    list_questions,
    mark_verified,
    update_question,
)

FIXTURE = Path(__file__).parent / "fixtures" / "pyq"
REAL = Path(__file__).resolve().parents[3] / "datasets" / "pyq" / "md"
H = {"Authorization": "Bearer " + "t" * 32}


@pytest.fixture
def conn():
    c = connect(":memory:")
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def imported(conn):
    import_dataset(conn, FIXTURE)
    return conn


def test_parse_paper_reads_frontmatter_questions_and_options():
    meta, questions = parse_paper((FIXTURE / "gs-paper-1.md").read_text(encoding="utf-8"))
    assert (
        meta["year"] == 2023
        and meta["source_url"].endswith("csp-p1.pdf")
        and len(meta["source_sha256"]) == 64
    )
    assert [q["id"] for q in questions] == ["PRE-2023-GS1-001", "PRE-2023-GS1-002", "PRE-2023-GS1-003"]
    q1, q2, q3 = questions
    assert q1["stem"].startswith(".Consider the following trees") and "deciduous\ntrees?" in q1["stem"]
    assert q1["options"] == ["Only one", "Only two", "All three", "None"] and q1["status"] == "parsed"
    assert q2["status"] == "failed" and q2["stem"] == "" and "East India Company" in q2["raw_text"]
    assert q3["answer"] == "b" and q3["answer_source"] == "official-key" and q3["marks"] == 2.0


def test_import_stores_every_question_with_provenance(imported):
    rows = imported.execute("select * from pyq order by id").fetchall()
    assert len(rows) == 3
    r = rows[0]
    assert (r["phase"], r["year"], r["paper"], r["number"], r["page"]) == (
        "prelims",
        2023,
        "gs-paper-1",
        1,
        3,
    )
    assert r["source_url"].startswith("https://www.upsc.gov.in/") and len(r["source_sha256"]) == 64
    assert json.loads(r["options_json"]) == ["Only one", "Only two", "All three", "None"]
    assert rows[1]["raw_text"] and rows[1]["stem"] == ""


def test_import_returns_counts_and_is_idempotent(conn):
    first = import_dataset(conn, FIXTURE)
    assert first == {"files": 1, "questions": 3, "inserted": 3, "updated": 0, "kept_owner_edits": 0}
    second = import_dataset(conn, FIXTURE)
    assert second["inserted"] == 0 and second["updated"] == 3
    assert conn.execute("select count(*) from pyq").fetchone()[0] == 3


def test_reimport_never_overwrites_owner_edits(imported):
    update_question(
        imported,
        "PRE-2023-GS1-001",
        stem="Consider the following trees (fixed by owner)",
        options=None,
        answer="b",
    )
    mark_verified(imported, "PRE-2023-GS1-001")
    imported.execute(
        "update pyq set stem = 'owner changed' where id = 'PRE-2023-GS1-003'"
    )  # untouched status: refreshed
    stats = import_dataset(imported, FIXTURE)
    q1 = get_question(imported, "PRE-2023-GS1-001")
    assert q1["status"] == "verified" and q1["answer"] == "b" and q1["answer_source"] == "owner-verified"
    assert "fixed by owner" in q1["stem"]
    assert stats["kept_owner_edits"] == 1
    assert get_question(imported, "PRE-2023-GS1-003")["stem"].startswith("Which one of the following")


def test_official_key_answer_is_kept_but_owner_answer_wins(imported):
    assert get_question(imported, "PRE-2023-GS1-003")["answer_source"] == "official-key"
    update_question(imported, "PRE-2023-GS1-003", stem=None, options=None, answer="c")
    q = get_question(imported, "PRE-2023-GS1-003")
    assert (q["answer"], q["answer_source"]) == ("c", "owner-verified")
    import_dataset(imported, FIXTURE)
    assert get_question(imported, "PRE-2023-GS1-003")["answer"] == "c"


def test_editing_marks_reviewed_and_clearing_the_answer_resets_its_source(imported):
    q = update_question(
        imported,
        "PRE-2023-GS1-002",
        stem="It ended the trade monopoly of the East India Company.",
        options=["a1", "b1", "c1", "d1"],
        answer=None,
    )
    assert q["status"] == "reviewed" and q["answer"] is None and q["answer_source"] == "none"
    q = update_question(imported, "PRE-2023-GS1-002", stem=None, options=None, answer="a")
    assert q["answer_source"] == "owner-verified"
    q = update_question(imported, "PRE-2023-GS1-002", stem=None, options=None, answer="")
    assert q["answer"] is None and q["answer_source"] == "none"


def test_invalid_edits_are_refused(imported):
    with pytest.raises(PyqError):
        update_question(imported, "PRE-2023-GS1-001", stem=None, options=None, answer="e")
    with pytest.raises(PyqError):
        update_question(
            imported, "PRE-2023-GS1-001", stem=None, options=["only", "three", "opts"], answer=None
        )
    with pytest.raises(KeyError):
        update_question(imported, "NOPE", stem="x", options=None, answer=None)


def test_verify_needs_a_complete_question(imported):
    with pytest.raises(PyqError, match="stem"):
        mark_verified(imported, "PRE-2023-GS1-002")  # failed, no stem and no options
    update_question(
        imported, "PRE-2023-GS1-002", stem="Complete stem", options=["a", "b", "c", ""], answer=None
    ) if False else None
    with pytest.raises(PyqError, match="four options"):
        update_question(
            imported, "PRE-2023-GS1-002", stem="Complete stem", options=["a", "b", "c", ""], answer=None
        )
    update_question(
        imported, "PRE-2023-GS1-002", stem="Complete stem", options=["a", "b", "c", "d"], answer=None
    )
    assert mark_verified(imported, "PRE-2023-GS1-002")["status"] == "verified"


def test_verify_needs_provenance(imported):
    imported.execute("update pyq set source_url = null where id = 'PRE-2023-GS1-001'")
    with pytest.raises(PyqError, match="source"):
        mark_verified(imported, "PRE-2023-GS1-001")


def test_papers_list_counts_by_status(imported):
    mark_verified(imported, "PRE-2023-GS1-001")
    papers = list_papers(imported)
    assert papers == [
        {
            "phase": "prelims",
            "year": 2023,
            "paper": "gs-paper-1",
            "total": 3,
            "parsed": 1,
            "failed": 1,
            "reviewed": 0,
            "verified": 1,
        }
    ]


def test_questions_filter_and_paginate(imported):
    assert [q["id"] for q in list_questions(imported, status="failed")] == ["PRE-2023-GS1-002"]
    assert len(list_questions(imported, phase="prelims", year=2023, paper="gs-paper-1")) == 3
    assert list_questions(imported, year=1999) == []
    assert [q["id"] for q in list_questions(imported, limit=1, offset=1)] == ["PRE-2023-GS1-002"]


def test_real_dataset_imports_completely(conn):
    stats = import_dataset(conn, REAL)
    assert stats["files"] == 22 and stats["questions"] == stats["inserted"] == 1587
    by = {r["status"]: r["n"] for r in conn.execute("select status, count(*) as n from pyq group by status")}
    assert by == {"parsed": 820, "failed": 767}
    # nothing is verified and no answer was invented by the importer
    assert conn.execute("select count(*) from pyq where answer is not null").fetchone()[0] == 0
    parsed = conn.execute("select options_json from pyq where status = 'parsed'").fetchall()
    assert all(len(json.loads(r["options_json"])) == 4 for r in parsed)


def test_missing_folder_is_an_error(conn, tmp_path):
    with pytest.raises(PyqError):
        import_dataset(conn, tmp_path / "nope")
    empty = tmp_path / "empty"
    empty.mkdir()
    assert import_dataset(conn, empty)["questions"] == 0


@pytest.fixture
def client(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "md")
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d")), tmp_path / "md"


def test_api_import_browse_edit_verify(client):
    c, md = client
    assert c.get("/pyq/papers").status_code == 401
    out = c.post("/pyq/import", headers=H, json={"root": str(md)})
    assert out.status_code == 200 and out.json()["inserted"] == 3
    papers = c.get("/pyq/papers", headers=H).json()
    assert papers[0]["total"] == 3
    qs = c.get("/pyq/questions?status=parsed", headers=H).json()
    assert {q["id"] for q in qs} == {"PRE-2023-GS1-001", "PRE-2023-GS1-003"}
    one = c.get("/pyq/questions/PRE-2023-GS1-001", headers=H).json()
    assert one["options"] == ["Only one", "Only two", "All three", "None"] and one["source_url"]
    put = c.put("/pyq/questions/PRE-2023-GS1-001", headers=H, json={"answer": "b"})
    assert put.json()["answer"] == "b" and put.json()["answer_source"] == "owner-verified"
    assert c.put("/pyq/questions/PRE-2023-GS1-001", headers=H, json={"answer": "z"}).status_code == 422
    assert c.put("/pyq/questions/NOPE", headers=H, json={"answer": "a"}).status_code == 404
    assert c.post("/pyq/questions/PRE-2023-GS1-002/verify", headers=H).status_code == 422
    ok = c.post("/pyq/questions/PRE-2023-GS1-001/verify", headers=H)
    assert ok.status_code == 200 and ok.json()["status"] == "verified"
    assert c.post("/pyq/import", headers=H, json={"root": str(md / "missing")}).status_code == 422
