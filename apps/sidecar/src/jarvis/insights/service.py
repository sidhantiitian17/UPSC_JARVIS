"""Truth Dashboard metrics: claimed vs verified time, calibration, pace forecast, weekly honesty report."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

DEFAULT_EXAM_DATE = "2028-05-28"  # assumed until the owner sets the real date in Settings
MIN_CALIBRATION_ANSWERS = 5
EXPECTED = {"G": "90%+", "A": "60-70%", "R": "10-30%"}
WINDOW_DAYS = 7
PACE_DAYS = 28


def _setting(conn: sqlite3.Connection, key: str):  # noqa: ANN202
    row = conn.execute("select value_json from setting where key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else None


def _local_date(iso: str) -> date:
    return datetime.fromisoformat(iso).astimezone().date()


def _claimed_by_day(conn: sqlite3.Connection) -> dict[date, float]:
    out: dict[date, float] = defaultdict(float)
    for r in conn.execute("select coalesce(ended_at, started_at) as at, focused_seconds from study_session"):
        out[_local_date(r["at"])] += r["focused_seconds"] / 3600
    return out


def _verified_by_day(conn: sqlite3.Connection) -> dict[date, float]:
    out: dict[date, float] = defaultdict(float)
    for r in conn.execute(
        "select g.finished_at, s.focused_seconds from gate_result g "
        "join study_session s on s.id = g.session_id "
        "where g.passed = 1 and g.skipped = 0"
    ):
        out[_local_date(r["finished_at"])] += r["focused_seconds"] / 3600
    return out


def _weekly(claimed: dict[date, float], verified: dict[date, float], today: date) -> dict:
    days = []
    for i in range(WINDOW_DAYS - 1, -1, -1):
        d = today - timedelta(days=i)
        days.append(
            {
                "date": d.isoformat(),
                "claimed_hours": round(claimed.get(d, 0.0), 1),
                "verified_hours": round(verified.get(d, 0.0), 1),
            }
        )
    c = sum(claimed.get(today - timedelta(days=i), 0.0) for i in range(WINDOW_DAYS))
    v = sum(verified.get(today - timedelta(days=i), 0.0) for i in range(WINDOW_DAYS))
    return {
        "days": days,
        "claimed_hours": round(c, 1),
        "verified_hours": round(v, 1),
        "verified_share": round(100 * v / c) if c > 0 else None,
    }


def _calibration(conn: sqlite3.Connection) -> list[dict]:
    rows = {
        r["confidence"]: r
        for r in conn.execute(
            "select confidence, count(*) as n, sum(correct) as ok from attempt "
            "where confidence in ('G','A','R') group by confidence"
        )
    }
    out = []
    for tag in ("G", "A", "R"):
        r = rows.get(tag)
        n = r["n"] if r else 0
        out.append(
            {
                "tag": tag,
                "answers": n,
                "accuracy": round(100 * r["ok"] / n) if n else None,
                "enough_data": n >= MIN_CALIBRATION_ANSWERS,
                "expected": EXPECTED[tag],
            }
        )
    return out


def _forecast(conn: sqlite3.Connection, verified: dict[date, float], today: date) -> dict:
    stored = _setting(conn, "exam_date")
    exam = date.fromisoformat(stored or DEFAULT_EXAM_DATE)
    days_left = max(0, (exam - today).days)
    minutes = sum(verified.get(today - timedelta(days=i), 0.0) for i in range(PACE_DAYS)) * 60
    avg = round(minutes / PACE_DAYS)
    return {
        "exam_date": exam.isoformat(),
        "assumed_exam_date": stored is None,
        "days_left": days_left,
        "avg_daily_verified_minutes": avg,
        "projected_verified_hours": round(avg * days_left / 60),
    }


def _report(weekly: dict, calibration: list[dict], forecast: dict) -> list[str]:
    lines: list[str] = []
    share = weekly["verified_share"]
    if share is None:
        lines.append(
            "No study time is recorded for the last 7 days yet. "
            "Your first recall gate will start the picture."
        )
    else:
        lines.append(
            f"In the last 7 days you verified {weekly['verified_hours']} h "
            f"of the {weekly['claimed_hours']} h "
            f"you claimed ({share}%)."
        )
        if share < 60 and weekly["claimed_hours"] >= 2:
            lines.append(
                "Claimed time is well above verified time. "
                "Shorter reading ranges followed by a gate often close the gap."
            )
    g = next(c for c in calibration if c["tag"] == "G")
    if g["enough_data"] and g["accuracy"] is not None and g["accuracy"] < 80:
        lines.append(
            f"When you feel confident and tag an answer Green, you are right {g['accuracy']}% of the time. "
            "Slowing down on sure answers can help."
        )
    lines.append(
        f"At {forecast['avg_daily_verified_minutes']} verified minutes a day you would reach about "
        f"{forecast['projected_verified_hours']} verified hours by {forecast['exam_date']}"
        + (" (assumed exam date: set the real one in Settings)." if forecast["assumed_exam_date"] else ".")
    )
    return lines


def truth(conn: sqlite3.Connection, now: datetime | None = None) -> dict:
    today = (now or datetime.now(UTC)).astimezone().date()
    claimed, verified = _claimed_by_day(conn), _verified_by_day(conn)
    weekly = _weekly(claimed, verified, today)
    calibration = _calibration(conn)
    forecast = _forecast(conn, verified, today)
    return {
        "weekly": weekly,
        "calibration": calibration,
        "forecast": forecast,
        "report": _report(weekly, calibration, forecast),
    }
