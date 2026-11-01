---
type: phase
status: planned
tags: [state-planned, phase, ui, data]
depends_on: ["[[roadmap/PHASE_5]]"]
---

# Phase 10 — Planner++, Tests, Optional/Essay/Ethics, Phone companion, Backup

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 10` time, after earlier phases teach us what is real.

## Goal
Exam-ready polish: backward planner, full mocks, CSAT, optional/essay/ethics, Telegram-bot phone nudges, backup/restore, Hindi/English UI.

## Success Criteria
1. Backward planner from exam date; missed-day rebalance; last-60-days mode
2. Prelims full mock (configurable negative marking), attempt-strategy simulator, CSAT module
3. Optional subject module (ontology import + rubric); Essay builder/evaluator; GS4 case-study framework
4. Telegram-bot companion (plan, quick MCQs) using a separate bot token
5. One-zip backup/restore; Hindi/English UI; sidecar version pinning

## Exit Gate
Full-length Prelims mock completed in app; backup restored on a clean machine; owner accepts. Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Multi-user, cloud sync.

## Dependencies
`[[roadmap/PHASE_5]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P10-001 | Backward planner + rebalance + last-60 mode | Algorithm + tests | sidecar planner | P5 accepted | scoped tests + manual check | planned | — |
| WU-P10-002 | Prelims mock + attempt simulator | Engine, negative marking config | sidecar + desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P10-003 | CSAT module | Comprehension/numeracy/reasoning drills | sidecar + desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P10-004 | Optional + Essay + GS4 modules | Ontology import; rubrics | config + sidecar | prev WU | scoped tests + manual check | planned | — |
| WU-P10-005 | Telegram-bot companion | Bot token in safeStorage; reminders + quick MCQs | sidecar bot | prev WU | scoped tests + manual check | planned | — |
| WU-P10-006 | Backup/restore + i18n + version pinning | Zip export/import; EN/HI strings | scripts + desktop | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
