"""Pure rules for the sleep guard and the burnout guard (specs/guards.feature)."""

from __future__ import annotations

from datetime import date, time, timedelta

BURNOUT_DAY_HOURS = 12.0
HEAVY_DAY_HOURS = 9.0
HEAVY_STRETCH_DAYS = 5


def in_sleep_window(t: time, start: time, end: time) -> bool:
    """True when `t` is inside [start, end); the window may cross midnight."""
    if start <= end:
        return start <= t < end
    return t >= start or t < end


def minutes_until_end(t: time, end: time) -> int:
    now = t.hour * 60 + t.minute
    stop = end.hour * 60 + end.minute
    return (stop - now) % (24 * 60)


def burnout_status(hours_by_day: dict[date, float], today: date) -> dict:
    today_hours = hours_by_day.get(today, 0.0)
    stretch = all(
        hours_by_day.get(today - timedelta(days=i), 0.0) >= HEAVY_DAY_HOURS for i in range(HEAVY_STRETCH_DAYS)
    )
    return {
        "focused_hours_today": round(today_hours, 1),
        "warning": today_hours >= BURNOUT_DAY_HOURS,
        "heavy_stretch": stretch,
    }
