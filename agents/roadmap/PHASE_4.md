---
type: phase
status: planned
tags: [state-planned, phase, content-review, data]
depends_on: ["[[roadmap/PHASE_3]]", "[[roadmap/PHASE_0]]"]
---

# Phase 4 — PYQ Lab (Prelims)

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 4` time, after earlier phases teach us what is real.

## Goal
PYQ ko syllabus se jodna, trap patterns ko apne data se measure karna, aur har PYQ ko aapki books ke paragraph se map karna.

## Success Criteria
1. Official UPSC PYQ PDFs se Prelims corpus bana aur **owner ne verify kiya** (year, Q, options, answer)
2. Har PYQ syllabus node se tagged (owner review)
3. Topic x year weightage chart; Direction Drift Alert
4. PYQ <-> aapki books ke paragraph mapping (embedding similarity), split-view mein highlight + PYQ tag
5. Trap Lab flags ke saath **aapka hit-rate**; Mistake Autopsy; 9-minute drill; Bouncer set; calibration chart

## Exit Gate
Owner 100 PYQ ka corpus spot-check kare: **>= 95/100 correct parse**. Split-view par 20 mapped PYQ mein se **>= 14 relevant** (70%). Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Mains PYQ, CA, LightRAG (trigger check hi hoga, build nahi).

## Dependencies
`[[roadmap/PHASE_3]]` accepted and `[[roadmap/PHASE_0]]` dataset (WU-P00-001…007) accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P04-001 | PYQ corpus importer + review UI | **Import the Phase 0 dataset** (`datasets/pyq/md`) into SQLite (idempotent, keeps `status`/`answer_source`); review UI over the Phase 0 verify workflow; owner marks verified | `config/pyq/`, sidecar pyq router, review UI | P3 accepted | scoped tests + manual check | ready-for-review | 36315b0 |
| WU-P04-002 | Tag PYQ to syllabus nodes | LLM suggestion + owner accept/reject | sidecar pyq, review UI | prev WU | scoped tests + manual check | ready-for-review | 718c099 |
| WU-P04-003 | Trend analysis + Direction Drift Alert | Weightage chart; drift rule uses time spent vs weightage | sidecar analytics, Insights | prev WU | scoped tests + manual check | planned | — |
| WU-P04-004 | Source mapping (PYQ <-> paragraphs) | Embeddings (sqlite-vec) top-k; similarity threshold configurable; stored in `link` | sidecar mapping | prev WU | scoped tests + manual check | planned | — |
| WU-P04-005 | Split-view compare + highlight | 2-3 pdf.js panes; open mapped page; highlight paragraph; PYQ tag + year | `apps/desktop` Compare | prev WU | scoped tests + manual check | planned | — |
| WU-P04-006 | Trap Lab + hit-rate stats | Regex/word-substitution/contradiction flags; per-flag accuracy from owner attempts | sidecar traps | prev WU | scoped tests + manual check | planned | — |
| WU-P04-007 | 9-min drill + Mistake Autopsy + Bouncers + calibration | Timer phases 2/5/2; 4-type autopsy form; bouncer tag; chart | desktop PYQ Lab | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
