# Roadmap

> Navigation: [Philosophy](../project/PHILOSOPHY.md) · [Usage](../project/USAGE.md) · [Design](../project/DESIGN.md) · [Tech Stack](../project/TECH_STACK.md) · [Log](log.md)

## Objective
UPSC JARVIS: a local-first, zero-cost, gamified desktop study OS for one UPSC aspirant. It verifies retention (recall gate + FSRS), tracks syllabus coverage honestly, and grows into PYQ analysis, Mains evaluation, current affairs, interview practice and a focus browser. See `docs/00-EVALUATION.md` and `docs/architecture.md`.

## 80/20 Focus
- Core outcome: **the Study Loop** (PDF → start/end bookmark → 50-min timer → recall gate → FSRS → honest coverage) — Phases 1–2.
- Highest-impact risks: (1) LLM-generated MCQ quality (A1 gate), (2) free-quota/provider churn (LLMClient + fallback ladder), (3) builder over-scope (phase-gated roadmap).
- Deferred intentionally: LightRAG, Telegram import, interview room, focus browser, Mains OCR, phone companion.

## Current Status
- Default branch: main
- Active phase: none
- Active Work Unit: none
- Latest completed unit: none
- Blockers: (1) `upsc.gov.in`, `huggingface.co`, `pib.gov.in`, `ncert.nic.in` still 403 from the running cloud session although owner says all domains are allowed. The owner's screenshot shows the claude.ai CHAT setting (Code execution > Network egress > All domains), which does not govern Claude Code cloud environments; the cloud environment's own Network access (session title bar > environment menu > Edit) must be changed — start a fresh session or run `uv run pyq run` locally; (1b) SweetClaude init blocked by the plugin's own health gate: cloud container has no `installed_plugins.json` (`SC_PLUGIN_OK=false`); owner approved init but the gate was not bypassed; run `/sweetclaude:init` on the owner's Windows laptop instead; it would add a second tracking system next to WUR); (2) GitHub default branch is currently `claude/gallant-volta-orla5n` (no `main` exists) — owner to create `main` and set it default (not done by agent: pushing other branches is not permitted); (3) repo is public: owner opted in (2026-11-01) to committing generated PYQ md (raw PDFs stay ignored) and will make the repo private after all work — history keeps anything committed meanwhile. Open questions: `docs/00-EVALUATION.md` §9

## Phases
| Phase | Goal | Status | File | Contract |
|---|---|---|---|---|
| 0 | Data & Decision-Brain track (official PYQ dataset incl. Sociology; laya spike, bake-off, conditional fine-tune) — parallel to 1–2 | planned | [PHASE_0](PHASE_0.md) | — |
| 1 | Foundation (walking skeleton: Electron + sidecar + SQLite + LLMClient) | planned | [PHASE_1](PHASE_1.md) | — |
| 2 | Study Loop MVP (bookmark, timer, recall gate, FSRS, honest coverage) | planned | [PHASE_2](PHASE_2.md) | — |
| 3 | Habit Engine (XP, pet, popups, guards, planner, Truth Dashboard) | planned | [PHASE_3](PHASE_3.md) | — |
| 4 | PYQ Lab (corpus, source mapping, split-view, trap stats, autopsy) | planned | [PHASE_4](PHASE_4.md) | — |
| 5 | Mains Studio (rubric, photo evaluation, handwriting remediation) | planned | [PHASE_5](PHASE_5.md) | — |
| 6 | Current Affairs Engine (RSS, digest, CA↔static links) | planned | [PHASE_6](PHASE_6.md) | — |
| 7 | Library, Telegram import & full Obsidian vault | planned | [PHASE_7](PHASE_7.md) | — |
| 8 | Focus Browser & AI side panel (+ Web Assist) | planned | [PHASE_8](PHASE_8.md) | — |
| 9 | Interview Room (silent AI) | planned | [PHASE_9](PHASE_9.md) | — |
| 10 | Planner++, mocks, Optional/Essay/Ethics, phone companion, backup | planned | [PHASE_10](PHASE_10.md) | — |

Phase 0 runs in parallel with Phases 1–2 (data/tooling only; no app code dependency). Phase 4 consumes the Phase 0 dataset.

Phase gating: do not start Phase 3 until Phase 2 gates A1 (≥40/50 good MCQs) and A2 (≥5/7 days) pass. Phases 4–10 may be reordered by the owner after Phase 3 based on dogfood evidence.

## Commit Index
| Work Unit | Summary | Commit | Verification |
|---|---|---|---|
| WU-TW-000 | Bootstrap agents/ workspace, WUR hooks, phases 1–10 | 24112e0 | hooks smoke-tested (commit-msg accept/reject) |
| WU-TW-001 | Evaluation report, architecture, features, BOM, AI strategy, UX strategy, playbook, specs, CLAUDE.md, README | f17a5e8 | docs-only: relative-link check (0 broken), counts re-derived from files |
| WU-TW-003 | Research docs: Brain/laya (06), PYQ dataset spec (07), repo brainstorm (08) | dc3704b | docs-only; every external fact traced to a command run this session |
| WU-TW-004 | Phase 0 roadmap, specs, Windows/ADR/rule updates, features/BOM/README/playbook | 6398a24 | docs-only: link check, feature recount |
| WU-TW-006 | Owner inputs recorded (hardware, dataset opt-in, network, sweetclaude) | 2ee4f35 | docs-only |
| WU-P00-001 | Manifest-driven polite fetcher | 7fefa2c | 10 tests pass in isolated worktree; status blocked (real-site run) |
| WU-P00-002 | PDF extraction + scanned/language detection | 1f89979 | 13 cumulative tests pass; ready-for-review |
| WU-P00-003 | Prelims parser + md renderer + schema | c91e49b | 21 cumulative; status blocked (real PDFs) |
| WU-P00-004 | Mains/Essay/Sociology parser | 53695a6 | 24 cumulative; status blocked (real PDFs) |
| WU-P00-005 | Validator + coverage report | d1d313c | 27 cumulative; ready-for-review |
| WU-P00-006 | Official-only keys + syllabus ingest | e583c78 | 30 cumulative; status blocked (real files) |
| WU-P00-007 | Review sample + verify + pipeline + CLI | 657c936 | 35 cumulative, ruff clean; ready-for-review |

## Operating Rules
- Work in Work Units only. One WU = one commit.
- Failed work becomes another execution round in `contracts/PHASE_{n}_CONTRACT.md`; do not create Phase Fix ledgers for new work.
- WU status lifecycle: `planned -> active -> ready-for-review -> accepted -> done`; agents stop at `ready-for-review` unless the client confirms.
- Append to `log.md` on every contract open, test status change, and phase close.
- Small task, verify, commit. Repeat.
