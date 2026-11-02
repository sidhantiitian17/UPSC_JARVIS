"""WU-P04-002: PYQ <-> syllabus tags (specs/pyq-tags.feature). Scripted LLM, no network."""

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.llm.types import ProviderError, ProviderResult

FIXTURE = Path(__file__).parent / "fixtures" / "pyq"
H = {"Authorization": "Bearer " + "t" * 32}
Q1, Q2, Q3 = "PRE-2023-GS1-001", "PRE-2023-GS1-002", "PRE-2023-GS1-003"


class FakeLLM:
    name, kind = "ollama", "local"

    def __init__(self, ids=None, error=None):
        self.ids, self.error, self.calls = ids or ["gs2.polity"], error, []

    def complete(self, messages, *, model, json_schema=None, timeout=60.0):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return ProviderResult(json.dumps({"node_ids": self.ids}), 3, 3, model)


def make(tmp_path, llm=None):
    shutil.copytree(FIXTURE, tmp_path / "md")
    app = create_app(
        "t" * 32, data_dir=tmp_path / "d", provider_builder=lambda r, s: {"ollama": llm or FakeLLM()}
    )
    c = TestClient(app)
    assert c.post("/pyq/import", headers=H, json={"root": str(tmp_path / "md")}).status_code == 200
    return c


_edits = iter(range(1000))


def edit(c):
    c.put(f"/pyq/questions/{Q1}", headers=H, json={"stem": f"Consider the following trees (v{next(_edits)})"})


def tags(c, qid):
    return {t["node_id"]: t for t in c.get(f"/pyq/questions/{qid}", headers=H).json()["tags"]}


def conn_of(c):
    return c.app.state.jarvis.conn


def test_suggestions_come_from_the_llm_with_the_question_and_options(tmp_path):
    llm = FakeLLM(["gs2.polity"])
    c = make(tmp_path, llm)
    r = c.post(f"/pyq/questions/{Q1}/suggest-tags", headers=H)
    assert r.status_code == 200
    t = tags(c, Q1)
    assert t["gs2.polity"]["status"] == "suggested" and t["gs2.polity"]["source"] == "llm"
    assert t["gs2.polity"]["title"]
    prompt = llm.calls[0][-1].content
    assert "Consider the following trees" in prompt and "Only two" in prompt and "gs2.polity" in prompt
    assert conn_of(c).execute("select count(*) from link where src_type = 'pyq'").fetchone()[0] == 0


def test_keyword_fallback_is_labelled_when_the_model_is_down(tmp_path):
    c = make(tmp_path, FakeLLM(error=ProviderError("unavailable", "down")))
    c.put(
        f"/pyq/questions/{Q3}",
        headers=H,
        json={"stem": "Which Article of the Constitution guarantees equality?"},
    )
    c.post(f"/pyq/questions/{Q3}/suggest-tags", headers=H)
    t = tags(c, Q3)
    assert t and all(x["source"] == "keyword" and x["status"] == "suggested" for x in t.values())


def test_a_question_without_text_cannot_be_tagged(tmp_path):
    c = make(tmp_path)
    r = c.post(f"/pyq/questions/{Q2}/suggest-tags", headers=H)
    assert r.status_code == 422 and "text" in r.json()["detail"].lower()
    assert c.post("/pyq/questions/NOPE/suggest-tags", headers=H).status_code == 404


def test_accept_creates_a_link_and_reject_removes_it(tmp_path):
    c = make(tmp_path)
    c.post(f"/pyq/questions/{Q1}/suggest-tags", headers=H)
    ok = c.put(f"/pyq/questions/{Q1}/tags/gs2.polity", headers=H, json={"decision": "accept"})
    assert ok.status_code == 200 and tags(c, Q1)["gs2.polity"]["status"] == "accepted"
    link = (
        conn_of(c)
        .execute(
            "select * from link where src_type='pyq' and src_id=? and dst_id='gs2.polity' and kind='tag'",
            (Q1,),
        )
        .fetchone()
    )
    assert link is not None
    c.put(f"/pyq/questions/{Q1}/tags/gs2.polity", headers=H, json={"decision": "reject"})
    assert tags(c, Q1)["gs2.polity"]["status"] == "rejected"
    assert conn_of(c).execute("select count(*) from link where src_type = 'pyq'").fetchone()[0] == 0


def test_suggesting_again_keeps_owner_decisions_and_replaces_pending_ones(tmp_path):
    llm = FakeLLM(["gs2.polity", "gs3.economy"])
    c = make(tmp_path, llm)
    c.post(f"/pyq/questions/{Q1}/suggest-tags", headers=H)
    c.put(f"/pyq/questions/{Q1}/tags/gs2.polity", headers=H, json={"decision": "accept"})
    c.put(f"/pyq/questions/{Q1}/tags/gs3.economy", headers=H, json={"decision": "reject"})
    llm.ids = ["gs2.polity", "gs3.economy", "gs1.culture"]
    edit(c)  # new text, so the cached answer is not reused
    c.post(f"/pyq/questions/{Q1}/suggest-tags", headers=H)
    t = tags(c, Q1)
    assert t["gs2.polity"]["status"] == "accepted" and t["gs3.economy"]["status"] == "rejected"
    assert t["gs1.culture"]["status"] == "suggested" and len(t) == 3
    llm.ids = ["gs3.security"]
    edit(c)
    c.post(f"/pyq/questions/{Q1}/suggest-tags", headers=H)
    t = tags(c, Q1)
    assert (
        "gs1.culture" not in t
        and t["gs3.security"]["status"] == "suggested"
        and t["gs2.polity"]["status"] == "accepted"
    )


def test_manual_tags_need_a_known_node(tmp_path):
    c = make(tmp_path)
    bad = c.post(f"/pyq/questions/{Q1}/tags", headers=H, json={"node_id": "nope.nothing"})
    assert bad.status_code == 422
    ok = c.post(f"/pyq/questions/{Q1}/tags", headers=H, json={"node_id": "gs3.economy"})
    assert ok.status_code == 200
    assert (
        tags(c, Q1)["gs3.economy"]["status"] == "accepted" and tags(c, Q1)["gs3.economy"]["source"] == "owner"
    )
    assert conn_of(c).execute("select count(*) from link where src_type = 'pyq'").fetchone()[0] == 1


def test_decision_validation(tmp_path):
    c = make(tmp_path)
    c.post(f"/pyq/questions/{Q1}/suggest-tags", headers=H)
    assert (
        c.put(f"/pyq/questions/{Q1}/tags/gs2.polity", headers=H, json={"decision": "maybe"}).status_code
        == 422
    )
    assert (
        c.put(f"/pyq/questions/{Q1}/tags/gs9.none", headers=H, json={"decision": "accept"}).status_code == 404
    )


def test_batch_suggests_only_for_untagged_questions_with_text(tmp_path):
    llm = FakeLLM()
    c = make(tmp_path, llm)
    out = c.post("/pyq/suggest-tags", headers=H, json={"limit": 10}).json()
    assert out == {"tagged": 2, "skipped_no_text": 1, "already_tagged": 0, "remaining": 0}
    assert len(llm.calls) == 2
    again = c.post("/pyq/suggest-tags", headers=H, json={"limit": 10}).json()
    assert again["tagged"] == 0 and again["already_tagged"] == 2
    assert c.post("/pyq/suggest-tags", headers=H, json={"limit": 0}).status_code == 422


def test_batch_limit_leaves_the_rest_for_next_time(tmp_path):
    c = make(tmp_path)
    out = c.post("/pyq/suggest-tags", headers=H, json={"limit": 1}).json()
    assert out["tagged"] == 1 and out["remaining"] == 1


def test_requires_token(tmp_path):
    c = make(tmp_path)
    assert c.post(f"/pyq/questions/{Q1}/suggest-tags").status_code == 401
