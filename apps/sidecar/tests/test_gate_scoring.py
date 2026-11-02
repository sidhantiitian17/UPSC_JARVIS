"""WU-P02-009 backend: answering, scoring, restudy, skip penalty (specs/gate-scoring.feature)."""

from datetime import date, timedelta

import pytest

from jarvis.gate.generate import build_gate
from tests.test_gate import PAGES, FakeLLM, H, finished_session, make


@pytest.fixture
def gate(tmp_path):
    client = make(tmp_path, FakeLLM())
    sid, doc = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    return client, sid, g, tmp_path


def answer_key(client, qid):
    row = client.app.state.jarvis.conn.execute(
        "select answer_index from question where id=?", (qid,)
    ).fetchone()
    return row["answer_index"]


def answer(client, sid, qid, right, conf="G"):
    key = answer_key(client, qid)
    chosen = key if right else (key + 1) % 4
    return client.post(
        f"/sessions/{sid}/gate/answer",
        headers=H,
        json={"question_id": qid, "chosen_index": chosen, "confidence": conf, "time_ms": 4000},
    )


def run_gate(client, sid, g, right_count):
    for i, qq in enumerate(g["questions"]):
        assert answer(client, sid, qq["id"], i < right_count).status_code == 200
    return client.post(f"/sessions/{sid}/gate/finish", headers=H)


def test_answer_reveals_and_stores_the_attempt(gate):
    client, sid, g, _ = gate
    qq = g["questions"][0]
    r = answer(client, sid, qq["id"], True, "A")
    body = r.json()
    assert r.status_code == 200 and body["correct"] is True
    assert body["answer_index"] == answer_key(client, qq["id"]) and body["source_quote"] and body["page"] >= 1
    row = client.app.state.jarvis.conn.execute(
        "select * from attempt where question_id=?", (qq["id"],)
    ).fetchone()
    assert (row["confidence"], row["correct"], row["session_id"]) == ("A", 1, sid)


def test_answering_twice_returns_the_stored_result_without_a_second_attempt(gate):
    client, sid, g, _ = gate
    qid = g["questions"][0]["id"]
    first = answer(client, sid, qid, True).json()
    second = answer(client, sid, qid, False).json()  # a different choice must not overwrite the first
    assert second["correct"] is True and second == first
    n = client.app.state.jarvis.conn.execute(
        "select count(*) from attempt where question_id=?", (qid,)
    ).fetchone()[0]
    assert n == 1


def test_answer_validation(gate):
    client, sid, g, _ = gate
    qid = g["questions"][0]["id"]
    url = f"/sessions/{sid}/gate/answer"
    assert (
        client.post(
            url, headers=H, json={"question_id": qid, "chosen_index": 9, "confidence": "G"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            url, headers=H, json={"question_id": qid, "chosen_index": 1, "confidence": "X"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            url, headers=H, json={"question_id": 9999, "chosen_index": 1, "confidence": "G"}
        ).status_code
        == 404
    )
    assert (
        client.post(url, json={"question_id": qid, "chosen_index": 1, "confidence": "G"}).status_code == 401
    )


def test_finish_requires_all_questions_answered(gate):
    client, sid, g, _ = gate
    answer(client, sid, g["questions"][0]["id"], True)
    r = client.post(f"/sessions/{sid}/gate/finish", headers=H)
    assert r.status_code == 409 and "unanswered" in r.json()["detail"].lower()


def test_seventy_percent_passes_and_awards_xp(gate):
    client, sid, g, _ = gate
    n = len(g["questions"])
    right = -(-n * 70 // 100)
    r = run_gate(client, sid, g, right).json()
    assert r["passed"] is True and r["retention_pct"] >= 70 and r["xp"] > 0 and r["restudy"] == []
    state = client.app.state.jarvis
    assert state.conn.execute("select status from study_session where id=?", (sid,)).fetchone()[0] == "done"
    assert state.conn.execute("select passed from gate_result where session_id=?", (sid,)).fetchone()[0] == 1


def test_below_seventy_fails_with_restudy_advice_for_wrong_answers_only(gate):
    client, sid, g, _ = gate
    n = len(g["questions"])
    right = -(-n * 70 // 100) - 1
    r = run_gate(client, sid, g, right).json()
    assert r["passed"] is False and r["xp"] == 0 and r["retention_pct"] < 70
    assert r["restudy"] and all(item["book"] == "polity" and item["page"] >= 1 for item in r["restudy"])
    pages = [(i["page"], i["ordinal"]) for i in r["restudy"]]
    assert pages == sorted(pages) and len(pages) == len(set(pages))
    wrong_chunks = {
        client.app.state.jarvis.conn.execute(
            "select source_chunk_id from question where id=?", (qq["id"],)
        ).fetchone()[0]
        for qq in g["questions"][right:]
    }
    assert {i["chunk_id"] for i in r["restudy"]} == wrong_chunks
    status = client.app.state.jarvis.conn.execute(
        "select status from study_session where id=?", (sid,)
    ).fetchone()[0]
    assert status == "done"


def test_finishing_twice_returns_the_same_result(gate):
    client, sid, g, _ = gate
    first = run_gate(client, sid, g, len(g["questions"])).json()
    again = client.post(f"/sessions/{sid}/gate/finish", headers=H)
    assert again.status_code == 200 and again.json() == first


def test_confidence_tags_are_kept_for_calibration(gate):
    client, sid, g, _ = gate
    for qq, conf in zip(g["questions"], "GARGARGARG", strict=False):
        answer(client, sid, qq["id"], True, conf)
    rows = client.app.state.jarvis.conn.execute("select confidence from attempt order by id").fetchall()
    assert [r[0] for r in rows][:4] == ["G", "A", "R", "G"]


def test_awaiting_gate_is_reported_until_finished(gate):
    client, sid, g, _ = gate
    assert client.get("/sessions/awaiting-gate", headers=H).json()["id"] == sid
    run_gate(client, sid, g, len(g["questions"]))
    assert client.get("/sessions/awaiting-gate", headers=H).json() is None


def test_emergency_skip_costs_a_double_gate_tomorrow_only_once(tmp_path):
    client = make(tmp_path, FakeLLM())
    sid, _ = finished_session(client, tmp_path, "a")
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    base = len(g["questions"])
    r = client.post(f"/sessions/{sid}/gate/skip", headers=H).json()
    assert r["skipped"] is True and r["passed"] is False and r["xp"] == 0
    state = client.app.state.jarvis
    assert (
        state.conn.execute("select status from study_session where id=?", (sid,)).fetchone()[0] == "skipped"
    )
    assert client.get("/sessions/awaiting-gate", headers=H).json() is None

    sid2, _ = finished_session(client, tmp_path, "b")
    today_gate = client.post(f"/sessions/{sid2}/gate", headers=H).json()
    assert len(today_gate["questions"]) == base  # penalty starts tomorrow, not today

    sid3, _ = finished_session(client, tmp_path, "c")
    tomorrow = date.today() + timedelta(days=1)
    big = build_gate(state.conn, state.llm, sid3, today=tomorrow)
    assert len(big["questions"]) == min(30, base * 2)

    sid4, _ = finished_session(client, tmp_path, "d")
    after = build_gate(state.conn, state.llm, sid4, today=tomorrow)
    assert len(after["questions"]) == base  # the penalty was used up by one gate


def test_skip_after_finish_is_refused(gate):
    client, sid, g, _ = gate
    run_gate(client, sid, g, len(g["questions"]))
    assert client.post(f"/sessions/{sid}/gate/skip", headers=H).status_code == 409


def test_unknown_session_returns_404(gate):
    client, *_ = gate
    for path in ("answer", "finish", "skip"):
        r = client.post(
            f"/sessions/999/gate/{path}",
            headers=H,
            json={"question_id": 1, "chosen_index": 0, "confidence": "G"},
        )
        assert r.status_code == 404
    assert PAGES  # imported fixture data stays referenced


def test_skip_without_penalty_is_only_honoured_when_the_gate_could_not_be_built(tmp_path):
    from jarvis.llm.types import ProviderError

    client = make(tmp_path, FakeLLM(error=ProviderError("unavailable", "down")))
    sid, _ = finished_session(
        client, tmp_path, "tiny", ["Title\nShort text without enough sentences to quiz."]
    )
    assert client.post(f"/sessions/{sid}/gate", headers=H).status_code == 422
    r = client.post(f"/sessions/{sid}/gate/skip", headers=H, json={"penalty": False})
    assert r.status_code == 200 and r.json()["skipped"] is True
    state = client.app.state.jarvis
    assert state.conn.execute("select 1 from setting where key='gate_penalty'").fetchone() is None


def test_skip_without_penalty_is_ignored_when_questions_exist(gate):
    client, sid, g, _ = gate
    client.post(f"/sessions/{sid}/gate/skip", headers=H, json={"penalty": False})
    state = client.app.state.jarvis
    assert state.conn.execute("select 1 from setting where key='gate_penalty'").fetchone() is not None
