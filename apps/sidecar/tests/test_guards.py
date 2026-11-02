"""WU-P03-006: sleep guard, burnout guard, bad-day mode (specs/guards.feature)."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.guards.rules import burnout_status, in_sleep_window, minutes_until_end

H = {"Authorization": "Bearer " + "t" * 32}


@pytest.mark.parametrize(
    "t,expected",
    [
        ("23:45", True),
        ("02:00", True),
        ("23:30", True),
        ("05:29", True),
        ("05:30", False),
        ("12:00", False),
        ("23:29", False),
    ],
)
def test_sleep_window_crossing_midnight(t, expected):
    h, m = map(int, t.split(":"))
    assert in_sleep_window(time(h, m), time(23, 30), time(5, 30)) is expected


def test_sleep_window_within_one_day():
    assert in_sleep_window(time(14, 0), time(13, 0), time(15, 0)) is True
    assert in_sleep_window(time(16, 0), time(13, 0), time(15, 0)) is False


def test_minutes_until_the_window_ends():
    assert minutes_until_end(time(23, 45), time(5, 30)) == 345
    assert minutes_until_end(time(2, 0), time(5, 30)) == 210


def hours(**by_offset):
    today = date(2026, 11, 5)
    return today, {today - timedelta(days=int(k[1:])): v for k, v in by_offset.items()}


def test_twelve_hour_day_raises_the_warning():
    today, days = hours(d0=12.0)
    s = burnout_status(days, today)
    assert s["warning"] is True and s["focused_hours_today"] == 12.0
    today, days = hours(d0=11.9)
    assert burnout_status(days, today)["warning"] is False


def test_five_heavy_days_raise_a_heavy_stretch_notice():
    today, days = hours(d0=9.0, d1=9.5, d2=10.0, d3=9.0, d4=9.2)
    assert burnout_status(days, today)["heavy_stretch"] is True
    today, days = hours(d0=9.0, d1=9.5, d2=8.0, d3=9.0, d4=9.2)
    assert burnout_status(days, today)["heavy_stretch"] is False


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))


def at(hh, mm):
    return datetime(2026, 11, 5, hh, mm).astimezone(UTC)


def seed_session(client, focused_seconds, when):
    state = client.app.state.jarvis
    state.conn.execute(
        "insert into document(sha256,path,title,page_count,added_at) values ('x','p','Book',10,?)",
        (when.isoformat(),),
    )
    did = state.conn.execute("select id from document").fetchone()[0]
    state.conn.execute(
        "insert into study_session(document_id,started_at,ended_at,focused_seconds,status) "
        "values (?,?,?,?, 'done')",
        (did, when.isoformat(), when.isoformat(), focused_seconds),
    )


def test_status_defaults_and_requires_token(client):
    assert client.get("/guard/status").status_code == 401
    s = client.get("/guard/status", headers=H).json()
    assert s["sleep"]["enabled"] is True and (s["sleep"]["start"], s["sleep"]["end"]) == ("23:30", "05:30")
    assert s["burnout"]["warning"] is False and s["bad_day"]["today_active"] is False


def test_sleep_guard_active_inside_the_window_and_can_be_turned_off(client):
    from jarvis.guards.service import status

    state = client.app.state.jarvis
    late = status(state.conn, datetime(2026, 11, 5, 23, 45).astimezone())
    assert late["sleep"]["active"] is True and late["sleep"]["minutes_until_end"] == 345
    noon = status(state.conn, datetime(2026, 11, 5, 12, 0).astimezone())
    assert noon["sleep"]["active"] is False
    client.put("/settings", headers=H, json={"sleep_guard_enabled": False})
    assert status(state.conn, datetime(2026, 11, 5, 23, 45).astimezone())["sleep"]["active"] is False


def test_sleep_settings_validate_time_format(client):
    assert (
        client.put("/settings", headers=H, json={"sleep_start": "22:15", "sleep_end": "06:00"}).status_code
        == 200
    )
    for bad in ("25:00", "9:5", "noon", ""):
        assert client.put("/settings", headers=H, json={"sleep_start": bad}).status_code == 422
    s = client.get("/guard/status", headers=H).json()
    assert (s["sleep"]["start"], s["sleep"]["end"]) == ("22:15", "06:00")


def test_burnout_warning_comes_from_todays_focused_time(client):
    seed_session(client, 12 * 3600, datetime.now(UTC))
    s = client.get("/guard/status", headers=H).json()
    assert s["burnout"]["warning"] is True and s["burnout"]["focused_hours_today"] >= 12


def test_bad_day_mode_toggles_for_today_and_changes_the_goal(client):
    s = client.put("/guard/bad-day", headers=H, json={"active": True}).json()
    assert s["bad_day"]["today_active"] is True
    p = client.get("/gamification/progress", headers=H).json()
    assert p["today_goal"] == p["bad_day_goal_minutes"] == 20
    client.put("/guard/bad-day", headers=H, json={"active": True})  # idempotent
    stored = client.app.state.jarvis.conn.execute(
        "select value_json from setting where key='bad_days'"
    ).fetchone()[0]
    assert stored.count(datetime.now().astimezone().date().isoformat()) == 1
    off = client.put("/guard/bad-day", headers=H, json={"active": False}).json()
    assert off["bad_day"]["today_active"] is False
    assert client.get("/gamification/progress", headers=H).json()["today_goal"] == 60


def test_old_bad_days_are_not_editable_and_do_not_pile_up(client):
    from jarvis.guards.service import set_bad_day

    state = client.app.state.jarvis
    long_ago = datetime(2026, 1, 1, 12, 0).astimezone()
    set_bad_day(state.conn, True, long_ago)
    set_bad_day(
        state.conn, False, datetime(2026, 1, 3, 12, 0).astimezone()
    )  # a later day cannot undo an earlier one
    stored = state.conn.execute("select value_json from setting where key='bad_days'").fetchone()[0]
    assert "2026-01-01" in stored


def test_guard_messages_are_supportive(client):
    from jarvis.guards.service import SUPPORTIVE_TEXTS

    banned = ("lazy", "fail", "shame", "behind", "weak", "pathetic")
    assert SUPPORTIVE_TEXTS and not any(w in t.lower() for t in SUPPORTIVE_TEXTS for w in banned)
