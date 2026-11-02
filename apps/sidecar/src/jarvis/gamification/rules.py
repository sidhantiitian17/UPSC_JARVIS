"""XP, levels, streaks and freezes as a pure function of daily verified minutes (specs/gamification.feature).

Replaying history from the data keeps the rules auditable: the event log is how every number was reached.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

FREEZE_EVERY = 7
MAX_FREEZES = 2
COMEBACK_MIN_LOST = 3
COMEBACK_DAYS = 3


@dataclass(frozen=True)
class DayStats:
    minutes: float  # verified retained minutes that day (passed gates only)
    xp: int  # XP awarded by passed gates that day


def xp_for_level(n: int) -> int:
    return 50 * n * (n - 1)


def level_for(xp: int) -> int:
    n = max(1, int((1 + math.sqrt(1 + 4 * xp / 50)) / 2))
    while xp_for_level(n + 1) <= xp:
        n += 1
    while n > 1 and xp_for_level(n) > xp:
        n -= 1
    return n


def compute_progress(
    days: dict[date, DayStats], today: date, goal: int, bad_days: set[date], bad_goal: int
) -> dict:
    events: list[dict] = []

    def log(d: date, kind: str, text: str) -> None:
        events.append({"date": d.isoformat(), "kind": kind, "text": text})

    xp_total = 0
    level = 1
    streak = best = freezes = lost = since_break = 0
    at_risk = False

    if days:
        d = min(days)
        while d <= today:
            s = days.get(d, DayStats(0, 0))
            threshold = bad_goal if d in bad_days else goal
            if s.xp > 0:
                xp_total += s.xp
                log(d, "gate_passed", f"Passed a recall gate: +{s.xp} XP")
                while level_for(xp_total) > level:
                    level += 1
                    log(d, "level_up", f"Level {level} reached")
            qualifies = s.minutes >= threshold
            if d == today and not qualifies:
                at_risk = streak > 0
            elif qualifies:
                streak += 1
                best = max(best, streak)
                if streak % FREEZE_EVERY == 0 and freezes < MAX_FREEZES:
                    freezes += 1
                    log(d, "freeze_earned", f"Streak freeze earned after {streak} days")
                if lost >= COMEBACK_MIN_LOST:
                    since_break += 1
                    if since_break == COMEBACK_DAYS:
                        streak = lost // 2 + COMEBACK_DAYS
                        best = max(best, streak)
                        log(d, "comeback_completed", f"Comeback complete: streak restored to {streak} days")
                        lost = since_break = 0
            elif streak > 0 and freezes > 0:
                freezes -= 1
                log(d, "freeze_used", f"Streak freeze used: your {streak}-day streak is safe")
            else:
                if streak > 0:
                    msg = (
                        f"Streak paused at {streak} days. A comeback quest is open."
                        if streak >= COMEBACK_MIN_LOST
                        else "Streak paused. A new one starts with your next goal day."
                    )
                    log(d, "streak_paused", msg)
                    if streak >= COMEBACK_MIN_LOST:
                        lost = streak
                    since_break = 0
                elif lost >= COMEBACK_MIN_LOST:
                    since_break = 0
                streak = 0
            d += timedelta(days=1)

    level = level_for(xp_total)
    today_stats = days.get(today, DayStats(0, 0))
    return {
        "xp_total": xp_total,
        "level": level,
        "xp_into_level": xp_total - xp_for_level(level),
        "xp_to_next_level": xp_for_level(level + 1) - xp_total,
        "streak": streak,
        "best_streak": best,
        "freezes": freezes,
        "at_risk": at_risk,
        "today_minutes": round(today_stats.minutes),
        "today_goal": bad_goal if today in bad_days else goal,
        "comeback": {
            "active": lost >= COMEBACK_MIN_LOST,
            "lost_streak": lost,
            "days_done": since_break if lost >= COMEBACK_MIN_LOST else 0,
            "days_needed": COMEBACK_DAYS,
        },
        "events": events,
    }
