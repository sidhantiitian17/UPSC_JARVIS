"""Focus Guard samples: category + app name only (never titles or URLs), summarised per day."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

SAMPLE_SECONDS = 5  # one sample is taken every 5 seconds while a focus block runs
CATEGORIES = ("study", "neutral", "distraction")


def add_samples(conn: sqlite3.Connection, samples: list[dict]) -> int:
    now = datetime.now(UTC).isoformat()
    conn.execute("begin")
    try:
        for s in samples:
            conn.execute(
                "insert into focus_sample(ts, category, app) values (?,?,?)",
                (s.get("ts") or now, s["category"], s["app"]),
            )
        conn.execute("commit")
    except Exception:
        conn.execute("rollback")
        raise
    return len(samples)


def _minutes(n: int) -> float:
    return round(n * SAMPLE_SECONDS / 60, 1)


def summary(conn: sqlite3.Connection, days: int = 7, now: datetime | None = None) -> dict:
    today = (now or datetime.now(UTC)).astimezone().date()
    first = today - timedelta(days=days - 1)
    per_day: dict[date, dict[str, int]] = defaultdict(lambda: dict.fromkeys(CATEGORIES, 0))
    apps: dict[str, int] = defaultdict(int)
    for r in conn.execute("select ts, category, app from focus_sample"):
        d = datetime.fromisoformat(r["ts"]).astimezone().date()
        if d < first or d > today:
            continue
        per_day[d][r["category"]] += 1
        if r["category"] == "distraction":
            apps[r["app"]] += 1
    out_days = []
    totals = dict.fromkeys(CATEGORIES, 0)
    for i in range(days):
        d = first + timedelta(days=i)
        c = per_day.get(d, dict.fromkeys(CATEGORIES, 0))
        for k in CATEGORIES:
            totals[k] += c[k]
        out_days.append(
            {
                "date": d.isoformat(),
                "study_minutes": _minutes(c["study"]),
                "neutral_minutes": _minutes(c["neutral"]),
                "distraction_minutes": _minutes(c["distraction"]),
            }
        )
    top = sorted(apps.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "days": out_days,
        "totals": {f"{k}_minutes": _minutes(totals[k]) for k in CATEGORIES},
        "top_distraction_apps": [{"app": a, "minutes": _minutes(n)} for a, n in top],
    }
