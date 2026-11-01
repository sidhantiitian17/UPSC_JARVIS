# UPSC JARVIS — Agent Instructions

Local-first, zero-cost, gamified desktop study OS for one UPSC aspirant. Read order: this file → `docs/architecture.md` → `agents/project/*` → `agents/roadmap/ALL.md` → active `PHASE_N.md` → `specs/*.feature`.

## Workflow (WUR + spec-first)
- One Work Unit = one commit. Message: `WU-P{nn}-{nnn}: <description>` (enforced by `.githooks/`).
- Write/extend the Gherkin in `specs/` first, turn scenarios into failing tests, then implement (red → green → refactor).
- Stop at `ready-for-review`; only the owner marks `accepted`/`done`.
- Every implementation commit stages its `agents/roadmap/` update.
- Do not push to or commit implementation on `main`; work on the designated feature branch.
- User-facing explanations to the owner are in Hinglish; code, commits and agent rules stay in English.

<!-- planfirst:start -->
## Architecture Reference
Full spec: `./docs/architecture.md` — read before adding any infrastructure.

### Stack (momento: validate)
- Desktop shell: Electron + Vite + React + TypeScript + Tailwind + shadcn/ui
- Backend: one Python 3.11+ FastAPI sidecar (uv), loopback + per-launch token
- Storage: SQLite (WAL) + FTS5 + sqlite-vec; syllabus tree + `link` table = knowledge graph
- AI: `LLMClient` → OmniRoute (sidecar) | Ollama | Gemini free key
- Decision Brain: `DecisionClient` → rules | baseline | laya (only heads that win the Phase 0 bake-off)
- Target OS: Windows 10/11 (LF endings enforced via `.gitattributes`; Python 3.11/3.12)
- PDF: pdf.js · Spaced repetition: py-fsrs · Pet: OpenPets (external) · Vault: plain markdown

### Agent Rules
- DO NOT add PostgreSQL, Redis, Kafka, Kubernetes, or any queue/broker. SQLite is the only datastore until multi-user exists.
- DO NOT call any LLM provider directly. All LLM traffic MUST go through `LLMClient` in `apps/sidecar/jarvis/llm/`.
- DO NOT copy code from repositories without an OSI license (`upsc-os`, `UPSC-Star`, `UPSC-Answer-Generator`, `prelimspattern`). Re-implement from the spec instead.
- DO NOT add LightRAG, Telethon, faster-whisper, MediaPipe, open-browser-use, or an adblocker before the phase that lists them in `agents/roadmap/`.
- DO NOT use decision heads (laya or baselines) for text generation. Access them only through `DecisionClient` with a rules/LLM fallback, and only for heads the Phase 0 bake-off adopted.
- DO NOT commit PYQ PDFs or generated PYQ markdown while the repository is public; datasets live in gitignored `datasets/pyq/`. Every PYQ must carry an official `source_url` and `source_sha256`; never use third-party or LLM-generated PYQ sources.
- DO NOT fill an answer key from an LLM. LLM guesses go only in `suggested_answer` (unverified) and are never used for scoring or as gold labels.
- DO NOT write scripts that assume POSIX paths or LF/CRLF; the target OS is Windows.
- DO NOT implement any bypass for Telegram protected/forward-restricted content, paywalls, or captchas.
- DO NOT scrape paywalled sites. Use RSS/public pages and respect robots.txt.
- DO NOT ship an LLM-generated MCQ without `source_chunk_id`, a verbatim `source_quote`, and a passing validation step.
- DO NOT show an LLM-generated quote/fact in the motivation popups unless `verified = 1` (human reviewed).
- DO NOT store secrets in plain files; use Electron `safeStorage`. Sidecar binds to `127.0.0.1` only, with a per-launch bearer token.
- DO NOT run external-site content (webview/browser) with `nodeIntegration`; keep `contextIsolation: true` and `sandbox: true`.
- ALWAYS write the Gherkin spec in `specs/` before implementing a slice; implement test-first.
- ALWAYS follow the WUR flow: one Work Unit = one commit, message `WU-P{nn}-{nnn}: ...`.
- ALWAYS cache LLM responses by `sha256(model+prompt+schema)` and record token usage in the quota ledger.
- ALWAYS label scores as "practice score", never as "predicted UPSC marks".
<!-- planfirst:end -->

## New dependencies
Before adding any package: `npm view` / `pip index`, read its LICENSE, add a row to `docs/02-REPO-BOM.md`. Model weights can carry licences separate from code.
