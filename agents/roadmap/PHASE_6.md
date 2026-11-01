---
type: phase
status: planned
tags: [state-planned, phase, data, legal]
depends_on: ["[[roadmap/PHASE_3]]"]
---

# Phase 6 — Current Affairs Engine

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 6` time, after earlier phases teach us what is real.

## Goal
Daily current affairs ko sirf legal/public sources se, UPSC-relevance filter, 3-line summary aur syllabus node se link ke saath.

## Success Criteria
1. RSS/public sources fetched respecting robots.txt; no paywall scraping
2. Dedupe + relevance score + summary (cached) + node tags
3. CA <-> static links; reverse-tracking prompt ('pehle ye static padho')
4. 35-minute newspaper mode + daily 10-Q CA quiz
5. Trackers: schemes/indices/reports and bills; monthly Obsidian compilation

## Exit Gate
7 din digest chalaya; owner rating: **>= 70% items 'relevant'**, news read time **<= 40 min/day**. Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Telegram, paywalled sources, LightRAG.

## Dependencies
`[[roadmap/PHASE_3]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P06-001 | RSS fetcher + dedupe + source registry | Source list in YAML; robots.txt respected; retry/backoff | sidecar ca | P3 accepted | scoped tests + manual check | planned | — |
| WU-P06-002 | Extraction + relevance + digest | Article text extraction; relevance via cheap tier; summary cached | sidecar ca | prev WU | scoped tests + manual check | planned | — |
| WU-P06-003 | Node tagging + CA<->static links | Tag to nodes; show linked static chapters | sidecar ca, link table | prev WU | scoped tests + manual check | planned | — |
| WU-P06-004 | CA UI + 35-min mode + CA quiz | Time-boxed reading UI; daily 10 Q | desktop CA | prev WU | scoped tests + manual check | planned | — |
| WU-P06-005 | Trackers + monthly compile | Scheme/index/report/bill tables; Obsidian monthly note | sidecar + vault | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
