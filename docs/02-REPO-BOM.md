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
