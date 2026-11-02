# UPSC JARVIS

Local-first, free, gamified UPSC study OS: padho → bookmark → focus timer → **recall gate** → spaced repetition → **honest** syllabus progress. Baad mein: PYQ Lab, Mains evaluation, current affairs, interview practice, focus browser.

> **Status (2026-11-02):** Phase 1 (foundation) aur Phase 2 ka Study Loop code ban chuka hai: PDF library + reader, start/end bookmark, focus timer, recall gate, FSRS review, honest coverage, Today dashboard, Obsidian mirror. Sab `ready-for-review` hai, `accepted` nahi. Windows par abhi chalaya nahi gaya aur asli AI keys se test nahi hua. Packaged `.exe` abhi nahi hai (neeche dekho).

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

## Windows laptop par chalane ka tareeka (source se)
Zaroori: Node 22+, pnpm 10 (`corepack enable`), [uv](https://docs.astral.sh/uv/), Python 3.11+ (uv khud la dega), Git.

```powershell
git clone https://github.com/sidhantiitian17/UPSC_JARVIS
cd UPSC_JARVIS
git checkout claude/gallant-volta-orla5n
pnpm install
cd apps/sidecar; uv sync; cd ../..
pnpm dev
```
Pehli baar app khulne par:
1. **Settings** mein *Library folder* aur *Vault folder* (Obsidian vault) chuno.
2. **Settings > AI providers**: Gemini ya OmniRoute ki API key daalo (Windows ke secure storage mein encrypted save hoti hai), ya Ollama chalao. Phir **Test AI** dabao. Model naam `config/routing.yaml` mein placeholder hain, apne hisaab se badlo.
3. **Study** par PDF add karo (picker ya drag-drop), kholo, paragraph ke saamne **Start here** dabao (timer chalu), padho, phir **End here** dabao. Recall gate khud khulta hai.
4. Bina AI key ke bhi gate chalta hai: tab text se *offline fill-in-the-blank* quiz banta hai.

Jo abhi **nahi** hai: packaged installer (sidecar ko `.exe` mein bundle karna baaki), scanned PDF ka OCR, Sociology ontology (official syllabus chahiye), PYQ lab / Mains / Current Affairs / Interview / Browser / Pet (Phase 3+).

## Developer quick start (Phase 1 onwards)
```bash
pnpm install                      # JS deps (Electron binary downloads on first install)
(cd apps/sidecar && uv sync)      # Python sidecar deps
pnpm dev                          # Electron app (sidecar is started by the app in WU-P01-003)
pnpm verify                       # lint + typecheck + tests for everything
```
Rules for agents: `CLAUDE.md`. Roadmap: `agents/roadmap/ALL.md`.

## Licence
Abhi tay nahi. Public karne se pehle dependencies ke licenses (aur model weights ke terms) `docs/02-REPO-BOM.md` mein dobara check karo.
