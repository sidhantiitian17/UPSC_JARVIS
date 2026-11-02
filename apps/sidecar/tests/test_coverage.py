"""WU-P02-011: honest coverage + dashboard (specs/coverage.feature)."""

from datetime import UTC, datetime, timedelta

import pytest
import yaml
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.coverage.service import coverage_nodes, dashboard_today
from jarvis.db.migrate import connect, migrate
from jarvis.syllabus.ontology import load_ontology, sync_ontology

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    nodes = [
        {
            "id": "s",
            "title": "Subject",
            "kind": "subject",
            "children": [
                {"id": "s.a", "title": "Topic A", "kind": "topic", "target_pages": 10},
                {"id": "s.b", "title": "Topic B", "kind": "topic", "target_pages": 20},
                {"id": "s.c", "title": "Topic C (no target)", "kind": "topic"},
            ],
        }
    ]
    (tmp_path / "o.yaml").write_text(yaml.safe_dump({"version": 1, "nodes": nodes}), encoding="utf-8")
    c = connect(":memory:")
    migrate(c)
    sync_ontology(c, load_ontology(tmp_path))
    c.execute(
        "insert into document(sha256,path,title,page_count,added_at,last_page) "
        "values ('x','p','Book',100,?,7)",
        (NOW.isoformat(),),
    )
    for page in range(1, 41):
        c.execute(
            "insert into chunk(document_id,page,ordinal,text,char_start,char_end) values (1,?,0,'t',0,1)",
            (page,),
        )
    yield c
    c.close()


def chunk(conn, page):
    return conn.execute("select id from chunk where page = ? and ordinal = 0", (page,)).fetchone()[0]


def session(
    conn,
    first,
    last,
    node,
    *,
    retention=None,
    passed=True,
    skipped=False,
    status="done",
    focused=3000,
    finished=None,
):
    cur = conn.execute(
        "insert into study_session(document_id,start_chunk_id,end_chunk_id,started_at,ended_at,"
        "focused_seconds,status) "
        "values (1,?,?,?,?,?,?)",
        (chunk(conn, first), chunk(conn, last), NOW.isoformat(), NOW.isoformat(), focused, status),
    )
    sid = cur.lastrowid
    conn.execute(
        "insert into link(src_type,src_id,dst_type,dst_id,kind) values ('session',?,'node',?,'tag')",
        (str(sid), node),
    )
    if retention is not None:
        conn.execute(
            "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) "
            "values (?,10,?,?,?,?,0,?)",
            (sid, retention // 10, retention, int(passed), int(skipped), (finished or NOW).isoformat()),
        )
    return sid


def node(conn, node_id):
    return {n["id"]: n for n in coverage_nodes(conn)}[node_id]


def test_retention_weighted_verified_pages_and_percent(conn):
    session(conn, 3, 5, "s.a", retention=80)
    n = node(conn, "s.a")
    assert n["verified_pages"] == 2.4 and n["percent"] == 24 and n["sessions"] == 1


def test_only_passed_gates_add_coverage(conn):
    session(conn, 1, 3, "s.a", retention=40, passed=False)  # failed gate
    session(conn, 1, 3, "s.a", retention=0, passed=False, skipped=True, status="skipped")
    session(conn, 1, 3, "s.a", status="gate")  # no result yet
    session(conn, 1, 3, "s.a", status="running")
    n = node(conn, "s.a")
    assert n["verified_pages"] == 0 and n["percent"] == 0 and n["sessions"] == 0


def test_overlapping_ranges_count_each_page_once_at_best_retention(conn):
    session(conn, 1, 3, "s.a", retention=70)
    session(conn, 3, 5, "s.a", retention=100)
    # pages 1,2 at .7 ; page 3 at max(.7,1.0)=1 ; pages 4,5 at 1.0
    assert node(conn, "s.a")["verified_pages"] == 4.4


def test_percent_is_capped_at_100(conn):
    session(conn, 1, 30, "s.a", retention=100)
    assert node(conn, "s.a")["percent"] == 100


def test_node_without_target_shows_pages_but_no_percent(conn):
    session(conn, 1, 4, "s.c", retention=100)
    n = node(conn, "s.c")
    assert n["verified_pages"] == 4 and n["percent"] is None and n["target_pages"] is None


def test_parents_roll_up_children(conn):
    session(conn, 1, 5, "s.a", retention=100)  # 5 of 10
    session(conn, 10, 14, "s.b", retention=100)  # 5 of 20
    session(conn, 20, 21, "s.c", retention=100)  # 2 pages, no target: not in the percent
    p = node(conn, "s")
    assert p["verified_pages"] == 12 and p["target_pages"] == 30 and p["percent"] == round(100 * 10 / 30)


def test_nothing_verified_yet(conn):
    assert all(n["verified_pages"] == 0 for n in coverage_nodes(conn))


def test_dashboard_counts_verified_minutes_from_passed_gates_only(conn):
    session(conn, 1, 3, "s.a", retention=80, focused=3000, finished=NOW)  # 50 min today
    session(
        conn, 4, 6, "s.a", retention=90, focused=1800, finished=NOW - timedelta(days=3)
    )  # 30 min, this week
    session(conn, 7, 9, "s.a", retention=40, passed=False, focused=3000, finished=NOW)  # failed: not counted
    session(conn, 10, 12, "s.a", retention=95, focused=3600, finished=NOW - timedelta(days=30))  # old
    d = dashboard_today(conn, NOW)
    assert d["verified_minutes_today"] == 50
    assert d["verified_minutes_week"] == 80
    assert len(d["heatmap"]) == 84 and d["heatmap"][-1]["minutes"] == 50
    assert sum(day["minutes"] for day in d["heatmap"]) == 50 + 30 + 60


def test_next_block_is_the_last_document_and_page(conn):
    assert dashboard_today(conn, NOW)["next_block"] is None
    session(conn, 1, 3, "s.a", retention=80)
    nb = dashboard_today(conn, NOW)["next_block"]
    assert nb == {"document_id": 1, "title": "Book", "page": 7}


def test_dashboard_flags_a_gate_that_is_waiting(conn):
    sid = session(conn, 1, 3, "s.a", status="gate")
    assert dashboard_today(conn, NOW)["awaiting_gate_session_id"] == sid


def test_coverage_api(tmp_path):
    client = TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))
    h = {"Authorization": "Bearer " + "t" * 32}
    assert client.get("/coverage/nodes").status_code == 401
    nodes = client.get("/coverage/nodes", headers=h).json()
    assert any(n["id"] == "gs2.polity" and n["verified_pages"] == 0 for n in nodes)
    d = client.get("/dashboard/today", headers=h).json()
    assert d["verified_minutes_today"] == 0 and len(d["heatmap"]) == 84 and d["next_block"] is None
