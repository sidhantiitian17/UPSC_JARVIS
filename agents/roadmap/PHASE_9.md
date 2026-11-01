---
type: phase
status: planned
tags: [state-planned, phase, security, performance]
depends_on: ["[[roadmap/PHASE_4]]"]
---

# Phase 9 — Interview Room (silent AI)

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 9` time, after earlier phases teach us what is real.

## Goal
Silent interview practice: question on screen, aap awaaz mein jawab do, AI sirf dekhta aur sunta hai; practice score + coaching report.

## Success Criteria
1. DAF profile + DAF-based question generator
2. Silent UI: questions as text only; recording with explicit consent; video **not stored by default**
3. MediaPipe Tasks (JS): eye contact, posture, hand fidget, head pose metrics
4. faster-whisper transcript + wpm, pauses, filler words, pitch variation
5. Evaluator: content (facts, balance, ethics, structure) + coaching metrics -> **practice score**, timeline report

## Exit Gate
Same recorded answer scored 3x: content score range <= +/-10%. Owner finds report 'actionable' on 5 sessions. Runs on target laptop without freezing (heavy jobs sequenced). Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Real-time AI speech, 'predicted UPSC marks'.

## Dependencies
`[[roadmap/PHASE_4]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P09-001 | DAF form + analyzer | Structured DAF; per-line probable questions | sidecar interview, desktop | P4 accepted | scoped tests + manual check | planned | — |
| WU-P09-002 | Interview room UI + question flow | Silent mode; timer; consent prompt | desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P09-003 | Vision metrics (MediaPipe Tasks JS) | Gaze/head pose/posture/hands; calibration step | desktop renderer | prev WU | scoped tests + manual check | planned | — |
| WU-P09-004 | Audio capture + whisper + prosody | Record -> faster-whisper CPU -> wpm/pauses/fillers/pitch | sidecar audio | prev WU | scoped tests + manual check | planned | — |
| WU-P09-005 | Evaluator + report | Content rubric + metrics; practice score + range; timeline | sidecar interview | prev WU | scoped tests + manual check | planned | — |
| WU-P09-006 | Home-state pack + opinion bank | Owner-verified facts; balanced pros/cons | sidecar + content | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
