---
type: phase
status: planned
tags: [state-planned, phase, infra, llm]
---

# Phase 1 — Foundation (Walking Skeleton)

## Goal
Ek khaali par **chalta hua** app: Electron window khule, Python sidecar secure tareeke se chale, SQLite migrate ho, aur "Test AI" button ek AI tier se jawab laye (fallback ladder ke saath). Koi UPSC content nahi.

## Success Criteria
1. `pnpm dev` Electron app kholta hai; sidebar mein saari screens placeholder ke roop mein hain.
2. Sidecar `/health` OK deta hai; bina bearer token ke `401`.
3. DB migrations up/down chalte hain; FTS5 aur sqlite-vec verify hue.
4. "Test AI" kam se kam ek tier se text laata hai; fallback/caching/schema-retry fake providers ke saath tested hain.
5. Secrets `safeStorage` mein; koi key repo/log mein nahi.
6. `pnpm verify` local aur CI dono mein green.

## Exit Gate
Owner apni machine par app chalata hai, "Test AI" dabata hai, aur fresh `pnpm verify` output attach hota hai. Owner `accepted` karta hai.

## Out of Scope
PDF, syllabus content, recall gate, pet, Telegram, browser, interview, Mains.

## Dependencies
None (`docs/architecture.md`, `agents/project/*`).

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P01-001 | Monorepo scaffold | pnpm workspace (`apps/desktop`, `apps/sidecar`, `packages/shared`); ESLint, Prettier, strict tsconfig, ruff, pytest, vitest; root `pnpm verify` runs both sides; README ke 5 lines | root configs, `apps/*`, `packages/*` | — | `pnpm verify` green | ready-for-review | — |
| WU-P01-002 | Electron shell + design tokens | Screens: Today, Study, Syllabus, PYQ, Mains, CA, Interview, Browser, Insights, Settings (placeholders with empty states); Tailwind + shadcn; tokens from `DESIGN.md`; `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false` | `apps/desktop/**` | 001 | UI render tests; manual launch; contrast check vs WCAG AA | ready-for-review | — |
| WU-P01-003 | Sidecar + secure IPC | FastAPI `/health`; Electron spawns sidecar on random port, `127.0.0.1` only, per-launch bearer token; sidecar stops with app; typed TS client from OpenAPI | `apps/sidecar/**`, `apps/desktop/src/main/**`, `packages/shared` | 001 | pytest (401 without token); vitest client; manual start/stop | ready-for-review | — |
| WU-P01-004 | SQLite schema v1 + migrations | Tables: `syllabus_node, link, document, chunk (+FTS5), study_session, question, attempt, card, review_log, llm_cache, llm_usage, setting`; sqlite-vec verified (+LICENSE noted in BOM); migrate up/down | `apps/sidecar/jarvis/db/**` | 003 | pytest: migrations, FTS5 query, recursive CTE on `syllabus_node` | planned | — |
| WU-P01-005 | `LLMClient` + routing + ledger | `complete(task, messages, schema?)`; `config/routing.yaml` task→tier; providers: OmniRoute (`localhost:20128`), Ollama, Gemini direct; sha256 cache; `llm_usage` ledger; fallback ladder; schema validate + 1 repair retry; implements `specs/llm-gateway.feature` | `apps/sidecar/jarvis/llm/**`, `config/routing.yaml` | 004 | pytest with fake providers for every scenario in `specs/llm-gateway.feature` | planned | — |
| WU-P01-006 | Settings + secrets + folder pickers | Settings screen: AI providers (free/credit label, credit disabled by default), "Test AI" button, library path, vault path; secrets in `safeStorage` | `apps/desktop/src/**`, sidecar settings router | 002, 003, 005 | vitest; manual: restart keeps settings, no secrets on disk in plain text | planned | — |
| WU-P01-007 | CI | GitHub Actions: lint, typecheck, vitest, pytest on push/PR; Actions pinned by SHA; least-privilege token | `.github/workflows/**` | 001 | CI run green on branch | planned | — |
| WU-P01-008 | LLM eval harness | Golden fixtures + JSON-schema checks + score report for prompt templates; one sample task wired | `apps/sidecar/tests/golden/**` | 005 | `uv run pytest -m golden` | planned | — |

## Verification Strategy
Per WU: scoped tests + lint/typecheck of the touched surface. Phase closeout: full `pnpm verify`, CI green, manual launch checklist (window opens, Test AI works, restart persists settings).
