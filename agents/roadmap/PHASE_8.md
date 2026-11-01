---
type: phase
status: planned
tags: [state-planned, phase, security, legal]
depends_on: ["[[roadmap/PHASE_2]]"]
---

# Phase 8 — Focus Browser & AI side panel

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 8` time, after earlier phases teach us what is real.

## Goal
Distraction-free embedded browser: Shorts band, feed hidden, ads blocked, allowlisted lectures, AI side panel, aur human-in-loop Web Assist.

## Success Criteria
1. Embedded browser (WebContentsView, isolated session, sandbox, no nodeIntegration)
2. YouTube Shorts blocked at URL level + CSS hide; recommendations/feed hidden
3. Ghostery ad-blocking; package/licence verified
4. Channel allowlist + LLM relevance gate on title/description
5. AI side panel with timestamped notes -> Obsidian; Web Assist capture (human-in-loop)

## Exit Gate
Owner 5 din YouTube sirf is browser se use kare; Shorts ek bhi load na ho; ad-blocking failure mode (anti-adblock) ka fallback tested. Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Full-auto web-chat automation (experimental flag only, default OFF, separate decision).

## Dependencies
`[[roadmap/PHASE_2]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P08-001 | Embedded browser + session isolation | WebContentsView; permissions deny-by-default | desktop main | P2 accepted | scoped tests + manual check | planned | — |
| WU-P08-002 | Shorts ban + feed hide | webRequest + will-navigate + CSS injection | desktop main | prev WU | scoped tests + manual check | planned | — |
| WU-P08-003 | Ad-blocking | Ghostery integration; update lists; failure fallback | desktop main | prev WU | scoped tests + manual check | planned | — |
| WU-P08-004 | Allowlist + relevance gate | User-managed channel list; LLM classify; cache | sidecar + desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P08-005 | AI side panel + timestamped notes | Transcript (if available) + notes to vault | desktop + sidecar | prev WU | scoped tests + manual check | planned | — |
| WU-P08-006 | Web Assist capture | Prompt to clipboard; Capture button reads DOM; import markdown | desktop | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
