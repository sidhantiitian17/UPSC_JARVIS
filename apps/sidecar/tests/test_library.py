"""WU-P02-004: library add/extract/chunk/index/search (specs/library.feature)."""

import pytest

from jarvis.db.migrate import connect, migrate
from jarvis.library.extract import chunk_text, extract_pages
from jarvis.library.service import LibraryError, add_pdf, list_documents, search
from tests.pdfgen import make_pdf

PAGES = [
    "Federalism in India\nThe Constitution describes India as a Union of States.\n\n"
    "Parliament may form new States under Article 3.",
    "Fundamental Rights\nArticle 14 guarantees equality before law.\n\nArticle 21 protects life and liberty.",
    "Directive Principles\nDPSPs are non-justiciable guidelines for the State.",
]


@pytest.fixture
def conn():
    c = connect(":memory:")
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def pdf(tmp_path):
    p = tmp_path / "polity.pdf"
    p.write_bytes(make_pdf(PAGES))
    return p


def test_extract_pages_returns_text_per_page(pdf):
    pages = extract_pages(pdf)
    assert len(pages) == 3
    assert "Union of States" in pages[0] and "Article 14" in pages[1]


def test_add_pdf_stores_document_chunks_and_index(conn, pdf):
    out = add_pdf(conn, pdf)
    assert out["duplicate"] is False and out["page_count"] == 3 and out["scanned"] is False
    doc = list_documents(conn)[0]
    assert doc["title"] == "polity" and doc["page_count"] == 3 and doc["chunks"] >= 3
    hits = search(conn, "equality")
    assert hits and hits[0]["page"] == 2 and "equality" in hits[0]["text"].lower()
    assert hits[0]["document_id"] == out["id"]


def test_same_bytes_under_another_name_is_a_duplicate(conn, pdf, tmp_path):
    first = add_pdf(conn, pdf)
    copy = tmp_path / "renamed.pdf"
    copy.write_bytes(pdf.read_bytes())
    second = add_pdf(conn, copy)
    assert second["duplicate"] is True and second["id"] == first["id"]
    assert len(list_documents(conn)) == 1
    n = conn.execute("select count(*) from chunk").fetchone()[0]
    assert n == list_documents(conn)[0]["chunks"]


def test_chunk_offsets_are_exact_and_bounded(conn, pdf):
    add_pdf(conn, pdf)
    pages = extract_pages(pdf)
    rows = conn.execute("select page, text, char_start, char_end from chunk").fetchall()
    assert rows
    for r in rows:
        assert pages[r["page"] - 1][r["char_start"] : r["char_end"]] == r["text"]
        assert len(r["text"]) <= 900


def test_chunk_text_splits_long_paragraphs_on_sentences_and_hard_limits():
    sentence = "This is a sentence about governance. "
    text = sentence * 60
    chunks = chunk_text(text, max_chars=300)
    assert len(chunks) > 5
    assert all(len(t) <= 300 for _, _, t in chunks)
    assert all(text[s:e] == t for s, e, t in chunks)
    blob = "x" * 1000  # no whitespace at all: hard split
    assert all(len(t) <= 300 for _, _, t in chunk_text(blob, max_chars=300))


def test_chunk_text_skips_blank_input():
    assert chunk_text("   \n\n  ", max_chars=300) == []


def test_scanned_pdf_is_flagged_not_rejected(conn, tmp_path):
    p = tmp_path / "scan.pdf"
    p.write_bytes(make_pdf(["", "", ""]))
    out = add_pdf(conn, p)
    assert out["scanned"] is True and "scanned" in out["warning"].lower()
    assert conn.execute("select count(*) from chunk").fetchone()[0] == 0
    assert list_documents(conn)[0]["scanned"] is True


@pytest.mark.parametrize("kind", ["missing", "folder", "not_pdf", "corrupt"])
def test_invalid_inputs_are_refused_and_nothing_is_stored(conn, tmp_path, kind):
    if kind == "missing":
        p = tmp_path / "nope.pdf"
    elif kind == "folder":
        p = tmp_path / "dir.pdf"
        p.mkdir()
    elif kind == "not_pdf":
        p = tmp_path / "notes.txt"
        p.write_text("hello")
    else:
        p = tmp_path / "bad.pdf"
        p.write_bytes(b"%PDF-1.4 this is not really a pdf")
    with pytest.raises(LibraryError):
        add_pdf(conn, p)
    assert conn.execute("select count(*) from document").fetchone()[0] == 0


def test_search_ignores_punctuation_in_queries(conn, pdf):
    add_pdf(conn, pdf)
    assert search(conn, 'Article 14: "equality" OR (law)')  # must not raise an FTS syntax error
    assert search(conn, "") == []


def test_library_api(tmp_path):
    from fastapi.testclient import TestClient

    from jarvis.app import create_app

    token = "t" * 32
    h = {"Authorization": f"Bearer {token}"}
    p = tmp_path / "polity.pdf"
    p.write_bytes(make_pdf(PAGES))
    client = TestClient(create_app(token, data_dir=tmp_path / "d"))
    assert client.get("/library/documents").status_code == 401
    r = client.post("/library/documents", headers=h, json={"path": str(p)})
    assert r.status_code == 200 and r.json()["page_count"] == 3 and r.json()["duplicate"] is False
    doc_id = r.json()["id"]
    assert client.post("/library/documents", headers=h, json={"path": str(p)}).json()["duplicate"] is True
    assert [d["id"] for d in client.get("/library/documents", headers=h).json()] == [doc_id]
    assert client.get(f"/library/documents/{doc_id}", headers=h).json()["title"] == "polity"
    assert client.get("/library/documents/999", headers=h).status_code == 404
    hits = client.get("/library/search", headers=h, params={"q": "equality"}).json()
    assert hits and hits[0]["page"] == 2
    (tmp_path / "x.txt").write_text("hi")
    bad = client.post("/library/documents", headers=h, json={"path": str(tmp_path / "x.txt")})
    assert bad.status_code == 422 and "PDF" in bad.json()["detail"]


def _client(tmp_path):
    from fastapi.testclient import TestClient

    from jarvis.app import create_app

    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d")), {"Authorization": "Bearer " + "t" * 32}


def _add(client, h, path):
    return client.post("/library/documents", headers=h, json={"path": str(path)}).json()["id"]


def test_file_endpoint_returns_pdf_bytes(tmp_path, pdf):
    client, h = _client(tmp_path)
    doc_id = _add(client, h, pdf)
    r = client.get(f"/library/documents/{doc_id}/file", headers=h)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content == pdf.read_bytes()
    assert client.get(f"/library/documents/{doc_id}/file").status_code == 401


def test_file_endpoint_unknown_and_moved(tmp_path, pdf):
    client, h = _client(tmp_path)
    assert client.get("/library/documents/99/file", headers=h).status_code == 404
    doc_id = _add(client, h, pdf)
    pdf.unlink()
    r = client.get(f"/library/documents/{doc_id}/file", headers=h)
    assert r.status_code == 410 and "moved or deleted" in r.json()["detail"]


def test_position_is_saved_and_validated(tmp_path, pdf):
    client, h = _client(tmp_path)
    doc_id = _add(client, h, pdf)
    ok = client.put(f"/library/documents/{doc_id}/position", headers=h, json={"page": 3})
    assert ok.status_code == 200 and ok.json()["last_page"] == 3
    assert client.get(f"/library/documents/{doc_id}", headers=h).json()["last_page"] == 3
    for bad in (0, 4, -1):
        assert (
            client.put(f"/library/documents/{doc_id}/position", headers=h, json={"page": bad}).status_code
            == 422
        )
    assert client.put("/library/documents/99/position", headers=h, json={"page": 1}).status_code == 404
