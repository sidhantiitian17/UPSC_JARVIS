"""WU-P03-005 sidecar side: focus samples, summary, privacy (specs/focus-guard.feature)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.focus.service import SAMPLE_SECONDS, add_samples, summary

H = {"Authorization": "Bearer " + "t" * 32}
NOW = datetime(2026, 11, 5, 12, 0).astimezone()


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))


def enable(client):
    assert (
        client.put("/settings", headers=H, json={"focus_guard_enabled": True}).json()["focus_guard_enabled"]
        is True
    )


def test_off_by_default_and_refuses_samples(client):
    assert client.get("/settings", headers=H).json()["focus_guard_enabled"] is False
    r = client.post("/focus/samples", headers=H, json={"samples": [{"category": "study", "app": "Acrobat"}]})
    assert r.status_code == 409 and "off" in r.json()["detail"].lower()
    assert client.get("/focus/summary", headers=H).json()["enabled"] is False


def test_requires_token(client):
    assert client.post("/focus/samples", json={"samples": []}).status_code == 401
    assert client.get("/focus/summary").status_code == 401


def test_samples_are_stored_and_summarised(client):
    enable(client)
    now = datetime.now(UTC).isoformat()
    samples = (
        [{"ts": now, "category": "study", "app": "Acrobat"}] * 6
        + [{"ts": now, "category": "distraction", "app": "Steam"}] * 3
        + [{"ts": now, "category": "neutral", "app": "Explorer"}] * 3
    )
    out = client.post("/focus/samples", headers=H, json={"samples": samples})
    assert out.status_code == 200 and out.json()["stored"] == 12
    s = client.get("/focus/summary?days=7", headers=H).json()
    assert s["enabled"] is True and len(s["days"]) == 7
    today = s["days"][-1]
    per_min = SAMPLE_SECONDS / 60
    assert today["study_minutes"] == round(6 * per_min, 1) and today["distraction_minutes"] == round(
        3 * per_min, 1
    )
    assert s["top_distraction_apps"] == [{"app": "Steam", "minutes": round(3 * per_min, 1)}]
    assert s["totals"]["study_minutes"] == today["study_minutes"]


def test_only_category_and_app_name_are_accepted_never_titles(client):
    enable(client)
    r = client.post(
        "/focus/samples",
        headers=H,
        json={"samples": [{"category": "study", "app": "Chrome", "title": "My private email"}]},
    )
    assert r.status_code == 422  # unknown field: a title can never be stored
    bad = client.post("/focus/samples", headers=H, json={"samples": [{"category": "gaming", "app": "x"}]})
    assert bad.status_code == 422
    big = client.post(
        "/focus/samples", headers=H, json={"samples": [{"category": "study", "app": "x"}] * 201}
    )
    assert big.status_code == 422
    long_app = client.post(
        "/focus/samples", headers=H, json={"samples": [{"category": "study", "app": "a" * 100}]}
    )
    assert long_app.status_code == 422
    stored = client.app.state.jarvis.conn.execute("select count(*) from focus_sample").fetchone()[0]
    assert stored == 0


def test_summary_window_and_empty_state(client):
    conn = client.app.state.jarvis.conn
    s = summary(conn, 7, NOW)
    assert len(s["days"]) == 7 and s["totals"] == {
        "study_minutes": 0.0,
        "neutral_minutes": 0.0,
        "distraction_minutes": 0.0,
    }
    add_samples(conn, [{"ts": (NOW - timedelta(days=30)).isoformat(), "category": "study", "app": "A"}])
    assert summary(conn, 7, NOW)["totals"]["study_minutes"] == 0.0  # outside the window


def test_privacy_panel_counts_and_deletes_focus_samples(client):
    enable(client)
    now = datetime.now(UTC).isoformat()
    client.post(
        "/focus/samples", headers=H, json={"samples": [{"ts": now, "category": "study", "app": "A"}] * 4}
    )
    cats = {c["id"]: c for c in client.get("/privacy/summary", headers=H).json()["categories"]}
    assert cats["focus"]["count"] == 4
    after = client.delete("/privacy/focus?confirm=yes", headers=H).json()
    assert {c["id"]: c["count"] for c in after["categories"]}["focus"] == 0
