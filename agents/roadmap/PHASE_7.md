---
type: phase
status: planned
tags: [state-planned, phase, legal, security]
depends_on: ["[[roadmap/PHASE_2]]"]
---

# Phase 7 — Library, Telegram import & full Obsidian vault

> Outline-level plan. Detailed acceptance criteria and scope are refined at `/wur:start 7` time, after earlier phases teach us what is real.

## Goal
Padhai ka material ek jagah: official sources downloader, aapke apne Telegram chats se import (rate-limited, no bypass), auto-ingest, aur full Obsidian second brain.

## Success Criteria
1. Official sources downloader (NCERT, Economic Survey, Budget, ARC, PIB...) with source URLs recorded
2. Telegram login wizard (api_id/hash + OTP) with **encrypted local session**
3. Channel picker, filetype filter, incremental sync, FloodWait-safe delays; **protected/forward-restricted content skipped**
4. Auto-ingest pipeline (text, chunks, index, tags, dedupe)
5. Vault: MOCs, backlinks, daily/monthly notes; optional OCR for scanned PDFs

## Exit Gate
Owner links own Telegram account, syncs 1 channel without FloodWait errors; restricted items correctly skipped (test). Security review passes. Fresh `pnpm verify`. Owner `accepted`.

## Out of Scope
Any channel lists, any bypass of protections.

## Dependencies
`[[roadmap/PHASE_2]]` accepted.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P07-001 | Official sources downloader | Per-source scripts with URL + date; checksum | sidecar library | P2 accepted | scoped tests + manual check | planned | — |
| WU-P07-002 | Telethon login wizard + secure session | OTP flow; session encrypted with `safeStorage`; logout deletes session | sidecar telegram, desktop | prev WU | scoped tests + manual check | planned | — |
| WU-P07-003 | Channel picker + incremental sync + rate limits | last_message_id per chat; random delay; concurrency cap; skip noforwards/protected | sidecar telegram | prev WU | scoped tests + manual check | planned | — |
| WU-P07-004 | Auto-ingest pipeline | Download -> extract -> chunk -> index -> tag; dedupe by sha256 | sidecar library | prev WU | scoped tests + manual check | planned | — |
| WU-P07-005 | Full vault: MOCs + backlinks | Notes link to nodes/books; idempotent regeneration | sidecar vault | prev WU | scoped tests + manual check | planned | — |
| WU-P07-006 | Optional OCR for scanned PDFs | Surya (weights licence noted); only on user request | sidecar ocr | prev WU | scoped tests + manual check | planned | — |

## Verification Strategy
Per WU: spec/test first, scoped checks. Phase closeout: full verify plus the exit-gate evidence recorded in `agents/research/`.
