# Philosophy

## What this project is
**UPSC JARVIS** is a local-first, zero-cost, gamified desktop study operating system for a single UPSC Civil Services aspirant. It verifies that what is read is retained (recall gate + FSRS spaced repetition), tracks syllabus coverage honestly down to micro-themes, and extends into PYQ analysis, Mains evaluation, current affairs, interview practice and a distraction-free browser. Source of truth for the idea: `docs/00-EVALUATION.md`, `docs/01-FEATURES.md`, `docs/architecture.md`.

## Principles the agent must uphold
1. **Study Loop first.** Nothing ships ahead of the loop (PDF → bookmark range → timer → recall gate → FSRS → honest coverage).
2. **Honest progress.** Coverage rises only when recall passes. "Read" is not "known".
3. **Local-first, free-only.** SQLite, local files, free-tier AI. No billing, no cloud account required.
4. **One door for AI.** Every LLM call goes through `LLMClient` (cache, ledger, fallback ladder).
5. **Grounded or discarded.** Generated questions/facts need a source chunk and verbatim quote; motivational quotes need `verified = 1`.
6. **Coach, not shame.** Gamification must never humiliate; sleep and burnout are protected.
7. **No licence, no copy.** Never copy code from unlicensed repos. Re-implement from spec.
8. **Respect the rules of others.** No bypassing paywalls, captchas, or Telegram protected content; no default-on bot automation of consumer chat UIs.
9. **Small, testable, reversible.** One Work Unit = one commit; spec first (Gherkin), test first.
10. **Practice score, not prophecy.** Never present a score as predicted UPSC marks.

## Explicit non-goals
- Multi-user / cloud / accounts / public leaderboards (until a measured need exists).
- Training an SLM from scratch.
- Locking down the phone.
- Supplying copyrighted study material or channel lists.
- Replacing the aspirant's judgement or a human mentor.

## Default branch
`main` (remote is empty; not yet created). Working branch for this session: `claude/gallant-volta-orla5n`.
