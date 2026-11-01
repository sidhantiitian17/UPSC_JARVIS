# AGENTS.md

This repository's rules for every coding agent (Claude Code, Antigravity, OpenCode, Cursor, Codex) live in **`CLAUDE.md`**. Read it first, then `docs/architecture.md` and `agents/roadmap/ALL.md`.

Short version: spec first (`specs/`), one Work Unit per commit (`WU-Pnn-nnn: ...`), all LLM calls via `LLMClient`, SQLite only, no code from unlicensed repos, no bypassing paywalls/captchas/Telegram protections, stop at `ready-for-review`.
