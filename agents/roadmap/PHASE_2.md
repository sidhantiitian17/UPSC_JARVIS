---
type: phase
status: planned
tags: [state-planned, phase, study-loop, content-review, llm]
depends_on: ["[[roadmap/PHASE_1]]"]
---

# Phase 2 — Study Loop MVP (the heart)

## Goal
PDF kholo → start/end bookmark → 50-min timer → recall gate → FSRS → **honest** syllabus progress. Is phase ke baad aap roz isse padh sakte ho.

## Success Criteria
1. Aap ek PDF library mein add karke reader mein padh sakte ho; position restore hoti hai.
2. Start/end bookmark exact range (page + offset) save hota hai aur syllabus nodes se tag hota hai.
3. Timer khatam hote hi reader lock; gate 10–30 MCQ deta hai, har ek source quote + chunk ke saath (`specs/study-loop.feature`).
4. Gate fail par restudy advice (book, page, paragraph); gate pass par coverage badhta hai.
5. Galat jawab card ban kar FSRS queue mein jaata hai (`specs/retention-fsrs.feature`).
6. Today screen par due cards, next block, aur syllabus progress (verified %) dikhte hain.
7. Session aur cards Obsidian vault mein markdown ban kar likhe jaate hain.

## Exit Gate (human, measurable)
- **A1:** 50 random generated MCQs ko owner grade kare: **≥ 40 "sahi aur useful"**.
- **A2:** 7-din dogfood: **≥ 5 din** gate complete.
- Fresh `pnpm verify`. Owner `accepted`.
Agar A1 fail ho: prompts/validation badlo; Phase 3 shuru **nahi** hoga.

## Out of Scope
Pet, gamification beyond basic XP number, PYQ, Mains, CA, Telegram, browser, interview, LightRAG.

## Dependencies
`[[roadmap/PHASE_1]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P02-001 | Ontology schema + loader + tree view | YAML schema validated; unique ids; loads into `syllabus_node`; tree UI with expand/collapse | `config/syllabus/schema.*`, sidecar syllabus router, `apps/desktop` Syllabus screen | P1 | pytest (schema, uniqueness); UI test | ready-for-review | 609a9ca |
| WU-P02-002 | Ontology data A: Polity & Governance, Economy, History & Culture | Micro-themes down to leaf nodes; `source: draft` until owner review sets `reviewed: true` | `config/syllabus/*.yaml` | 001 | schema validation; **owner review** (`content-review`) | planned | — |
| WU-P02-003 | Ontology data B: Geography, Environment, S&T, IR, Security, Society, Ethics, Essay | Same as 002 | `config/syllabus/*.yaml` | 001 | schema validation; **owner review** | planned | — |
| WU-P02-004 | Library: add PDF + extraction + chunking + FTS | Drag-drop/picker; sha256 dedupe; page text via `pypdfium2` (license verified); chunks with page + offsets; FTS5 index; scanned-PDF detection (warn only) | sidecar library router, `apps/desktop` Library screen | P1 | pytest on fixture PDFs; dedupe test | ready-for-review | 368e3a1 |
| WU-P02-005 | PDF reader (pdf.js) | Open, page nav, zoom, text layer, dark mode, last-position restore | `apps/desktop` Reader | 004 | vitest + manual | ready-for-review | 764219e |
| WU-P02-006 | Start/End bookmark → study session + auto-tag | Range persisted (page + char offset); tagging via `LLMClient` (cached) → `link` rows; Source Budget alert (>3 sources per node) | sidecar sessions router, Reader UI | 005, 001 | pytest: offsets, tags (fake LLM); implements bookmark scenario | ready-for-review | 0c50d87 |
| WU-P02-007 | Focus timer + session state machine | 50/10 configurable; pause on system idle; lock reader at 0; keyboard shortcuts | desktop main + renderer | 006 | state-machine unit tests; manual | ready-for-review | 6f13442 |
| WU-P02-008 | Gate generation + validation (backend) | Adaptive N 10–30; 70/20/10 mix; JSON schema; each question has `source_chunk_id` within range + verbatim `source_quote` (substring-checked); invalid discarded; "report bad question" excludes it; Brain Context Pack v1 | sidecar gate router | 006, P1-005, P1-008 | pytest + golden tests (`specs/study-loop.feature` scenarios 3, 8) | planned | — |
| WU-P02-009 | Gate UI + scoring + restudy + G/A/R + emergency skip | Full-window gate; keyboard 1–4; G/A/R tag; retention %; restudy advice with page links; emergency skip doubles next gate; offline mini-quiz fallback | `apps/desktop` Gate | 007, 008 | UI tests + manual; scenarios 2, 4–7 | planned | — |
| WU-P02-010 | FSRS cards + review queue | `py-fsrs` (MIT); wrong answers → cards; daily limit; interleaving; review log | sidecar fsrs router, Review UI | 009 | pytest: schedule, limits; `specs/retention-fsrs.feature` | planned | — |
| WU-P02-011 | Honest coverage + Today dashboard | Coverage = f(range, recall); progress bars per node; heatmap; Today shows next block, due cards, verified % | sidecar coverage, desktop Today/Syllabus | 009, 010 | pytest: formula (gate fail does not raise coverage); UI | planned | — |
| WU-P02-012 | Obsidian mirror v1 | Daily note + session notes + card files written to vault; atomic writes; no secrets; configurable path | sidecar vault writer | 010 | pytest: file contents, atomicity; secret-scan | planned | — |
| WU-P02-013 | Ontology data C: **Sociology (Paper I & II)** | Built from the **official syllabus** ingested in WU-P00-006 (not from memory); thinkers/concepts as nodes with `kind: thinker|concept`; `reviewed: true` only after owner review | `config/syllabus/sociology*.yaml` | 001, WU-P00-006 | schema validation; **owner review** (`content-review`) | planned | — |

## Verification Strategy
Per WU: spec-derived failing test first, then code. Phase closeout: full `pnpm verify`, A1/A2 evidence in `agents/research/`, manual end-to-end session on a real PDF.
