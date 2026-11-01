# Repo Brainstorm — preparation ko enhance karne wale GitHub repos (Hinglish)

> Date: 2026-11-01. ★ / license / last-push **GitHub API se**, maine khud nikaale (search + repo metadata). "Inspected" = maine code/README clone karke ya raw se padha. "Not inspected" = sirf metadata dekha. HuggingFace sandbox se unreachable hai, isliye HF models/datasets verify nahi hue.

## 0. Pehle ek reality check
UPSC-specific GitHub ecosystem **patla hai**. Maine `upsc pyq`, `upsc current affairs`, `upsc mains answer evaluation`, `sociology optional upsc`, `ncert books` jaise queries chalaye. Zyadatar repos **0–10 ★**, **bina license**, aur kuch **LLM-generated ya PDF-mirror** hain (provenance unclear). Isliye **asli leverage generic, battle-tested open-source tools mein hai** (ActivityWatch, FSRS tools, trafilatura, fastembed, SetFit, OCRmyPDF…) jo hum UPSC ke liye jodenge. UPSC-specific repos sirf *reference* hain.

## 1. ADOPT (strong fit, permissive license, active)

| Repo | ★ / license / last push | Kya karega JARVIS mein | Phase | Status |
|---|---|---|---|---|
| `OpenPetsHQ/openpets` | 1,366 · MIT · 2026-10-30 | **Pet (aapka decision).** Windows signed installer; Windows named-pipe IPC; `@open-pets/client` TS client; official plugins: **Focus Buddy, Mood Check-in, Water Reminder, Anxiety Aid Tools, Calendar Airmail** | P3 | **inspected** |
| `ActivityWatch/activitywatch` | 19,459 · MPL-2.0 · 2026-10-26 | **Focus Guard / doomscroll detector bina apna watcher likhe**: local server + window watcher; REST API. `aw-watcher-web` browser ke liye | P3 | metadata only; GitHub description "Cross-platform…", Windows behaviour spike mein verify |
| `adbar/trafilatura` | 7,050 · Apache-2.0 · 2026-10-30 | Current-affairs articles ka main text extraction (RSS ke baad) | P6 | metadata |
| `qdrant/fastembed` | 3,277 · Apache-2.0 · 2026-10-28 | CPU par ONNX embeddings (torch ke bina): retrieval + **bake-off baseline A** | P0/P2 | metadata |
| `asg017/sqlite-vec` | 8,232 · Apache-2.0 · 2026-05-18 | SQLite mein vector search | P1 | metadata |
| `jsvine/pdfplumber` | 10,860 · MIT · 2026-10-15 | PDF text with layout/positions (PYQ parser, book ingest) | P0/P2 | metadata |
| `ocrmypdf/OCRmyPDF` | 35,199 · MPL-2.0 · 2026-10-25 | **Scanned PDF → searchable PDF** (Telegram/old PYQ PDFs aksar scanned) | P0/P7 | metadata |
| `tesseract-ocr/tesseract` | 77,283 · Apache-2.0 · 2026-10-28 | OCRmyPDF ka engine; printed text ke liye | P0/P7 | metadata |
| `open-spaced-repetition/fsrs-optimizer` | 112 · BSD-3 · 2026-08-06 | **Aapke review logs se FSRS parameters personalize** (kuch hazaar reviews ke baad) | P10 | metadata |
| `markmap/markmap` | 13,211 · MIT · 2026-09-12 | Markdown notes → **mind-map** (revision ke liye har syllabus node ka map) | P3/P10 | metadata |
| `excalidraw/excalidraw` | 134,957 · MIT · 2026-10-31 | Mains **diagram/flowchart trainer** (embed as component; npm package WU mein verify) | P5 | metadata |
| `kerrickstaley/genanki` | 2,780 · MIT · 2024-12-30 | **Phone revision**: due/weak cards ko `.apkg` banake Anki mobile mein padho (JARVIS ka custom mobile app nahi chahiye). Export-only, scheduling duplicate na ho | P10 | metadata; last push 2024 (stable lib) |
| `blacksmithgu/obsidian-dataview` | 9,411 · MIT · 2025-11-17 | Vault ke notes ke upar **bina UI code ke dashboards** (coverage, due, streak) | P2 | metadata; last push Nov-2025 (activity slow: check) |
| `st3v3nmw/obsidian-spaced-repetition` | 2,605 · MIT · 2026-11-01 | Obsidian ke andar flashcard review (hamare vault mirror ke saath compatible) | P2 | metadata |

## 2. EVALUATE (spike / bake-off ke baad faisla)

| Repo | ★ / license / last push | Sawal | Phase |
|---|---|---|---|
| `NandhaKishorM/laya` | 34,782 · Apache-2.0 · 2026-11-01 | **Decision Brain.** Zero-shot near chance → fine-tune zaroori. `docs/06-BRAIN-DECISION-MODEL.md` | P0 |
| `huggingface/setfit` | 2,858 · Apache-2.0 · 2026-10-06 | Few-shot tagging: laya ka rival (bake-off B) | P0 |
| `docling-project/docling` | 69,940 · MIT · 2026-10-31 | Layout-aware PDF → Markdown (books). **Heavy** hai (ML models) vs pdfplumber | P2/P7 |
| `microsoft/markitdown` | 193,299 · MIT · 2026-10-28 | docx/pptx/xlsx notes ko markdown mein convert (ingest) | P7 |
| `promptfoo/promptfoo` | 26,685 · MIT · 2026-11-01 | Prompt regression testing (hamare golden harness ka alternative; Node-based) | P1 |
| `m-bain/whisperX` | 24,989 · BSD-2 · 2026-10-22 | **Word-level timestamps** → pauses/filler words (interview). Dependencies heavy | P9 |
| `ggml-org/whisper.cpp` | 54,832 · MIT · 2026-10-30 | Python-free STT; Windows par faster-whisper vs yeh | P9 |
| `librosa/librosa` | 8,745 · ISC · 2026-10-06 | Prosody (pitch, energy) — **permissive** | P9 |
| `YannickJadoul/Parselmouth` | 1,298 · **GPL-3.0** · 2026-10-13 | Praat-quality pitch; **GPL** — repo public hai, isliye librosa pehle | P9 |
| `huggingface/transformers.js` | 16,393 · Apache-2.0 · 2026-10-30 | Renderer/Node mein small models (embeddings), Python ke bina | later |
| `datameet/maps` | 487 · MIT · **2022-05-11** | India spatial data (geography/CA map pins). **Stale + boundary-depiction sensitivity:** official map se verify karo | P6 |
| `rhasspy/piper` / `OHF-Voice/piper1-gpl` | 11,314 (last push 2025-08) / 6,112 · MIT / **GPL-3.0** | "Notes sunna" (TTS, optional). License aur maintenance check | P10 |
| `unslothai/unsloth` | 78,900 · Apache-2.0 · 2026-11-01 | Sirf agar future mein *generative* LoRA chahiye. Abhi **nahi** | — |
| `open-spaced-repetition/fsrs4anki`, `…/srs-benchmark` | 4,121 MIT · 283 (no license) | FSRS docs/reference; benchmark methodology | P2 |
| `kurtmckee/feedparser` | 2,453 · license "NOASSERTION" (GitHub detect nahi kar paya) | RSS parsing; license WU mein confirm | P6 |

## 3. UPSC-SPECIFIC: sirf REFERENCE (code copy nahi)

| Repo | ★ / license | Note |
|---|---|---|
| `realyuvishere/upsc-pyq` | 1 · **MIT** · 2026-09-20 | Official page se PYQ scraper. **Inspected** (`main.py`). Site structure ka reference. Limits: no resume/hash/robots. ~2.9 GB (PDFs committed) — clone mat karo |
| `ananyaem/UPSC-LLM` | 9 · MIT · 2024-06-19 | Current-affairs RAG. Not inspected. Stale |
| `aayushdutt/ncert-downloader` | 10 · **no license** · 2026-07-26 | NCERT scraper idea; hum apna fetcher likhenge (P7) |
| `shyamji02/pib-rag`, `Niharika1614/n8n-upsc-pib-summarizer`, `Ankitbuilder/upsc-current-affairs-pipeline`, `dineshsankhala2192/pib-upsc-current-affairs`, `nandubangari/upsc-current-affairs-app` | ≤1 · no license | PIB/CA pipelines: **source lists ke idea** ke liye. Not inspected |
| `rubinu12/AnswerEvaluator`, `upadhyaysabyasachi/UPSC-MAINS-GRADER`, `lalitmishra8785-cmyk/examinerai-upsc`, `rtsdark/*` | ≤1 · no license | Mains evaluators; **rubric ideas** compare karne ke liye. Not inspected |
| `upscclub/upsc-resources` | 1 · MIT | Curated links. Not inspected |
| `Vikhram-S/IndianConstitution-js` | 2 · Apache-2.0 | Constitution lookup library; **accuracy verify** karo; official text behtar |

## 4. AVOID / EXCLUDE (aur kyun)

| Repo/Source | Kyun |
|---|---|
| `vinaykumargb/UPSC-Mains-PYQs` | Description: **"Generated using Claude AI"** → official nahi; PYQ dataset mein **excluded** |
| `Shabber10/ALL-PYQ-Papers`, `sk417/UPSC-PYQ`, `roshankumarsinghupsc/sociology-upsc-question-papers`, `UPSC-2K25/MainsPYQ` | Third-party mirrors, provenance unverified, license nahi → **official site hi source** |
| `HabitRPG/habitica` (license "NOASSERTION"), `ankitects/anki` ("NOASSERTION") | Mixed/unclear licenses → **embed nahi**; mechanics ke liye reference ya export-only |
| Coaching-site scrapers, Telegram channel lists | Copyright/ToS (policy: `docs/00-EVALUATION.md` row 16) |

## 5. Is brainstorm se **nayi ideas** (features)

| # | Idea | Kaise (repo) | Phase | Value |
|---|---|---|---|---|
| 1 | **Phone par revision** bina custom app: weak/due cards `.apkg` export → Anki mobile | genanki | P10 | Phone distraction ka cheap alternative |
| 2 | **Focus Guard bina apna watcher**: ActivityWatch data se "aaj kahan time gaya" + distraction classifier (H8) | ActivityWatch | P3 | `active-win` code kam |
| 3 | **Vault dashboards zero-UI**: coverage/due/streak notes (Dataview) | obsidian-dataview | P2 | Obsidian "second brain" turant useful |
| 4 | **Mind-map per syllabus node** (revision) | markmap | P3/P10 | Visual revision |
| 5 | **Diagram trainer** (Mains): flowchart draw + timed practice | excalidraw | P5 | Diagram marks |
| 6 | **Verified quote bank** (Gutenberg/Wikisource/Archive.org ke public-domain texts mein exact-string match → author/work/chapter citation automatic). Sociology thinkers ke liye khaas; translations ka copyright check karo | (idea, repo nahi) | P3 | `verified` flag ko human-only se auto-assisted banata hai |
| 7 | **Personal FSRS parameters** (review logs se) | fsrs-optimizer | P10 | Better scheduling |
| 8 | **Scanned book → searchable** auto | OCRmyPDF + Tesseract | P7 | Telegram/old PDFs ka bada hissa scanned hota hai (aam observation, verify) |
| 9 | **Wellbeing**: official OpenPets plugins (Anxiety Aid, Mood Check-in, Water) interview/gate se pehle | openpets | P3 | Burnout guard ke liye ready-made |
| 10 | **Prompt regression tests** CI mein | promptfoo | P1 | Prompt change se quality na bigde |
| 11 | **Sociology-specific**: thinker↔concept graph, "kisne kya kaha" cards, compare-contrast tables, Paper I/II PYQ → answer template (directive + thinkers) | ontology + LLM | P2/P5 | Aapka optional |
| 12 | **Offline decision heads** (tagging/relevance/grounding) bina LLM quota | laya / fastembed+LR | P0→ | Free quota bachta hai |

## 6. Kya maine verify **nahi** kiya
- Windows par ActivityWatch / OCRmyPDF / laya ka real behavior (spike mein).
- `pypdfium2` ka license: GitHub metadata `None` (LICENSE file WU mein padhna).
- Hugging Face par koi bhi model/dataset (sandbox se unreachable): embeddings model cards, laya weights license, `DataOrigin/ncert-lectures-india` jaisa dataset jo web search mein dikha.
- Jin repos ko "Not inspected" likha, unka code quality.
- Stars/dates **2026-11-01** ke snapshot hain.
