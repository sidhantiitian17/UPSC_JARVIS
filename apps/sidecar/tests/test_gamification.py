"""WU-P03-001: XP / level / streak / freeze (specs/gamification.feature)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.gamification.rules import DayStats, compute_progress, level_for, xp_for_level

D0 = date(2026, 11, 1)


def days(spec: dict[int, tuple[int, int]]) -> dict[date, DayStats]:
    """{offset_days: (verified_minutes, xp)}"""
    return {D0 + timedelta(days=k): DayStats(minutes=m, xp=x) for k, (m, x) in spec.items()}


def run(spec, today_offset, goal=30, bad=(), bad_goal=10):
    return compute_progress(
        days(spec), D0 + timedelta(days=today_offset), goal, {D0 + timedelta(days=b) for b in bad}, bad_goal
    )


def test_level_thresholds():
    assert [xp_for_level(n) for n in (1, 2, 3, 4)] == [0, 100, 300, 600]
    assert [level_for(x) for x in (0, 99, 100, 299, 300, 599, 600)] == [1, 1, 2, 2, 3, 3, 4]


def test_xp_level_and_progress_to_next():
    p = run({0: (40, 150), 1: (35, 100)}, 1)
    assert (
        p["xp_total"] == 250 and p["level"] == 2 and p["xp_into_level"] == 150 and p["xp_to_next_level"] == 50
    )


def test_streak_grows_on_goal_days_and_today_in_progress_does_not_break_it():
    p = run({0: (30, 10), 1: (45, 10), 2: (0, 0)}, 2)
    assert p["streak"] == 2 and p["today_minutes"] == 0 and p["at_risk"] is True


def test_today_reaching_the_goal_counts():
    p = run({0: (30, 10), 1: (30, 10), 2: (31, 10)}, 2)
    assert p["streak"] == 3 and p["at_risk"] is False


def test_a_missed_day_pauses_the_streak_without_a_freeze():
    p = run({0: (30, 1), 1: (30, 1), 2: (5, 0), 3: (30, 1)}, 3)
    assert p["streak"] == 1 and p["best_streak"] == 2
    assert any(e["kind"] == "streak_paused" for e in p["events"])


def test_seven_day_streak_earns_a_freeze_and_a_miss_uses_it():
    spec = {i: (30, 1) for i in range(7)}
    assert run(spec, 6)["freezes"] == 1
    spec[7] = (0, 0)  # missed
    spec[8] = (30, 1)
    p = run(spec, 8)
    assert p["freezes"] == 0 and p["streak"] == 8  # day 7 kept the streak without growing it, day 8 grew it
    assert [e["kind"] for e in p["events"] if e["kind"].startswith("freeze")] == [
        "freeze_earned",
        "freeze_used",
    ]


def test_freezes_are_capped_at_two():
    p = run({i: (30, 1) for i in range(21)}, 20)
    assert p["freezes"] == 2


def test_bad_day_uses_the_smaller_goal():
    spec = {0: (30, 1), 1: (12, 1), 2: (30, 1)}
    assert run(spec, 2, bad=[1])["streak"] == 3
    assert run(spec, 2)["streak"] == 1  # without bad-day mode day 1 (12 < 30) breaks it


def test_comeback_quest_after_a_lost_streak():
    spec = {i: (30, 1) for i in range(6)}  # 6-day streak
    spec[6] = (0, 0)  # lost
    p = run(spec, 6)
    assert p["streak"] == 0 or p["at_risk"]
    spec.update({7: (30, 1), 8: (30, 1)})
    mid = run(spec, 8)
    assert mid["comeback"] == {"active": True, "lost_streak": 6, "days_done": 2, "days_needed": 3}
    spec[9] = (30, 1)
    done = run(spec, 9)
    assert done["streak"] == 3 + 3 and done["comeback"]["active"] is False
    assert any(e["kind"] == "comeback_completed" for e in done["events"])


def test_short_streaks_do_not_open_a_comeback_quest():
    p = run({0: (30, 1), 1: (30, 1), 2: (0, 0), 3: (0, 0)}, 3)
    assert p["comeback"]["active"] is False


def test_events_are_dated_and_include_gate_xp_and_level_ups():
    p = run({0: (60, 120), 1: (30, 200)}, 1)
    kinds = [e["kind"] for e in p["events"]]
    assert kinds.count("gate_passed") == 2 and kinds.count("level_up") == 2  # 120 -> L2, 320 -> L3
    assert all("date" in e and "text" in e for e in p["events"])
    assert [e["date"] for e in p["events"]] == sorted(e["date"] for e in p["events"])


def test_no_history_is_a_calm_zero_state():
    p = run({}, 0)
    assert (p["xp_total"], p["level"], p["streak"], p["freezes"]) == (0, 1, 0, 0) and p["events"] == []


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app("t" * 32, data_dir=tmp_path / "d"))


H = {"Authorization": "Bearer " + "t" * 32}


def test_api_progress_defaults_and_goal_settings(client):
    assert client.get("/gamification/progress").status_code == 401
    p = client.get("/gamification/progress", headers=H).json()
    assert p["level"] == 1 and p["daily_goal_minutes"] == 60 and p["bad_day_goal_minutes"] == 20
    out = client.put(
        "/settings", headers=H, json={"daily_goal_minutes": 45, "bad_day_goal_minutes": 15}
    ).json()
    assert (out["daily_goal_minutes"], out["bad_day_goal_minutes"]) == (45, 15)
    assert client.put("/settings", headers=H, json={"daily_goal_minutes": 5}).status_code == 422
    assert client.get("/gamification/progress", headers=H).json()["daily_goal_minutes"] == 45
