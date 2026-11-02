"""WU-P03-009: privacy panel (specs/privacy.feature)."""

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.privacy.service import CATEGORY_IDS, delete_category, summary

H = {"Authorization": "Bearer " + "t" * 32}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))


def conn_of(client):
    return client.app.state.jarvis.conn


def seed_everything(conn):
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "insert into document(sha256,path,title,page_count,added_at) values ('h','p','Book',5,?)", (now,)
    )
    conn.execute(
        "insert into chunk(document_id,page,ordinal,text,char_start,char_end) values (1,1,0,'text',0,4)"
    )
    sid = conn.execute(
        "insert into study_session(document_id,start_chunk_id,end_chunk_id,started_at,ended_at,focused_seconds,status) "
        "values (1,1,1,?,?,600,'done')",
        (now, now),
    ).lastrowid
    conn.execute(
        "insert into link(src_type,src_id,dst_type,dst_id,kind) values ('session',?,'node','gs2.polity','tag')",
        (str(sid),),
    )
    q = conn.execute(
        "insert into question(kind,source,stem,options_json,answer_index,status,created_at) "
        "values ('mcq','generated','Q?','[\"a\",\"b\",\"c\",\"d\"]',0,'active',?)",
        (now,),
    ).lastrowid
    conn.execute("insert into gate_question(session_id,question_id,position) values (?,?,0)", (sid, q))
    conn.execute(
        "insert into attempt(question_id,session_id,chosen_index,correct,answered_at) values (?,?,0,1,?)",
        (q, sid, now),
    )
    conn.execute(
        "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) values (?,1,1,100,1,0,5,?)",
        (sid, now),
    )
    cid = conn.execute(
        "insert into card(question_id,due,state_json,created_at) values (?,?,'{}',?)", (q, now, now)
    ).lastrowid
    conn.execute("insert into review_log(card_id,rating,reviewed_at) values (?,3,?)", (cid, now))
    conn.execute("insert into llm_cache(key,response_json,created_at) values ('k','{}',?)", (now,))
    conn.execute(
        "insert into llm_usage(ts,provider,model,task,status,cache_hit) values (?,'p','m','t','ok',0)", (now,)
    )


def counts(conn, *tables):
    return {t: conn.execute(f"select count(*) from {t}").fetchone()[0] for t in tables}


def test_summary_lists_categories_with_counts_and_locations(client):
    seed_everything(conn_of(client))
    s = summary(conn_of(client), data_dir="/data", vault_path="/vault", library_path="/lib")
    cats = {c["id"]: c for c in s["categories"]}
    assert set(cats) == set(CATEGORY_IDS) == {"library", "study_history", "review", "ai_cache", "focus"}
    assert cats["library"]["count"] == 1 and cats["study_history"]["count"] == 1
    assert cats["review"]["count"] == 1 and cats["ai_cache"]["count"] == 2
    assert all(c["where"] and c["retention"] for c in s["categories"])
    assert s["locations"] == {"data_dir": "/data", "vault_path": "/vault", "library_path": "/lib"}
    text = " ".join(s["notes"]).lower()
    assert "encrypted" in text and "this pc" in text and "ai request" in text


def test_library_category_warns_about_dependent_sessions(client):
    cats = {c["id"]: c for c in summary(conn_of(client), "/d", None, None)["categories"]}
    assert "sessions tied to those books" in cats["library"]["warning"].lower()


def test_deleting_study_history_keeps_everything_else(client):
    conn = conn_of(client)
    seed_everything(conn)
    delete_category(conn, "study_history")
    after = counts(
        conn,
        "study_session",
        "attempt",
        "gate_result",
        "gate_question",
        "document",
        "chunk",
        "card",
        "syllabus_node",
    )
    assert after["study_session"] == after["attempt"] == after["gate_result"] == after["gate_question"] == 0
    assert (
        after["document"] == 1 and after["chunk"] == 1 and after["card"] == 1 and after["syllabus_node"] > 0
    )
    assert conn.execute("select count(*) from link where src_type = 'session'").fetchone()[0] == 0


def test_deleting_review_removes_cards_and_logs_only(client):
    conn = conn_of(client)
    seed_everything(conn)
    delete_category(conn, "review")
    after = counts(conn, "card", "review_log", "question", "study_session")
    assert (
        after["card"] == after["review_log"] == 0 and after["question"] == 1 and after["study_session"] == 1
    )


def test_deleting_ai_cache_clears_cache_usage_and_queue(client):
    conn = conn_of(client)
    seed_everything(conn)
    conn.execute("insert into llm_queue(task,request_json,created_at) values ('t','{}','x')")
    delete_category(conn, "ai_cache")
    assert counts(conn, "llm_cache", "llm_usage", "llm_queue") == {
        "llm_cache": 0,
        "llm_usage": 0,
        "llm_queue": 0,
    }


def test_deleting_the_library_also_removes_sessions_tied_to_it(client):
    conn = conn_of(client)
    seed_everything(conn)
    delete_category(conn, "library")
    after = counts(conn, "document", "chunk", "study_session")
    assert after == {"document": 0, "chunk": 0, "study_session": 0}


def test_unknown_category_is_refused(client):
    with pytest.raises(KeyError):
        delete_category(conn_of(client), "everything")


def test_api_requires_confirmation_and_known_category(client):
    seed_everything(conn_of(client))
    assert client.get("/privacy/summary").status_code == 401
    assert client.delete("/privacy/review", headers=H).status_code == 422  # no confirm
    assert client.delete("/privacy/review?confirm=no", headers=H).status_code == 422
    assert counts(conn_of(client), "card")["card"] == 1
    assert client.delete("/privacy/nothing?confirm=yes", headers=H).status_code == 404
    out = client.delete("/privacy/review?confirm=yes", headers=H)
    assert out.status_code == 200 and {c["id"]: c["count"] for c in out.json()["categories"]}["review"] == 0


def test_api_summary_reports_configured_folders(client, tmp_path):
    vault = tmp_path / "v"
    vault.mkdir()
    client.put("/settings", headers=H, json={"vault_path": str(vault)})
    s = client.get("/privacy/summary", headers=H).json()
    assert s["locations"]["vault_path"] == str(vault.resolve()) and s["locations"]["data_dir"]
    assert json.dumps(s)  # serialisable
