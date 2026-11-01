# Usage

## Read first (in order)
1. `CLAUDE.md` (rules + architecture block)
2. `docs/architecture.md`
3. `agents/project/PHILOSOPHY.md`, `DESIGN.md`, `TECH_STACK.md`
4. `agents/roadmap/ALL.md` then the active `PHASE_N.md`
5. `specs/*.feature` for the slice being built

## Commands
Commands below are **planned**; they are created in WU-P01-001 / WU-P01-007. Until then they do not exist.

| Purpose | Command |
|---|---|
| Install | `pnpm install` and `cd apps/sidecar && uv sync` |
| Dev (Electron + sidecar) | `pnpm dev` |
| Verify (lint + typecheck + tests, both sides) | `pnpm verify` |
| UI tests | `pnpm --filter desktop test` |
| Sidecar tests | `cd apps/sidecar && uv run pytest` |
| Sidecar lint | `cd apps/sidecar && uv run ruff check .` |

## Commit message conventions (enforced by `.githooks/`)
| Shape | Example |
|---|---|
| `WU-P{nn}-{nnn}: <description>` | `WU-P02-006: add start/end bookmark` |
| `WU-P{nn}-close/fix/abort: …` | administrative phase commits |
| `WU-TW-{k}: <description>` | tiny work units (docs, config) |
| `Phase {n}: merge <branch>` | phase merge |

Every implementation commit must stage the matching `agents/roadmap/` update. Implementation commits are blocked on the default branch (`main`).

## Guardrails
- Spec first: write/extend `specs/*.feature`, turn scenarios into failing tests, then code.
- New dependency: check `npm view`/`pip index` + LICENSE, record in `docs/02-REPO-BOM.md`.
- No direct provider calls; use `LLMClient`.
- No secrets in repo, logs, or vault files.
- Sidecar listens on `127.0.0.1` with a per-launch bearer token.
- Fresh verification output before claiming a WU is done. Agents stop at `ready-for-review`.
- Content that affects learning (ontology, PYQ tags, quotes) is reviewed by the owner before `verified = 1`.
