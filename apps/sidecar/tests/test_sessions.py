"""WU-P02-006: bookmarks -> study sessions + auto-tagging (specs/bookmarks.feature)."""

import json

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.llm.types import ProviderError, ProviderResult
from tests.pdfgen import make_pdf

TOKEN = "t" * 32
H = {"Authorization": f"Bearer {TOKEN}"}


def _page(title: str, fact: str) -> str:
    """~1400 chars of short lines, so the page yields at least two chunks (pdfium drops blank lines)."""
    lines = [title, fact]
    lines += [f"Line {i} explains the working of the Union and the States in detail." for i in range(1, 19)]
    return "\n".join(lines)


PAGES = [
    _page(
        "Federalism in India",
        "The Constitution describes India as a Union of States. Article 3 lets Parliament form States.",
    ),
    _page(
        "Fundamental Rights",
        "Article 14 guarantees equality before law. Article 21 protects life and liberty.",
    ),
]


class FakeLLM:
    name, kind = "ollama", "local"

    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, []

    def complete(self, messages, *, model, json_schema=None, timeout=60.0):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return ProviderResult(json.dumps(self.reply), 5, 5, model)


def make(tmp_path, llm):
    app = create_app(TOKEN, data_dir=tmp_path / "d", provider_builder=lambda r, s: {"ollama": llm})
    return TestClient(app)


def add_doc(client, tmp_path, name="a", pages=PAGES):
    p = tmp_path / f"{name}.pdf"
    p.write_bytes(make_pdf(pages))
    return client.post("/library/documents", headers=H, json={"path": str(p)}).json()["id"]


def chunks(client, doc, page):
    return client.get(f"/library/documents/{doc}/pages/{page}/chunks", headers=H).json()


@pytest.fixture
def ctx(tmp_path):
    llm = FakeLLM({"node_ids": ["gs2.polity"]})
    client = make(tmp_path, llm)
    doc = add_doc(client, tmp_path)
    return client, doc, llm, tmp_path


def start(client, doc, page=1, idx=0):
    cid = chunks(client, doc, page)[idx]["id"]
    return client.post("/sessions", headers=H, json={"document_id": doc, "start_chunk_id": cid})


def test_requires_token(ctx):
    client, *_ = ctx
    assert client.get("/sessions/active").status_code == 401


def test_chunks_of_a_page_in_reading_order(ctx):
    client, doc, *_ = ctx
    cs = chunks(client, doc, 2)
    assert [c["ordinal"] for c in cs] == list(range(len(cs))) and len(cs) >= 2
    assert "equality" in cs[0]["text"].lower() or "equality" in cs[1]["text"].lower()
    assert client.get(f"/library/documents/{doc}/pages/99/chunks", headers=H).json() == []


def test_start_creates_running_session_and_blocks_a_second(ctx):
    client, doc, *_ = ctx
    r = start(client, doc)
    assert r.status_code == 200 and r.json()["status"] == "running" and r.json()["start"]["page"] == 1
    assert client.get("/sessions/active", headers=H).json()["id"] == r.json()["id"]
    again = start(client, doc, page=2)
    assert again.status_code == 409 and again.json()["detail"]["session_id"] == r.json()["id"]


def test_start_rejects_unknown_chunk_or_wrong_document(ctx):
    client, doc, *_ = ctx
    bad = client.post("/sessions", headers=H, json={"document_id": doc, "start_chunk_id": 99999})
    assert bad.status_code == 422


def test_end_closes_range_and_tags_through_the_llm(ctx):
    client, doc, llm, _ = ctx
    sid = start(client, doc, 1, 0).json()["id"]
    end_chunk = chunks(client, doc, 2)[1]["id"]
    r = client.post(
        f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": end_chunk, "focused_seconds": 1500}
    )
    body = r.json()
    assert r.status_code == 200 and body["status"] == "gate" and body["focused_seconds"] == 1500
    assert (body["start"]["page"], body["end"]["page"]) == (1, 2) and body["document_title"] == "a"
    assert [t["id"] for t in body["tags"]] == ["gs2.polity"] and body["needs_tagging"] is False
    assert len(llm.calls) == 1 and "gs2.polity" in llm.calls[0][-1].content
    assert client.get("/sessions/active", headers=H).json() is None


def test_end_validation(ctx, tmp_path):
    client, doc, *_ = ctx
    other = add_doc(client, tmp_path, "b", ["Other book\nSome other text about economy."])
    sid = start(client, doc, 2, 1).json()["id"]
    before = chunks(client, doc, 1)[0]["id"]
    assert client.post(f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": before}).status_code == 422
    foreign = chunks(client, other, 1)[0]["id"]
    assert client.post(f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": foreign}).status_code == 422
    assert client.post("/sessions/999/end", headers=H, json={"end_chunk_id": before}).status_code == 404
    ok = client.post(
        f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": chunks(client, doc, 2)[1]["id"]}
    )
    assert ok.status_code == 200
    again = client.post(
        f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": chunks(client, doc, 2)[1]["id"]}
    )
    assert again.status_code == 409


def test_unknown_ids_fall_back_to_keyword_match(tmp_path):
    client = make(tmp_path, FakeLLM({"node_ids": ["nope.nothing"]}))
    doc = add_doc(client, tmp_path)
    sid = start(client, doc, 1, 0).json()["id"]
    r = client.post(
        f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": chunks(client, doc, 1)[-1]["id"]}
    )
    assert [t["id"] for t in r.json()["tags"]] == [
        "gs2.polity"
    ]  # "Constitution" matches "Constitution and Polity"


def test_llm_failure_never_blocks_the_session(tmp_path):
    client = make(tmp_path, FakeLLM(error=ProviderError("unavailable", "down")))
    doc = add_doc(client, tmp_path)
    sid = start(client, doc, 1, 0).json()["id"]
    r = client.post(
        f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": chunks(client, doc, 1)[-1]["id"]}
    )
    assert r.status_code == 200 and r.json()["status"] == "gate" and r.json()["tags"]


def test_untaggable_range_is_flagged_and_can_be_tagged_manually(tmp_path):
    client = make(tmp_path, FakeLLM({"node_ids": []}))
    doc = add_doc(
        client, tmp_path, "z", ["Zzz\nQqq www eee rrr ttt yyy uuu iii ooo ppp aaa sss ddd fff ggg."]
    )
    sid = start(client, doc, 1, 0).json()["id"]
    r = client.post(
        f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": chunks(client, doc, 1)[-1]["id"]}
    )
    assert r.json()["tags"] == [] and r.json()["needs_tagging"] is True
    bad = client.put(f"/sessions/{sid}/tags", headers=H, json={"node_ids": ["unknown.id"]})
    assert bad.status_code == 422
    ok = client.put(f"/sessions/{sid}/tags", headers=H, json={"node_ids": ["gs3.economy"]})
    assert ok.status_code == 200 and [t["id"] for t in ok.json()["tags"]] == ["gs3.economy"]
    assert ok.json()["needs_tagging"] is False


def test_source_budget_alert_on_the_fourth_source(tmp_path):
    client = make(tmp_path, FakeLLM({"node_ids": ["gs2.polity"]}))
    alert = None
    for i in range(4):
        doc = add_doc(client, tmp_path, f"book{i}", [f"Book {i}\nConstitution text number {i} about polity."])
        sid = start(client, doc, 1, 0).json()["id"]
        r = client.post(
            f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": chunks(client, doc, 1)[-1]["id"]}
        )
        alert = r.json()["source_budget"]
        if i < 3:
            assert alert == []
    assert alert and alert[0]["node_id"] == "gs2.polity" and alert[0]["sources"] == 4


def test_cancel_marks_skipped_without_tags(ctx):
    client, doc, llm, _ = ctx
    sid = start(client, doc).json()["id"]
    r = client.post(f"/sessions/{sid}/cancel", headers=H)
    assert r.status_code == 200 and r.json()["status"] == "skipped" and r.json()["tags"] == []
    assert client.get("/sessions/active", headers=H).json() is None and llm.calls == []
