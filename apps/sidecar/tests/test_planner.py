"""WU-P03-007: daily planner + commitment contract (specs/planner.feature)."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.planner.service import build_plan, commit_plan, planner_status

H = {"Authorization": "Bearer " + "t" * 32}
NOW = datetime(2026, 11, 5, 9, 0).astimezone()


@pytest.fixture
def client(tmp_path):
    c = TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))
    # the frozen test ontology has no Prelims papers: add the starter subjects the planner falls back to
    for sid, title in (("pre.polity", "Polity"), ("pre.history", "History"), ("pre.economy", "Economy")):
        c.app.state.jarvis.conn.execute(
            "insert into syllabus_node(id,title,kind,paper) values (?,?,'subject','PRE-GS1')", (sid, title)
        )
    return c


def conn_of(client):
    return client.app.state.jarvis.conn


def seed_card(conn, n):
    for i in range(n):
        q = conn.execute(
            "insert into question(kind,source,stem,options_json,answer_index,status,created_at) "
            "values ('mcq','generated',?,'[\"a\",\"b\",\"c\",\"d\"]',0,'active','x')",
            (f"Q{i}",),
        ).lastrowid
        conn.execute(
            "insert into card(question_id,due,state_json,created_at,subject_id) "
            "values (?,?,'{}','x','gs2.polity')",
            (q, (NOW - timedelta(days=1)).astimezone(UTC).isoformat()),
        )


def seed_history(conn, subject_node, right, total):
    """A finished session tagged to a leaf under `subject_node` with `total` attempts, `right` correct."""
    conn.execute(
        "insert into document(sha256,path,title,page_count,added_at) values (?, 'p','Book',10,'x')",
        (subject_node,),
    )
    did = conn.execute("select max(id) from document").fetchone()[0]
    sid = conn.execute(
        "insert into study_session(document_id,started_at,ended_at,focused_seconds,status) "
        "values (?, 'x','x',3000,'done')",
        (did,),
    ).lastrowid
    conn.execute(
        "insert into link(src_type,src_id,dst_type,dst_id,kind) values ('session',?,'node',?,'tag')",
        (str(sid), subject_node),
    )
    for i in range(total):
        q = conn.execute(
            "insert into question(kind,source,stem,options_json,answer_index,status,created_at) "
            "values ('mcq','generated',?,'[\"a\",\"b\",\"c\",\"d\"]',0,'active','x')",
            (f"{subject_node}-{i}",),
        ).lastrowid
        conn.execute(
            "insert into attempt(question_id,session_id,chosen_index,correct,answered_at) "
            "values (?,?,0,?,'x')",
            (q, sid, int(i < right)),
        )


def total_minutes(plan):
    return sum(b["minutes"] for b in plan["blocks"])


@pytest.mark.parametrize("hours", [1, 2, 3.5, 6, 12])
def test_plan_never_exceeds_the_free_time(client, hours):
    plan = build_plan(conn_of(client), hours, NOW)
    assert 0 < plan["planned_minutes"] <= hours * 60 and plan["planned_minutes"] == total_minutes(plan)
    assert all(b["minutes"] >= 10 for b in plan["blocks"])
    assert all(b["minutes"] >= 25 for b in plan["blocks"] if b["kind"] == "study")


def test_due_cards_get_a_review_block_first_and_capped_at_a_quarter(client):
    conn = conn_of(client)
    seed_card(conn, 12)
    plan = build_plan(conn, 4, NOW)
    first = plan["blocks"][0]
    assert first["kind"] == "review" and first["minutes"] == 12
    seed_card(conn, 200)
    big = build_plan(conn, 2, NOW)["blocks"][0]
    assert big["kind"] == "review" and big["minutes"] <= 0.25 * 120


def test_no_review_block_without_due_cards(client):
    assert all(b["kind"] != "review" for b in build_plan(conn_of(client), 3, NOW)["blocks"])


def test_study_blocks_go_to_the_weakest_subjects_first(client):
    conn = conn_of(client)
    seed_history(conn, "gs2.polity", right=2, total=10)  # 20% recall: weakest
    seed_history(conn, "gs3.economy", right=9, total=10)  # 90%
    plan = build_plan(conn, 5, NOW)
    study = [b for b in plan["blocks"] if b["kind"] == "study"]
    assert study[0]["subject_id"] == "gs2.polity" and "20%" in study[0]["reason"]
    ids = [b["subject_id"] for b in study]
    assert ids.count("gs2.polity") >= ids.count("gs3.economy") >= 0


def test_without_history_the_prelims_starter_subjects_are_used(client):
    plan = build_plan(conn_of(client), 4, NOW)
    study = [b for b in plan["blocks"] if b["kind"] == "study"]
    assert study and all(b["subject_id"].startswith("pre.") for b in study)
    assert all("starter" in b["reason"] for b in study)


def test_breaks_follow_focus_blocks_when_time_allows(client):
    plan = build_plan(conn_of(client), 4, NOW)
    kinds = [b["kind"] for b in plan["blocks"]]
    assert "break" in kinds
    assert kinds[-1] != "break"
    brk = next(b for b in plan["blocks"] if b["kind"] == "break")
    assert brk["minutes"] == 10


def test_api_validates_free_hours(client):
    for bad in (0.5, 0, 17, -1):
        assert client.post("/planner/plan", headers=H, json={"free_hours": bad}).status_code == 422
    assert client.post("/planner/plan", json={"free_hours": 3}).status_code == 401
    ok = client.post("/planner/plan", headers=H, json={"free_hours": 3}).json()
    assert ok["planned_minutes"] <= 180 and ok["blocks"]


def test_commit_is_remembered_for_today(client):
    conn = conn_of(client)
    plan = build_plan(conn, 3, NOW)
    commit_plan(conn, plan, NOW)
    st = planner_status(conn, NOW)
    assert st["committed_today"]["study_minutes"] == sum(
        b["minutes"] for b in plan["blocks"] if b["kind"] == "study"
    )
    out = client.post("/planner/commit", headers=H, json={"free_hours": 3})
    assert (
        out.status_code == 200
        and client.get("/planner/status", headers=H).json()["committed_today"] is not None
    )


def seed_verified(conn, day_dt, minutes):
    conn.execute(
        "insert into document(sha256,path,title,page_count,added_at) values (?, 'p','B',10,'x')",
        (str(day_dt),),
    )
    did = conn.execute("select max(id) from document").fetchone()[0]
    sid = conn.execute(
        "insert into study_session(document_id,started_at,ended_at,focused_seconds,status) "
        "values (?,?,?,?,'done')",
        (did, day_dt.isoformat(), day_dt.isoformat(), minutes * 60),
    ).lastrowid
    conn.execute(
        "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) "
        "values (?,10,9,90,1,0,10,?)",
        (sid, day_dt.astimezone(UTC).isoformat()),
    )


def commit_yesterday(conn, study_minutes):
    key = f"plan:{(NOW - timedelta(days=1)).date().isoformat()}"
    conn.execute(
        "insert into setting(key,value_json) values (?,?)",
        (key, json.dumps({"study_minutes": study_minutes, "blocks": []})),
    )


def test_missed_commitment_becomes_a_catch_up_block(client):
    conn = conn_of(client)
    commit_yesterday(conn, 200)
    seed_verified(conn, NOW - timedelta(days=1), 60)  # 60 of 200 verified: under 70%
    st = planner_status(conn, NOW)
    assert st["yesterday"] == {"committed_minutes": 200, "verified_minutes": 60, "missed": True}
    assert st["catch_up_due"] is True
    plan = build_plan(conn, 3, NOW)
    assert plan["blocks"][0]["kind"] == "catch_up" and plan["catch_up"] is True
    assert "gentle" in plan["notes"][0].lower() or "catch" in plan["notes"][0].lower()


def test_meeting_the_commitment_gives_no_catch_up(client):
    conn = conn_of(client)
    commit_yesterday(conn, 100)
    seed_verified(conn, NOW - timedelta(days=1), 80)
    assert planner_status(conn, NOW)["catch_up_due"] is False
    assert all(b["kind"] != "catch_up" for b in build_plan(conn, 3, NOW)["blocks"])


def test_no_commitment_yesterday_means_no_catch_up(client):
    assert planner_status(conn_of(client), NOW)["catch_up_due"] is False
