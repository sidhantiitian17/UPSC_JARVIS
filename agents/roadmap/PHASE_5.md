---
type: phase
status: planned
tags: [state-planned, phase, llm, content-review]
depends_on: ["[[roadmap/PHASE_4]]"]
---

# Phase 5 — Mains Studio

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 5` time, after earlier phases teach us what is real.

## Goal
Mains answers ka rubric-based, no-mercy feedback: photo upload -> transcription -> evaluation -> improvement + handwriting remediation.

## Success Criteria
1. Rubric YAML (default + user-editable) with weights/penalties
2. Mains PYQ bank + timed topic/full tests
3. Photo upload -> preprocessing -> Gemini vision transcription
4. Evaluator: 2-pass median, **score range**, per-dimension remarks (intro, body, facts, linkage, diagram, conclusion, language, word limit, presentation)
5. Handwriting Remediation sheet from illegible-word detection; Topper-diff using owner-supplied copy

## Exit Gate
Same answer evaluated 3x: **range <= +/-1.5 marks** (10-marker). Owner rates 10 reports: **>= 8/10 'fair and actionable'**. Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Essay and Ethics modules (Phase 10), interview.

## Dependencies
`[[roadmap/PHASE_4]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P05-001 | Rubric schema + editor | YAML schema; default rubric; UI to edit weights/penalties; versioned | `config/rubric/`, Settings | P4 accepted | scoped tests + manual check | planned | — |
| WU-P05-002 | Mains question bank + timed tests | PYQ import (owner-verified), topic/full tests, timers (7/11 min per 10/15 marks) | sidecar mains, desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P05-003 | Photo upload + transcription | Deskew/contrast (OpenCV); Gemini vision via `LLMClient`; privacy notice (image leaves device) | sidecar mains | prev WU | scoped tests + manual check | planned | — |
| WU-P05-004 | Evaluator | Rubric-anchored prompts; 2-pass median; temperature 0; range output; golden tests | sidecar evaluator | prev WU | scoped tests + manual check | planned | — |
| WU-P05-005 | Handwriting remediation | Surya line confidence + OCR disagreement flags; red boxes; practice sheet export | sidecar + desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P05-006 | Topper-diff + daily 1-answer habit | Split view with owner copy; daily timer prompt | desktop | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
