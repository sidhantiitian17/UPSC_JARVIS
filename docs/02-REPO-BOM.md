# Repo Bill of Materials (BOM) — Verified

> Verification date: 2026-11-01. "Exists" = `git ls-remote` se confirm. "Inspected" = maine clone karke code/README padha. "License" = LICENSE file se.
> **Rule:** repo ko sirf teen label milenge: **LIBRARY** (dependency) · **SIDECAR** (alag app) · **REFERENCE** (sirf padho). **Koi repo fork nahi hoga.**

## A. Jo hum use karenge

| Repo | Label | Role | License | Verified | Phase | Note |
|---|---|---|---|---|---|---|
| `mozilla/pdf.js` | LIBRARY | PDF reader | Apache-2.0 | exists, license | P2 | `pdfjs-dist` npm package |
| `open-spaced-repetition/py-fsrs` | LIBRARY | FSRS scheduler | MIT | exists, license | P2 | |
| `open-spaced-repetition/ts-fsrs` | LIBRARY (optional) | UI-side preview | — | exists | P3 | License maine check nahi kiya |
| `diegosouzapw/OmniRoute` | **SIDECAR** | Free AI gateway `:20128` | MIT | **inspected**, license | P1 | `npm i -g omniroute`. Clone 862 MB, isliye fork nahi. Version pin karo. README ke "380 providers/150+ free" claims maine verify **nahi** kiye. |
| `ollama/ollama` | **SIDECAR** | Local models | — | exists | P1 | License maine check nahi kiya (public MIT jaana-pehchana hai, par verify karo) |
| `OpenPetsHQ/openpets` | **SIDECAR** | 2D pet + plugin SDK + CLI/MCP | MIT | **inspected**, license | P3 | Desktop release download hota hai. 72 MB monorepo, fork nahi. |
| `LonamiWebs/Telethon` | LIBRARY | Telegram client | MIT | exists, license | P7 | Sirf aapka user-session |
| `SYSTRAN/faster-whisper` | LIBRARY | Speech-to-text | MIT | exists, license | P9 | CPU par `small`/`base` model |
| `google-ai-edge/mediapipe` | LIBRARY | Face/Pose/Hand (Tasks, JS) | — | exists | P9 | `@mediapipe/tasks-vision`; license maine check nahi kiya |
| `ghostery/adblocker` | LIBRARY | Browser ad-block | MPL-2.0 | exists, license | P8 | npm package ka exact naam WU mein verify karo |
| `datalab-to/surya` | LIBRARY (optional) | OCR + line boxes (legibility) | Apache-2.0 (code); weights OpenRAIL-M | exists, license | P5/P7 | Weights: personal/research free; **public distribution se pehle terms padho** |
| `datalab-to/marker` | LIBRARY (optional) | Scanned/complex PDF → markdown | Apache-2.0 (code); weights OpenRAIL-M | exists, license | P7 | Default text extraction `pypdfium2` se; marker sirf zaroorat par |
| `BerriAI/litellm` | LIBRARY (Plan B) | Gateway ka fallback | MIT, par kuch `enterprise` directories par alag license (LICENSE file ke hisaab se) | exists, license | — | Agar OmniRoute fail ho |
| `HKUDS/LightRAG` | LIBRARY (deferred) | Graph RAG | MIT | exists, license | **Later** | Trigger: `docs/architecture.md` → Add Later |

## B. Sirf reference (code copy nahi)

| Repo | Kyun reference | License | Verified | Finding |
|---|---|---|---|---|
| `Sachin23991/upsc-os` | UI ideas (dashboard, planner, streaks) | **Koi nahi** | **inspected** | 48 files, Vite + React (JS), **Firebase** auth, last commit 2026-01-16 |
| `thisisAtharv/ExamEdge` | Library/leaderboard UI idea | MIT | **inspected** | MERN + Firebase + n8n; **Shastra/handwriting evaluator nahi mila** |
| `laleetborse/UPSC-Answer-Generator` | Answer-structure prompt idea | **Koi nahi** | **inspected** | 6 files, Streamlit `main.py`, answer *generator* hai, evaluator nahi |
| `amanbh2/UPSC-Star` | Mains question set ka shape | **Koi nahi** | **inspected** | Sirf Mains: GS-I 191, GS-II 185, GS-III 189, last commit 2022, answers nahi |
| `iaseth/prelimspattern` | Idea | **Koi nahi** | exists, license (content maine nahi dekha) | last commit 2022 |
| `iFurySt/open-browser-use` | Phase 8 ka experimental automation | MIT | **inspected** | Browser extension + CLI + SDKs. Electron-IAB package abhi npm par nahi |
| `QuantumNous/new-api` | Gateway alternative | **AGPL-3.0** | exists, license | Embed mat karo |
| `ahrm/sioyek` | Split-view/portal UX idea | GPL-3.0 | exists, license | Native C++, embed nahi |
| `datalab-to/chandra` | Handwriting VLM | Apache-2.0 (code); weights OpenRAIL-M | exists, license | Bhaari; commercial self-host par license chahiye |
| `cliqz-oss/adblocker` | Purana naam | — | exists | Maintained fork: ghostery/adblocker |

## C. Jo verify hue par abhi use nahi karenge

| Repo | Verified | Kyun nahi |
|---|---|---|
| `songquanpeng/one-api` | exists | OmniRoute kaafi hai |
| `HKUDS/VideoRAG` | exists | Phase 8 ke baad dekhenge |
| `abhinavsricharan/local-rag-bot`, `projectvishwagyan-source/LLM-RAG`, `Mankarjasika2506/civil-guru-ai` | exists | Content inspect nahi kiya. Hamara RAG simple hai |
| `Dineshkarthik/telegram_media_downloader`, `randaft20-cloud/Telegram-media-downloader`, `yousofss/telegram-media-downloader` | exist | Telethon se seedha likhna simple hai. Incremental-sync *idea* reference ho sakta hai |
| `Neet-Nestor/Telegram-Media-Downloader` | exists | Browser userscript, restricted-content ke liye. **Policy: use nahi** |
| `Playa-Cyrene/Cyrene-Agent`, `LorisYounger/VPet` | exist | OpenPets kaafi hai |
| `obligator11/InterviewAnalyzer`, `mrgulrez/haven-ml` | exist | Content inspect nahi kiya. Legacy `mp.solutions` hoga; hum Tasks API use karenge |
| `rinavolu/Youtube-Application` | exists | Content inspect nahi kiya |
| `ananyaem/UPSC-LLM`, `nit-in/pib`, `nit-in/download_ncert_books`, `ojhankit/dailynews-automation`, `imsoumya18/upsc_bot` | exist | Content inspect nahi kiya. Phase 6/7 mein reference ke liye dekh sakte hain |
| `ai-learning-tools/obsidian-spaced-repetition-ai`, `open-spaced-repetition/obsidian-spaced-repetition-recall` | exist | Obsidian plugins app se drive nahi hote |
| `crafter-station/webctl` | exists | RSS kaafi hai; Rust CLI premature |
| `V1rtual-Desk-Pet/V1rtual-Desk-Pet` | **MISSING (owner guess galat tha)** | Blueprint mein owner nahi diya tha |

## D. Naye dependencies jo blueprint mein nahi the (WU mein verify honge)

| Dependency | Role | Note |
|---|---|---|
| `pypdfium2` | PDF text extraction (permissive license) | Verify at WU-P02-004 |
| `sqlite-vec` | SQLite mein vector search | Verify at WU-P01-004 |
| `trafilatura` ya equivalent | Article text extraction (RSS ke baad) | Verify at P6 |
| `electron-vite`, `shadcn/ui`, `Tailwind` | UI toolchain | Verify at WU-P01-002 |
| `parselmouth` / `librosa` | Audio prosody | Verify at P9 |
| `active-win` | Active window title (Focus Guard) | Verify at P3 |

> **Note:** "Verify" ka matlab: us WU ke andar agent ko pehle `npm view`/`pip index` + LICENSE check karna hai. Bina check ke dependency add nahi hogi.

## E. Owner inputs ke baad jode gaye (2026-11-01; detail `docs/08-REPO-BRAINSTORM.md`)

| Repo | Label | Role | License (GitHub API) | Verified | Phase | Note |
|---|---|---|---|---|---|---|
| `NandhaKishorM/laya` | LIBRARY (evaluate) | Decision Brain heads | Apache-2.0 (code) **and weights** (HF model-card metadata, verified 2026-11-01) | **inspected** (README, BENCHMARKS, docs), PyPI 0.4.20, ★34,782; **installed + run on sandbox CPU** (`agents/research/laya-spike.md`) | P0 | Bake-off decides per head (`docs/06`) |
| `OpenPetsHQ/openpets` | SIDECAR | Pet (**confirmed**) | MIT | **inspected** (README, cli/mcp/ipc/plugins docs) | P3 | Windows signed installer; `@open-pets/client` named-pipe IPC |
| `ActivityWatch/activitywatch` | SIDECAR (evaluate) | Focus Guard data | MPL-2.0 | metadata | P3 | Windows behaviour to verify in spike |
| `qdrant/fastembed` | LIBRARY | CPU embeddings, bake-off baseline | Apache-2.0 | metadata | P0/P2 | |
| `huggingface/setfit` | LIBRARY (bake-off) | Few-shot tagging | Apache-2.0 | metadata | P0 | |
| `jsvine/pdfplumber` | LIBRARY | PDF text/layout | MIT | metadata | P0/P2 | |
| `tesseract-ocr/tesseract` (UB-Mannheim Windows build 5.4.0.20240606) | tool (CLI, external) | Scanned PDF page images → text (called via `subprocess`, no Python wrapper) | Apache-2.0 (winget metadata; installer SHA256 verified by winget) | installed + run on owner laptop 2026-11-01 | P0/P7 | OCRmyPDF dropped for now: it also needs Ghostscript (AGPL) which was not approved. Only the `eng` and `osd` traineddata are installed |
| `python-pillow/Pillow` 13.0.0 | LIBRARY | Page image crop/resize/border before OCR, gutter detection | MIT-CMU (HPND-style, from package metadata) | installed + used 2026-11-01; was already a transitive dependency of pdfplumber, now declared in tools/pyq/pyproject.toml | P0 | |
| `ocrmypdf/OCRmyPDF` | LIBRARY (not used) | — | MPL-2.0 | — | — | Not adopted; revisit only if Ghostscript is approved |
| `adbar/trafilatura` | LIBRARY | Article extraction | Apache-2.0 | metadata | P6 | |
| `open-spaced-repetition/fsrs-optimizer` | LIBRARY | Personal FSRS params | BSD-3-Clause | metadata | P10 | |
| `kerrickstaley/genanki` | LIBRARY | Anki `.apkg` export | MIT | metadata | P10 | |
| `markmap/markmap`, `excalidraw/excalidraw` | LIBRARY | Mind-maps, diagram trainer | MIT | metadata | P3/P5 | |
| `blacksmithgu/obsidian-dataview`, `st3v3nmw/obsidian-spaced-repetition` | Obsidian plugins (user-installed) | Vault dashboards / card review | MIT | metadata | P2 | Dataview last push Nov-2025 |
| `realyuvishere/upsc-pyq` | REFERENCE | Official-page scraper structure | MIT | **inspected** (`main.py`, README) | P0 | ~2.9 GB (PDFs committed): do not clone |
| `promptfoo/promptfoo`, `docling-project/docling`, `microsoft/markitdown`, `m-bain/whisperX`, `ggml-org/whisper.cpp`, `librosa/librosa`, `YannickJadoul/Parselmouth` (GPL-3.0), `datameet/maps` (2022), `rhasspy/piper`, `huggingface/transformers.js`, `unslothai/unsloth` | EVALUATE | See brainstorm §2 | various | metadata | later | Parselmouth GPL: avoid while repo is public |

> `pypdfium2`: GitHub licence metadata `None` → read the LICENSE file before use (WU-P00-002).

## F. Build dependencies added in Phase 1 (licences read from the npm registry, 2026-11-01)

| Package | Licence | Role | WU |
|---|---|---|---|
| `electron-vite` template (`@quick-start/create-electron`), `electron`, `vite`, `react` | MIT (template and tools) | Desktop shell scaffold (existing repo reused, not written from scratch) | P01-001 |
| `react-router-dom`, `clsx`, `tailwind-merge`, `tailwindcss`, `@tailwindcss/vite` | MIT | Routing, class utilities, styling | P01-002 |
| `class-variance-authority` | Apache-2.0 | Button variants | P01-002 |
| `lucide-react` | ISC | Icons | P01-002 |
| `@fontsource-variable/inter`, `@fontsource/noto-sans-devanagari`, `@fontsource-variable/source-serif-4` | OFL-1.1 (font licence) | Bundled fonts (offline, CSP-safe) | P01-002 |
| `vitest`, `jsdom`, `@testing-library/{react,jest-dom,user-event}` | MIT | Tests | P01-002 |
| `playwright-core` | Apache-2.0 | `pnpm e2e` Electron launch check | P01-002 |

`@electron-toolkit/preload` was removed: the preload is now a minimal sandbox-safe bridge.

## G. Sidecar and API tooling (licences read from PyPI/npm, 2026-11-01)

| Package | Licence | Role | WU |
|---|---|---|---|
| `fastapi`, `pydantic`, `pyyaml`, `jsonschema`, `hatchling`, `pytest`, `ruff` | MIT | Sidecar framework, validation, build, tests, lint | P01-001/003 |
| `uvicorn`, `httpx` | BSD-3-Clause | ASGI server, HTTP client | P01-001/003 |
| `openapi-typescript` | MIT | Generates `packages/shared/src/api.d.ts` from the sidecar's OpenAPI | P01-003 |
| `sqlite-vec` 0.1.9 | MIT OR Apache-2.0 (PyPI metadata) | Vector search inside SQLite (loaded in `connect()`; KNN verified in tests) | P01-004 |

## H. CI Actions (licences read from each repo's LICENSE, 2026-11-01; pinned by commit SHA in `.github/workflows/ci.yml`)

| Action | Licence | Role | WU |
|---|---|---|---|
| `actions/checkout` v7.0.1, `actions/setup-node` v7.1.0, `actions/setup-python` v7.1.0 | MIT | Checkout, Node, Python toolchains | P01-007 |
| `pnpm/action-setup` v6.1.0, `astral-sh/setup-uv` v10.3.3 | MIT | pnpm (version from `packageManager`), uv | P01-007 |

PyYAML (MIT, already listed in G) is also used by the syllabus ontology loader (P02-001). No new packages.
