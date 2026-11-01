# UPSC JARVIS

Local-first, free, gamified UPSC study OS: padho → bookmark → focus timer → **recall gate** → spaced repetition → **honest** syllabus progress. Baad mein: PYQ Lab, Mains evaluation, current affairs, interview practice, focus browser.

> **Status:** planning complete, code abhi shuru nahi hua. Phase 1 se build shuru hoga.

## Kahan se padhein (Hinglish)
| Document | Kya hai |
|---|---|
| [`docs/00-EVALUATION.md`](docs/00-EVALUATION.md) | Blueprint ka evaluation: kya sahi, kya galat, kya badla |
| [`docs/architecture.md`](docs/architecture.md) | Final architecture (simple stack, ADRs, "Don't use now") |
| [`docs/01-FEATURES.md`](docs/01-FEATURES.md) | 166 features, 16 modules, phase + difficulty |
| [`docs/02-REPO-BOM.md`](docs/02-REPO-BOM.md) | Har GitHub repo: verified, license, use/sidecar/reference |
| [`docs/03-FREE-AI-STRATEGY.md`](docs/03-FREE-AI-STRATEGY.md) | Free quota + context bachane ka tareeka |
| [`docs/04-UX-STRATEGY.md`](docs/04-UX-STRATEGY.md) | JTBD, North Star, ethics, screen map |
| [`docs/05-VIBE-CODING-PLAYBOOK.md`](docs/05-VIBE-CODING-PLAYBOOK.md) | Bina coding ke build kaise karein (prompts, Windows notes) |
| [`docs/06-BRAIN-DECISION-MODEL.md`](docs/06-BRAIN-DECISION-MODEL.md) | **laya** ("jev") research, bake-off, fine-tune plan |
| [`docs/07-PYQ-DATASET.md`](docs/07-PYQ-DATASET.md) | Official PYQ → Markdown dataset (Sociology dahil): spec + blocker |
| [`docs/08-REPO-BRAINSTORM.md`](docs/08-REPO-BRAINSTORM.md) | Preparation enhance karne wale repos (verified) |
| [`specs/`](specs/) | Gherkin specs (core loop) |
| [`agents/roadmap/ALL.md`](agents/roadmap/ALL.md) | 10-phase Work Unit Roadmap |
| [`docs/source/`](docs/source/) | Original blueprint (as received) |

## Pehla kadam
1. `docs/00-EVALUATION.md` §9 ke 4 bache hue sawal (RAM/GPU, prelims date, `upsc.gov.in` network, dataset publishing) ka jawab do.
2. `docs/05-VIBE-CODING-PLAYBOOK.md` §1 aur §1b (Windows) ka setup karo.
3. `agents/roadmap/PHASE_1.md` ka pehla WU (`WU-P01-001`) apne coding agent ko do. Saath mein Phase 0 (`PHASE_0.md`): PYQ dataset aur laya bake-off.

## Licence
Abhi tay nahi. Public karne se pehle dependencies ke licenses (aur model weights ke terms) `docs/02-REPO-BOM.md` mein dobara check karo.
