"""WU-P03-008: Truth Dashboard metrics (specs/truth-dashboard.feature)."""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.insights.service import truth

H = {"Authorization": "Bearer " + "t" * 32}
NOW = datetime(2026, 11, 5, 18, 0).astimezone()


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))


def conn_of(client):
    return client.app.state.jarvis.conn


def add_session(conn, when, minutes, passed=None):
    """passed=None: no gate result; True/False: gate result with that outcome."""
    conn.execute(
        "insert into document(sha256,path,title,page_count,added_at) values (?, 'p','B',10,'x')",
        (str(when) + str(minutes),),
    )
    did = conn.execute("select max(id) from document").fetchone()[0]
    sid = conn.execute(
        "insert into study_session(document_id,started_at,ended_at,focused_seconds,status) "
        "values (?,?,?,?, 'done')",
        (did, when.isoformat(), when.isoformat(), minutes * 60),
    ).lastrowid
    if passed is not None:
        conn.execute(
            "insert into gate_result(session_id,total,correct,retention_pct,passed,skipped,xp,finished_at) "
            "values (?,10,?,?,?,0,5,?)",
            (sid, 9 if passed else 4, 90 if passed else 40, int(passed), when.astimezone(UTC).isoformat()),
        )
    return sid


def add_attempts(conn, sid, conf, right, total):
    for i in range(total):
        q = conn.execute(
            "insert into question(kind,source,stem,options_json,answer_index,status,created_at) "
            "values ('mcq','generated',?,'[\"a\",\"b\",\"c\",\"d\"]',0,'active','x')",
            (f"{sid}-{conf}-{i}-{conn.execute('select count(*) from question').fetchone()[0]}",),
        ).lastrowid
        conn.execute(
            "insert into attempt(question_id,session_id,chosen_index,correct,confidence,answered_at) "
            "values (?,?,0,?,?,'x')",
            (q, sid, int(i < right), conf),
        )


def test_claimed_versus_verified_hours(client):
    conn = conn_of(client)
    add_session(conn, NOW, 120, passed=True)  # 2h claimed, 2h verified
    add_session(conn, NOW - timedelta(days=1), 180, passed=False)  # 3h claimed, 0 verified
    add_session(conn, NOW - timedelta(days=2), 60, passed=None)  # 1h claimed (never gated)
    add_session(conn, NOW - timedelta(days=20), 600, passed=True)  # outside the 7-day window
    w = truth(conn, NOW)["weekly"]
    assert w["claimed_hours"] == 6.0 and w["verified_hours"] == 2.0 and w["verified_share"] == 33
    assert len(w["days"]) == 7 and w["days"][-1] == {
        "date": NOW.date().isoformat(),
        "claimed_hours": 2.0,
        "verified_hours": 2.0,
    }


def test_calibration_by_confidence_tag(client):
    conn = conn_of(client)
    sid = add_session(conn, NOW, 60, passed=True)
    add_attempts(conn, sid, "G", right=9, total=10)
    add_attempts(conn, sid, "A", right=3, total=10)
    add_attempts(conn, sid, "R", right=1, total=2)
    cal = {c["tag"]: c for c in truth(conn, NOW)["calibration"]}
    assert (cal["G"]["answers"], cal["G"]["accuracy"]) == (10, 90)
    assert (cal["A"]["answers"], cal["A"]["accuracy"]) == (10, 30)
    assert cal["R"]["enough_data"] is False and cal["G"]["enough_data"] is True
    assert (
        cal["G"]["expected"] == "90%+"
        and cal["A"]["expected"] == "60-70%"
        and cal["R"]["expected"] == "10-30%"
    )


def test_forecast_uses_real_pace_and_flags_an_assumed_exam_date(client):
    conn = conn_of(client)
    for d in range(28):  # 60 verified minutes every day for 28 days
        add_session(conn, NOW - timedelta(days=d), 60, passed=True)
    f = truth(conn, NOW)["forecast"]
    assert f["avg_daily_verified_minutes"] == 60 and f["assumed_exam_date"] is True
    assert f["days_left"] == (date.fromisoformat(f["exam_date"]) - NOW.date()).days
    assert f["projected_verified_hours"] == round(60 * f["days_left"] / 60)
    client.put("/settings", headers=H, json={"exam_date": "2028-05-28"})
    g = truth(conn, NOW)["forecast"]
    assert g["assumed_exam_date"] is False and g["exam_date"] == "2028-05-28"


def test_exam_date_setting_validates(client):
    assert (
        client.put("/settings", headers=H, json={"exam_date": "2028-05-28"}).json()["exam_date"]
        == "2028-05-28"
    )
    for bad in ("28-05-2028", "2028-13-01", "soon", ""):
        assert client.put("/settings", headers=H, json={"exam_date": bad}).status_code == 422


def test_report_is_plain_and_kind(client):
    conn = conn_of(client)
    sid = add_session(conn, NOW, 120, passed=False)
    add_session(conn, NOW - timedelta(days=1), 60, passed=True)
    add_attempts(conn, sid, "G", right=2, total=10)  # overconfident
    rep = truth(conn, NOW)["report"]
    text = " ".join(rep).lower()
    assert "verified" in text and "claimed" in text and "confident" in text
    for banned in ("lazy", "fail", "shame", "behind", "weak", "pathetic", "predicted"):
        assert banned not in text


def test_empty_state_is_calm(client):
    t = truth(conn_of(client), NOW)
    assert t["weekly"]["claimed_hours"] == 0 and t["weekly"]["verified_share"] is None
    assert all(c["answers"] == 0 for c in t["calibration"])
    assert t["report"]


def test_nothing_is_called_predicted_marks(client):
    import json

    assert "predicted" not in json.dumps(truth(conn_of(client), NOW)).lower()


def test_api(client):
    assert client.get("/insights/truth").status_code == 401
    body = client.get("/insights/truth", headers=H).json()
    assert set(body) == {"weekly", "calibration", "forecast", "report"}
