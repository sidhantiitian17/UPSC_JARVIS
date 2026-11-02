---
type: phase
status: planned
tags: [state-planned, phase, habit, ui]
depends_on: ["[[roadmap/PHASE_2]]"]
---

# Phase 3 — Habit Engine (pet, XP, guards, planner)

## Goal
App ko "dost" jaisa banana jo padhai ko sticky banaye, bina shame ke: XP/streak, pet, motivation popups, Focus Guard, sleep/burnout guard, daily planner, aur Truth Dashboard.

## Success Criteria
1. XP verified minutes se milta hai; streak freeze aur bad-day mode kaam karte hain.
2. Popups sirf `verified = 1` quotes/facts dikhate hain, author/citation ke saath.
3. Pet (OpenPets) session events par react karta hai; Coach/Strict/Silent modes; language rules `docs/04-UX-STRATEGY.md` §9 ke hisab se.
4. Focus Guard (opt-in) local hai; sirf app-category store hoti hai.
5. Sleep guard, burnout guard, commitment contract.
6. Daily hour-wise plan banta hai; Truth Dashboard + weekly honesty report.

## Exit Gate (human, measurable)
- **A5:** 3 din Strict mode + 3 din Coach mode; owner ka stress/rating survey: Strict mein "stress ↑" na ho.
- Pet kabhi shame wali language use nahi karta (review of 20 sample messages).
- Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
PYQ, Mains, CA, Telegram, browser, interview, mobile.

## Dependencies
`[[roadmap/PHASE_2]]` accepted (including A1/A2).

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P03-001 | XP / level / streak / freeze model | XP from verified retained minutes; streak freeze; comeback quest; event log | sidecar gamification | P2 | pytest: rules table | ready-for-review | 7324283 |
| WU-P03-002 | Motivation popup engine + quote bank | `quote(text, author, citation, tags, verified)`; only `verified=1` shown; "Mains mein kaise use karein" line; owner reviews ≥ 100 seed entries | sidecar + desktop popup | 001 | pytest: unverified never returned; **owner review** (`content-review`) | planned | — |
| WU-P03-003 | OpenPets integration spike (**decided: use OpenPets**) | Windows installer running; `@open-pets/client` from Electron main over named-pipe IPC sends `react`/`say`; message limits respected; chosen pet's licence recorded; official plugins (Focus Buddy, Mood Check-in, Water Reminder, Anxiety Aid) enabled/configured; ADR with API-stability notes | `agents/docs/`, desktop main | P2 | spike report; licence verified; manual: pet reacts on session start | planned | — |
| WU-P03-004 | Pet adapter + modes + language rules | Events: session start, idle, gate pass/fail, level-up; Coach/Strict/Silent; message templates reviewed against rules; fallback: own transparent window if spike says so | desktop main | 003, 001 | unit tests on message rules; manual | planned | — |
| WU-P03-005 | Focus Guard (opt-in) | **ActivityWatch** (MPL-2.0, sidecar; verify Windows behaviour) or `active-win` as fallback — spike decides; categories study/neutral/distraction (rules first; head H8 later); stored locally; off by default | desktop main + sidecar | P2 | tests with fake window titles; privacy check | planned | — |
| WU-P03-006 | Sleep guard + burnout guard + bad-day mode | Configurable sleep window; ≥12h-day detector; bad-day minimum plan keeps streak | sidecar rules | 001 | pytest | ready-for-review | e9a7418 |
| WU-P03-007 | Daily planner v1 + commitment contract | Free hours input → subject-wise hour-wise plan from weak nodes + due cards; missed plan → tomorrow catch-up gate | sidecar planner, Today UI | P2 | pytest: plan constraints; UI | ready-for-review | 536f9a8 |
| WU-P03-008 | Truth Dashboard + weekly honesty report + forecast | Verified Retained Minutes, calibration chart, claimed vs verified hours, completion forecast vs exam date | desktop Insights | P2 | pytest: metrics; UI | planned | — |
| WU-P03-009 | Privacy panel | Shows what is stored, where, retention; one-click delete per category | desktop Settings | 005 | UI test | planned | — |

## Verification Strategy
Per WU: scoped tests. Phase closeout: full verify + A5 survey notes in `agents/research/`.
