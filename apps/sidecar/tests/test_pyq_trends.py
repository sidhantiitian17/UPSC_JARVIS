"""WU-P04-003: PYQ trends + Direction Drift Alert (specs/pyq-trends.feature)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.pyq.trends import drift, trends

H = {"Authorization": "Bearer " + "t" * 32}
NOW = datetime(2026, 11, 5, 12, 0).astimezone()


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))


def conn_of(c):
    return c.app.state.jarvis.conn


_n = iter(range(1, 10_000))


def add_q(conn, year, nodes, *, status="accepted", stem="Some stem"):
    qid = f"PRE-{year}-GS1-{next(_n):03d}"
    conn.execute(
        "insert into pyq(id,phase,year,paper,number,stem,options_json,status,updated_at) "
        "values (?, 'prelims', ?, 'gs-paper-1', ?, ?, '[]', 'parsed', 'x')",
        (qid, year, next(_n), stem),
    )
    for n in nodes:
        conn.execute(
            "insert into pyq_tag(pyq_id,node_id,status,source,created_at) values (?,?,?,'owner','x')",
            (qid, n, status),
        )
    return qid


def add_verified_minutes(conn, node, minutes, days_ago=1):
    when = NOW - timedelta(days=days_ago)
    conn.execute(
        "insert or ignore into document(sha256,path,title,page_count,added_at) values ('d','p','B',10,'x')"
    )
    did = conn.execute("select id from document").fetchone()[0]
    sid = conn.execute(
        "insert into study_session(document_id,started_at,ended_at,focused_seconds,status) "
        "values (?,?,?,?,'done')",
        (did, when.isoformat(), when.isoformat(), minutes * 60),
    ).lastrowid
    conn.execute(
        "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) "
        "values (?,10,9,90,1,0,5,?)",
        (sid, when.astimezone(UTC).isoformat()),
    )
    conn.execute(
        "insert into link(src_type,src_id,dst_type,dst_id,kind) values ('session',?,'node',?,'tag')",
        (str(sid), node),
    )


def test_weightage_per_subject_and_year_counts_only_accepted_tags(client):
    conn = conn_of(client)
    for _ in range(3):
        add_q(conn, 2022, ["gs2.polity"])
    add_q(conn, 2023, ["gs2.polity"])
    add_q(conn, 2023, ["gs3.economy"])
    add_q(conn, 2023, ["gs3.economy"], status="suggested")  # not counted
    add_q(conn, 2023, ["gs3.economy"], status="rejected")  # not counted
    t = trends(conn)
    by = {s["id"]: s for s in t["subjects"]}
    assert (
        by["gs2.polity"]["counts_by_year"] == {"2022": 3.0, "2023": 1.0} and by["gs2.polity"]["total"] == 4.0
    )
    assert by["gs3.economy"]["total"] == 1.0
    assert by["gs2.polity"]["share_pct"] == 80 and by["gs3.economy"]["share_pct"] == 20
    assert t["years"] == [2022, 2023]
    assert [s["id"] for s in t["subjects"]][0] == "gs2.polity"  # biggest first


def test_a_multi_tag_question_splits_its_weight(client):
    conn = conn_of(client)
    add_q(conn, 2024, ["gs2.polity", "gs3.economy"])
    by = {s["id"]: s for s in trends(conn)["subjects"]}
    assert by["gs2.polity"]["total"] == 0.5 and by["gs3.economy"]["total"] == 0.5
    assert by["gs2.polity"]["share_pct"] == 50


def test_tagging_coverage_is_reported(client):
    conn = conn_of(client)
    add_q(conn, 2023, ["gs2.polity"])
    add_q(conn, 2023, [])  # has text, untagged
    add_q(conn, 2023, [], stem="")  # no text: not counted as taggable
    t = trends(conn)
    assert (t["tagged_questions"], t["questions_with_text"], t["tagged_pct"]) == (1, 2, 50)


def test_empty_trends_are_calm(client):
    t = trends(conn_of(client))
    assert t["subjects"] == [] and t["tagged_questions"] == 0 and t["tagged_pct"] is None and t["years"] == []


def seed_enough(conn):
    for _ in range(24):
        add_q(conn, 2023, ["gs2.polity"])
    for _ in range(8):
        add_q(conn, 2023, ["gs3.economy"])
    # weightage: polity 75%, economy 25%


def test_not_enough_data_gives_no_alert(client):
    conn = conn_of(client)
    for _ in range(10):
        add_q(conn, 2023, ["gs2.polity"])
    add_verified_minutes(conn, "gs3.economy", 300)
    d = drift(conn, NOW)
    assert d["enough_data"] is False and d["alerts"] == [] and "not enough" in d["message"].lower()


def test_many_tagged_questions_but_almost_no_verified_time_gives_no_alert(client):
    conn = conn_of(client)
    seed_enough(conn)
    add_verified_minutes(conn, "gs3.economy", 30)
    d = drift(conn, NOW)
    assert d["enough_data"] is False and d["alerts"] == []


def test_under_served_subject_is_flagged(client):
    conn = conn_of(client)
    seed_enough(conn)
    add_verified_minutes(conn, "gs3.economy", 200)  # all time on economy (25% weight), none on polity (75%)
    d = drift(conn, NOW)
    assert d["enough_data"] is True
    kinds = {a["subject_id"]: a["kind"] for a in d["alerts"]}
    assert kinds["gs2.polity"] == "under_served"
    assert kinds.get("gs3.economy") in (None, "heavily_studied")
    polity = next(a for a in d["alerts"] if a["subject_id"] == "gs2.polity")
    assert polity["weight_share_pct"] == 75 and polity["time_share_pct"] == 0
    assert "next" in polity["text"].lower() or "try" in polity["text"].lower()


def test_balanced_time_raises_no_alert(client):
    conn = conn_of(client)
    seed_enough(conn)
    add_verified_minutes(conn, "gs2.polity", 150)
    add_verified_minutes(conn, "gs3.economy", 50)  # 75/25, same as the weightage
    d = drift(conn, NOW)
    assert d["enough_data"] is True and d["alerts"] == []
    rows = {r["subject_id"]: r for r in d["rows"]}
    assert rows["gs2.polity"]["weight_share_pct"] == 75 and rows["gs2.polity"]["time_share_pct"] == 75


def test_old_verified_time_does_not_count(client):
    conn = conn_of(client)
    seed_enough(conn)
    add_verified_minutes(conn, "gs3.economy", 400, days_ago=60)
    assert drift(conn, NOW)["enough_data"] is False


def test_alert_wording_is_supportive(client):
    conn = conn_of(client)
    seed_enough(conn)
    add_verified_minutes(conn, "gs3.economy", 300)
    text = " ".join(a["text"] for a in drift(conn, NOW)["alerts"]).lower()
    for banned in ("lazy", "fail", "shame", "behind", "weak", "pathetic", "predicted"):
        assert banned not in text


def test_api(client):
    assert client.get("/pyq/trends").status_code == 401
    conn = conn_of(client)
    add_q(conn, 2023, ["gs2.polity"])
    body = client.get("/pyq/trends", headers=H).json()
    assert body["subjects"][0]["id"] == "gs2.polity"
    d = client.get("/pyq/drift", headers=H).json()
    assert d["enough_data"] is False and set(d) >= {"enough_data", "message", "alerts", "rows"}
