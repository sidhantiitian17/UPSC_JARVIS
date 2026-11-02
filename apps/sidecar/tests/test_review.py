"""WU-P02-010: FSRS cards + review queue (specs/review.feature, specs/retention-fsrs.feature)."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from fsrs import Card

from jarvis.app import create_app
from jarvis.db.migrate import connect, migrate
from jarvis.review.fsrs_service import (
    DEFAULT_DAILY_LIMIT,
    create_or_lapse_card,
    queue,
    rate_card,
)
from tests.test_gate import FakeLLM, H, finished_session, make
from tests.test_gate_scoring import answer, run_gate

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


@pytest.fixture
def conn():
    c = connect(":memory:")
    migrate(c)
    yield c
    c.close()


def question(conn, stem="Q?"):
    cur = conn.execute(
        "insert into question(kind,source,stem,options_json,answer_index,explanation,source_quote,"
        "status,created_at) "
        "values ('mcq','generated',?,?,1,'because','a verbatim quote here','active',?)",
        (stem, json.dumps(["a", "b", "c", "d"]), NOW.isoformat()),
    )
    return cur.lastrowid


def test_creating_a_card_schedules_it_with_fsrs(conn):
    qid = question(conn)
    card_id = create_or_lapse_card(conn, qid, "gs2.polity", NOW)
    row = conn.execute("select * from card where id = ?", (card_id,)).fetchone()
    parsed = Card.from_dict(json.loads(row["state_json"]))
    assert parsed.due.isoformat() == row["due"] or datetime.fromisoformat(row["due"]) == parsed.due
    assert datetime.fromisoformat(row["due"]) >= NOW and row["subject_id"] == "gs2.polity"


def test_a_second_wrong_answer_lapses_the_same_card_and_logs_again(conn):
    qid = question(conn)
    first = create_or_lapse_card(conn, qid, "gs2.polity", NOW)
    second = create_or_lapse_card(conn, qid, "gs2.polity", NOW + timedelta(days=1))
    assert first == second
    assert conn.execute("select count(*) from card").fetchone()[0] == 1
    logs = conn.execute("select rating from review_log where card_id = ?", (first,)).fetchall()
    assert [r["rating"] for r in logs] == [1]


def test_rating_reschedules_and_logs(conn):
    qid = question(conn)
    cid = create_or_lapse_card(conn, qid, "s", NOW)
    before = conn.execute("select due from card where id=?", (cid,)).fetchone()["due"]
    out = rate_card(conn, cid, 3, NOW + timedelta(minutes=2))
    assert datetime.fromisoformat(out["due"]) > datetime.fromisoformat(before)
    log = conn.execute("select * from review_log where card_id=?", (cid,)).fetchone()
    assert log["rating"] == 3 and log["scheduled_days"] is not None and json.loads(log["state_before_json"])


def test_again_schedules_sooner_than_good(conn):
    a, g = question(conn, "A?"), question(conn, "G?")
    ca, cg = create_or_lapse_card(conn, a, "s", NOW), create_or_lapse_card(conn, g, "s", NOW)
    t = NOW + timedelta(days=2)
    # graduate both once, then compare the next intervals
    rate_card(conn, ca, 3, t)
    rate_card(conn, cg, 3, t)
    t2 = t + timedelta(days=3)
    again = rate_card(conn, ca, 1, t2)
    good = rate_card(conn, cg, 3, t2)
    assert datetime.fromisoformat(again["due"]) < datetime.fromisoformat(good["due"])


def test_invalid_rating_is_rejected(conn):
    cid = create_or_lapse_card(conn, question(conn), "s", NOW)
    with pytest.raises(ValueError):
        rate_card(conn, cid, 5, NOW)
    with pytest.raises(KeyError):
        rate_card(conn, 999, 3, NOW)


def seed_cards(conn, n, subjects=("a", "b")):
    ids = []
    for i in range(n):
        qid = question(conn, f"Q{i}?")
        cid = create_or_lapse_card(conn, qid, subjects[i % len(subjects)], NOW - timedelta(days=1))
        conn.execute(
            "update card set due = ? where id = ?", ((NOW - timedelta(hours=n - i)).isoformat(), cid)
        )
        ids.append(cid)
    return ids


def test_queue_respects_default_daily_limit(conn):
    seed_cards(conn, 80)
    assert DEFAULT_DAILY_LIMIT == 40
    assert len(queue(conn, NOW)) == 40


def test_reviews_done_today_use_up_the_allowance(conn):
    ids = seed_cards(conn, 80)
    for cid in ids[:5]:
        rate_card(conn, cid, 3, NOW)
    assert len(queue(conn, NOW)) == 35


def test_daily_limit_is_configurable(conn):
    seed_cards(conn, 30)
    conn.execute("insert into setting(key,value_json) values ('review_daily_limit','12')")
    assert len(queue(conn, NOW)) == 12


def test_subjects_are_interleaved(conn):
    # 12 cards of subject a are due first, then 4 of b: without interleaving a would repeat 12 times
    ids_a = seed_cards(conn, 12, ("a",))
    ids_b = seed_cards(conn, 4, ("b",))
    for k, cid in enumerate(ids_a + ids_b):
        conn.execute(
            "update card set due = ? where id = ?", ((NOW - timedelta(hours=30 - k)).isoformat(), cid)
        )
    subjects = [c["subject"] for c in queue(conn, NOW)]
    assert set(subjects) == {"a", "b"}
    run = longest = 1
    for prev, cur in zip(subjects, subjects[1:], strict=False):
        run = run + 1 if cur == prev else 1
        longest = max(longest, run)
    assert longest <= 2 or subjects[-4:] == ["a"] * 4  # only the leftover tail may repeat


def test_suspended_future_and_reported_cards_are_excluded(conn):
    ids = seed_cards(conn, 4)
    conn.execute("update card set suspended = 1 where id = ?", (ids[0],))
    conn.execute("update card set due = ? where id = ?", ((NOW + timedelta(days=3)).isoformat(), ids[1]))
    qid = conn.execute("select question_id from card where id = ?", (ids[2],)).fetchone()[0]
    conn.execute("update question set status = 'reported' where id = ?", (qid,))
    assert [c["card_id"] for c in queue(conn, NOW)] == [ids[3]]


def test_queue_items_carry_what_a_review_needs(conn):
    seed_cards(conn, 1)
    item = queue(conn, NOW)[0]
    assert item["stem"] and len(item["options"]) == 4 and item["answer_index"] == 1
    assert item["explanation"] == "because" and item["source_quote"]


# ---------- end to end through the gate and the API ----------
def test_finishing_a_gate_creates_cards_for_wrong_answers_only(tmp_path):
    client = make(tmp_path, FakeLLM())
    sid, _ = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    n = len(g["questions"])
    for i, qq in enumerate(g["questions"]):
        answer(client, sid, qq["id"], i >= 3)  # first three wrong
    client.post(f"/sessions/{sid}/gate/finish", headers=H)
    state = client.app.state.jarvis
    cards = state.conn.execute("select * from card").fetchall()
    assert len(cards) == 3 and n > 3
    wrong = {qq["id"] for qq in g["questions"][:3]}
    assert {c["question_id"] for c in cards} == wrong
    assert all(c["subject_id"] == "gs2.polity" for c in cards)


def test_review_api(tmp_path):
    client = make(tmp_path, FakeLLM())
    sid, _ = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    for qq in g["questions"]:
        answer(client, sid, qq["id"], False)
    client.post(f"/sessions/{sid}/gate/finish", headers=H)
    assert client.get("/review/queue").status_code == 401
    # new cards are due within a minute: make them due now
    state = client.app.state.jarvis
    state.conn.execute("update card set due = ?", ((datetime.now(UTC) - timedelta(minutes=1)).isoformat(),))
    stats = client.get("/review/stats", headers=H).json()
    assert stats["due_now"] == len(g["questions"]) and stats["daily_limit"] == 40
    q = client.get("/review/queue", headers=H).json()
    assert len(q) == len(g["questions"])
    r = client.post(f"/review/cards/{q[0]['card_id']}/rate", headers=H, json={"rating": 3})
    assert r.status_code == 200 and r.json()["interval_days"] >= 0
    assert (
        client.post(f"/review/cards/{q[0]['card_id']}/rate", headers=H, json={"rating": 9}).status_code == 422
    )
    assert client.post("/review/cards/999/rate", headers=H, json={"rating": 3}).status_code == 404
    assert client.get("/review/stats", headers=H).json()["reviewed_today"] == 1


def test_run_gate_helper_is_importable():
    assert run_gate and TestClient and create_app  # keep shared helpers referenced
