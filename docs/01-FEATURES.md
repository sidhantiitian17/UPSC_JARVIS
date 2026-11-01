# UPSC JARVIS — Feature Catalogue (Hinglish)

> Ye catalogue aapki list + blueprint + naye ideas ko ek jagah laata hai. Har feature ka phase aur difficulty hai, taaki aap decide kar sako kya pehle banana hai.

**Legend**
- **Origin:** `U` = aapne maanga · `B` = original blueprint mein tha · `N` = naya idea (maine add kiya)
- **Phase:** `P1`…`P10` = `agents/roadmap/PHASE_*.md`
- **Difficulty:** 🟢 aasan · 🟡 medium · 🔴 mushkil/risky
- **Kaise:** kaun si library/approach. Repo ka status `docs/02-REPO-BOM.md` mein hai.

**North Star:** *Verified Retained Minutes*: wo focused minutes jinke baad aapne recall test (≥70%) pass kiya. Time-on-app nahi, **yaad kitna raha**, ye asli metric hai (`docs/04-UX-STRATEGY.md`).

---

## M1 · Jarvis Brain (decision system)

> "Brain" koi ek model nahi hai. Ye rules + syllabus tree + retrieval + FSRS + LLM router + student profile ka combination hai.

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M1.1 | **Brain Context Pack**: ~2k tokens ka auto-generated student profile (weak nodes, mistake types, aaj ka plan, exam date) jo har LLM call mein jaata hai. Isse baar-baar context dene ki zaroorat nahi. | SQLite queries → template | U | P2 | 🟢 |
| M1.2 | **LLMClient**: ek hi interface, backend OmniRoute/Ollama/Gemini, caching, quota ledger, fallback | FastAPI module | U | P1 | 🟡 |
| M1.3 | **Tiered routing**: pehle code (no LLM), phir local model, phir free cloud, phir vision/heavy | rules table | U | P1 | 🟡 |
| M1.4 | **Direction Drift Alert**: "Aap low-yield topic mein time laga rahe ho, high-yield chhoot raha hai" | PYQ weightage × time spent | B | P4 | 🟡 |
| M1.5 | **Reverse-tracking**: current affairs padha → check karo uska static base cover hua ya nahi | graph links (CA → node) | B | P6 | 🟡 |
| M1.6 | **Source-grounded answers**: har AI jawab ke saath page/paragraph citation | RAG over chunks | U | P2 | 🟡 |
| M1.7 | **Ask-Jarvis chat**: library + syllabus se grounded Q&A | LLMClient + retrieval | U | P2 | 🟡 |
| M1.8 | **Weekly Brain Review**: "Is hafte kya sahi gaya, kya nahi, agle hafte ka plan" | LLM + stats | N | P3 | 🟡 |
| M1.9 | **Web Assist** (human-in-loop): prompt clipboard par, aap Gemini/ChatGPT/Claude web par Send dabao, **Capture** se jawab app mein | webview + DOM read | U | P8 | 🟡 |
| M1.10 | **LLM eval harness**: golden test-sets se prompts ki quality measure | pytest + fixtures | N | P1 | 🟡 |

## M2 · Syllabus Ontology & Coverage

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M2.1 | **Syllabus tree** (Prelims GS + Mains GS1–4 + Essay) micro-theme tak, YAML mein, aap edit kar sakte ho | LLM-draft + human review | U | P2 | 🟡 |
| M2.2 | **Coverage progress bars** (paper → subject → topic → micro-theme) | (read range × recall score) | U | P2 | 🟢 |
| M2.3 | **Coverage heatmap** (green/amber/red/grey) | React chart | U | P2 | 🟢 |
| M2.4 | **Honest coverage**: "padha" ≠ "yaad hai". Progress sirf recall pass hone par badhe | formula | N | P2 | 🟢 |
| M2.5 | **Completion forecast**: abhi ki speed par syllabus kab khatam hoga vs exam date | linear + variance | N | P3 | 🟢 |
| M2.6 | **Optional subject module**: apna syllabus tree load | YAML import | U | P10 | 🟡 |
| M2.7 | **Source Budget / Hoarding alert**: ek topic par 3 se zyada sources add karoge to warning ("top rankers kam sources, zyada revision") | rule | N | P2 | 🟢 |
| M2.8 | **Static ↔ current-affairs links** har node par | link table | U | P6 | 🟡 |
| M2.9 | **Revision cycles R1–R4** per node | FSRS + planner | N | P3 | 🟡 |

## M3 · Study Session Engine

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M3.1 | **Pomodoro 50/10** (configurable), distraction-free mode | state machine | U | P2 | 🟢 |
| M3.2 | **Recall Gate**: timer khatam → reader lock → adaptive 10–30 MCQ | LLM + validation | U | P2 | 🟡 |
| M3.3 | **Question sources**: 70% abhi padhe hisse se, 20% purane due cards (interleaving), 10% application-type | generator | N | P2 | 🟡 |
| M3.4 | **Restudy advice** exact page + paragraph ke saath | source_chunk_id | U | P2 | 🟢 |
| M3.5 | **Green/Amber/Red confidence tag** har answer par | UI | B | P2 | 🟢 |
| M3.6 | **Emergency skip** (cost: kal ke gate mein double questions) | rule | N | P2 | 🟢 |
| M3.7 | **Idle detection**: system idle > N min to session pause | Electron powerMonitor | U | P2 | 🟢 |
| M3.8 | **Two-minute start ritual**: bahut thaka ho to sirf 2 min "shuru to karo" | UX | N | P3 | 🟢 |
| M3.9 | **Shutdown ritual**: raat ko 5 Q recall + kal ka plan | UX | N | P3 | 🟢 |
| M3.10 | **Bad-day mode**: minimum viable din (1 pomodoro + 10 cards), streak bachti hai | rule | N | P3 | 🟢 |
| M3.11 | **Eye/stretch breaks** (20-20-20), hydration | OpenPets plugin | N | P3 | 🟢 |
| M3.12 | **Subject-wise / hour-wise daily plan**, free time aap set karo | planner v1 | U | P3 | 🟡 |
| M3.13 | **Focus Guard** (opt-in): active window category check (study vs distraction), data local | `active-win` | U | P3 | 🟡 |

## M4 · PDF Reader & Tracking

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M4.1 | **Library**: PDF add (drag-drop/folder), hash dedupe | pypdfium2 | U | P2 | 🟢 |
| M4.2 | **Reader**: pdf.js, text layer, last-position restore, dark mode | pdf.js | U | P2 | 🟡 |
| M4.3 | **Start/End bookmark** → exact range (page + character offset) store | DB | U | P2 | 🟡 |
| M4.4 | **Study log** (date, subject, node, time, book, pages) | DB | U | P2 | 🟢 |
| M4.5 | **Auto-tag range → syllabus nodes** | LLM (cached) | U | P2 | 🟡 |
| M4.6 | **Highlights + margin notes** (→ Obsidian) | pdf.js | N | P2 | 🟡 |
| M4.7 | **Page-level time heat** (kis page par kitna time) | events | N | P3 | 🟢 |
| M4.8 | **"Sahi cheez padh raha hun?" check**: range ka PYQ-relevance score | PYQ links | U | P4 | 🟡 |
| M4.9 | **Scanned PDF OCR** | Surya (optional) | N | P7 | 🔴 |
| M4.10 | **Auto-flashcards** covered range se | LLM + validation | U | P2 | 🟡 |

## M5 · Retention Engine (spaced repetition)

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M5.1 | **FSRS scheduler** | py-fsrs | U | P2 | 🟢 |
| M5.2 | **Due queue** (daily limit, interleaved subjects) | SQL | U | P2 | 🟢 |
| M5.3 | **Wrong answer → card** automatically | rule | N | P2 | 🟢 |
| M5.4 | **Forgetting-risk dashboard** (kaun se nodes bhool rahe ho) | FSRS retrievability | U | P3 | 🟢 |
| M5.5 | **Obsidian mirror** (cards `.md` format) | file writer | U | P2 | 🟡 |
| M5.6 | **Weekly consolidation test** (30 mixed Qs) | generator | N | P3 | 🟡 |

## M6 · PYQ Lab (Prelims)

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M6.1 | **PYQ corpus** (official UPSC PDFs → parse → **human verify**) | parser + review UI | U | P4 | 🔴 |
| M6.2 | **Tag har PYQ → syllabus node** | LLM + review | U | P4 | 🟡 |
| M6.3 | **Trend analysis**: topic × year weightage | SQL + chart | U | P4 | 🟢 |
| M6.4 | **Source mapping**: PYQ ↔ aapki books ke paragraphs | embeddings | U | P4 | 🔴 |
| M6.5 | **Split-view compare** (2–3 books side by side), relevant paragraph highlight + PYQ tag | pdf.js ×N | U | P4 | 🔴 |
| M6.6 | **Trap Lab**: flags (extreme words, word-substitution, contradiction pair) + **aapka hit-rate** | regex + stats | B | P4 | 🟡 |
| M6.7 | **Mistake Autopsy**: Conceptual / Revision / Silly / Over-elimination | form | B | P4 | 🟢 |
| M6.8 | **9-minute drill** (2 solve + 5 analysis + 2 notes) | UI | B | P4 | 🟢 |
| M6.9 | **Distractor Notes** (galat options bhi study material) | LLM | B | P4 | 🟡 |
| M6.10 | **Bouncer questions** (obscure facts, skip-instinct training) | tagged set | B | P4 | 🟡 |
| M6.11 | **3-iteration PYQ** (baseline → source mapping → trap psychology) | workflow | B | P4 | 🟢 |
| M6.12 | **Calibration chart** (confidence vs accuracy) | stats | N | P4 | 🟢 |
| M6.13 | **Attempt-strategy simulator** ("80 vs 90 attempt karun to expected score?") | simulation | N | P10 | 🟡 |
| M6.14 | **Statement-type trainer** ("How many of the above…") | generator | N | P4 | 🟡 |
| M6.15 | **Next-year predictor** (distractor themes + trend se *candidate* topics; "prediction" nahi, **hypothesis**) | stats + LLM | U | P4 | 🟡 |

## M7 · Mains Studio

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M7.1 | **Mains PYQ bank** (paper/year/topic) | corpus | U | P5 | 🟡 |
| M7.2 | **Question generator** (studied topic + linked current affairs) | LLM | U | P5 | 🟡 |
| M7.3 | **Timed tests**: topic-wise aur full GS paper | timer | U | P5 | 🟡 |
| M7.4 | **Photo upload evaluation**: copy ki photo → transcription → rubric report | Gemini vision | U | P5 | 🔴 |
| M7.5 | **Rubric Modifier**: rubric YAML aap badal sako (weights, penalties) | YAML + UI | U | P5 | 🟡 |
| M7.6 | **Directive coach**: Discuss / Critically examine / Comment / Analyse… ka meaning aur structure | static content | U | P5 | 🟢 |
| M7.7 | **No-mercy remarks**: intro, body, conclusion, language, facts, diagram, word limit | rubric | U | P5 | 🟡 |
| M7.8 | **Handwriting Remediation sheet** (illegible words ki practice) | OCR confidence | U | P5 | 🔴 |
| M7.9 | **Topper-diff**: aap apni uploaded topper copy se compare kar sakte ho (copyright: sirf personal) | split view | B | P5 | 🟡 |
| M7.10 | **Value-addition bank**: quotes, SC judgments, committees, data (verified) | curated + `verified` flag | U | P3 | 🟡 |
| M7.11 | **Daily 1-answer habit** (7–11 min timer) | planner | N | P5 | 🟢 |
| M7.12 | **Intro/Conclusion drills** (2 lines) | LLM | N | P5 | 🟢 |
| M7.13 | **Diagram trainer** (flowchart/hub-spoke templates) | static | N | P5 | 🟡 |
| M7.14 | **Score range** (point nahi), 2-pass median | evaluator | N | P5 | 🟡 |
| M7.15 | **Essay module**: outline builder, brainstorm map, evaluator | LLM | U | P10 | 🟡 |
| M7.16 | **GS4 Ethics**: case-study framework (stakeholders → dilemma → options → decision) | rubric | N | P10 | 🟡 |

## M8 · Current Affairs Engine

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M8.1 | **Sources (RSS/public)**: PIB, PRS, The Hindu/Indian Express (public RSS), RBI, ISRO, DST, MoEFCC, MEA, Down To Earth, AIR/Sansad TV, Yojana/Kurukshetra, Economic Survey/Budget, NITI Aayog, Law Commission, ARC, Supreme Court judgments | RSS + extractor | U | P6 | 🟡 |
| M8.2 | **Daily digest**: dedupe → UPSC-relevance score → 3-line summary → node tag | LLM (cached) | U | P6 | 🟡 |
| M8.3 | **35-min newspaper mode**: time-boxed, sirf relevant | UI | B | P6 | 🟢 |
| M8.4 | **CA → static link** + "pehle ye static padho" | graph | U | P6 | 🟡 |
| M8.5 | **CA quiz** (daily 10 Q) | generator | N | P6 | 🟢 |
| M8.6 | **Monthly compilation** (Obsidian) | file writer | N | P6 | 🟢 |
| M8.7 | **Scheme/Index/Report tracker** (index, rank, reporting body, year) | table | N | P6 | 🟡 |
| M8.8 | **Bill/Act tracker** (PRS) | RSS | N | P6 | 🟢 |
| M8.9 | **Map pins** (places in news → map) | static map | N | P6 | 🟡 |
| M8.10 | **UPSC notifications tracker** (official site) | RSS/poll | N | P10 | 🟢 |

## M9 · Interview Room

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M9.1 | **DAF profile** (state, district, graduation, hobbies, service/cadre prefs) | form | B | P9 | 🟢 |
| M9.2 | **DAF analyzer**: har line se probable questions | LLM | N | P9 | 🟡 |
| M9.3 | **Silent mode**: question sirf text, AI bolta nahi | UI | U | P9 | 🟢 |
| M9.4 | **Vision**: eye contact, posture, hand fidget, head pose | MediaPipe Tasks JS | U | P9 | 🔴 |
| M9.5 | **Audio**: transcript, wpm, pauses, filler words, pitch variation | faster-whisper + parselmouth | U | P9 | 🔴 |
| M9.6 | **Content eval**: facts, balance, ethics, structure | LLM | U | P9 | 🟡 |
| M9.7 | **Practice score + coaching report** (frame-wise timeline) | report | U | P9 | 🟡 |
| M9.8 | **Home-state pack**: district facts, schemes, issues | LLM + verify | B | P9 | 🟡 |
| M9.9 | **Opinion bank** (balanced pros/cons on hot topics) | CA + LLM | N | P9 | 🟡 |
| M9.10 | **Panel personalities** (stern / friendly / rapid-fire): sirf question *style* | prompt | N | P9 | 🟢 |
| M9.11 | **Camera/lighting/dress checklist** | static | N | P9 | 🟢 |

## M10 · Library & Ingestion

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M10.1 | **Folder chooser**: library + vault path onboarding mein | Electron dialog | U | P1 | 🟢 |
| M10.2 | **Official sources downloader** (NCERT, Economic Survey, Budget, ARC, PIB…) | scripts | B | P7 | 🟡 |
| M10.3 | **Telegram link** (api_id/hash + OTP, local session, encrypted) | Telethon | U | P7 | 🔴 |
| M10.4 | **Channel picker + filetype filter + incremental sync** | Telethon | U | P7 | 🟡 |
| M10.5 | **FloodWait-safe** (random delays, concurrency cap) | rate limiter | B | P7 | 🟡 |
| M10.6 | **Auto-ingest** (text, chunks, index, tag) | worker | U | P7 | 🟡 |
| M10.7 | **Dedupe** (sha256) | DB | N | P2 | 🟢 |
| M10.8 | **Obsidian vault**: daily notes, session notes, MOCs, cards, backlinks | file writer | U | P2→P7 | 🟡 |

## M11 · Focus Browser

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M11.1 | **Embedded browser** (WebContentsView, alag session) | Electron | U | P8 | 🟡 |
| M11.2 | **YouTube Shorts ban** (URL block + CSS hide) | webRequest | U | P8 | 🟢 |
| M11.3 | **Ad-block** (Ghostery) | library | U | P8 | 🟡 |
| M11.4 | **Allowlist** channels/playlists + relevance gate (title/description classify) | LLM | U | P8 | 🟡 |
| M11.5 | **Recommendations/feed hide** | CSS inject | U | P8 | 🟢 |
| M11.6 | **AI side panel**: lecture par sawal, timestamped notes → Obsidian | transcript + LLM | U | P8 | 🔴 |
| M11.7 | **Lecture ↔ syllabus node** link, watched time log | DB | N | P8 | 🟡 |
| M11.8 | **Break-glass**: 5 min "free browsing" with cost | rule | N | P8 | 🟢 |

## M12 · Gamification & Companion

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M12.1 | **XP/Levels** (verified minutes se, na ki sirf time se) | event log | U | P3 | 🟢 |
| M12.2 | **Streak + freeze + comeback quest** (no shame) | rule | N | P3 | 🟢 |
| M12.3 | **Quests/Badges** (weekly) | rule | U | P3 | 🟢 |
| M12.4 | **Syllabus journey map** ("kitna aaye, kitna baaki") | UI | U | P2 | 🟡 |
| M12.5 | **Pet** (OpenPets): idle par tokna, gate pass par celebrate | CLI/MCP | U | P3 | 🟡 |
| M12.6 | **Pet modes**: Coach / Strict / Silent | settings | N | P3 | 🟢 |
| M12.7 | **Motivation popups**: quote/jargon/fact + **author/citation** + "Mains mein kaise use karein" (sirf `verified`) | curated DB | U | P3 | 🟡 |
| M12.8 | **Level-gated rewards** (pet skins) | assets (license check) | N | P3 | 🟢 |

## M13 · Habit Breaker

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M13.1 | **Start-delay tracking** (planned vs actual) | events | N | P3 | 🟢 |
| M13.2 | **Session quality score** (focused/elapsed, pauses) | events | N | P3 | 🟢 |
| M13.3 | **Doomscroll detector** (distraction app time, opt-in, local) | active-win | N | P3 | 🟡 |
| M13.4 | **Commitment contract** ("plan miss to kal catch-up gate") | rule | N | P3 | 🟢 |
| M13.5 | **Weekly honesty report** (claimed vs verified hours) | stats | N | P3 | 🟢 |
| M13.6 | **Sleep guard** (late-night session par warning) | clock | N | P3 | 🟢 |
| M13.7 | **Burnout guard** (lagatar bahut lambe din → forced rest day suggestion) | rule | N | P3 | 🟢 |
| M13.8 | **Phone nudges** (Telegram bot): plan, quick MCQs | bot | N | P10 | 🟡 |

## M14 · Planner

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M14.1 | **Backward planner** (exam date se) | algorithm | N | P10 | 🟡 |
| M14.2 | **Daily hour-wise plan** | planner | U | P3 | 🟡 |
| M14.3 | **Missed-day rebalance** | algorithm | N | P10 | 🟡 |
| M14.4 | **Mock/test calendar** | calendar | N | P10 | 🟢 |
| M14.5 | **Last-60-days mode** (revision + tests only) | mode | N | P10 | 🟢 |

## M15 · Tests & Analytics

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M15.1 | **Prelims full mock** (negative marking configurable, default −1/3) | engine | U | P10 | 🟡 |
| M15.2 | **CSAT module** (comprehension / numeracy / reasoning, time drills) | generator | N | P10 | 🟡 |
| M15.3 | **Truth Dashboard** (Verified Retained Minutes, calibration, risk) | charts | N | P3 | 🟡 |
| M15.4 | **Sectional tests**, per-topic accuracy, time per Q | stats | U | P4 | 🟢 |
| M15.5 | **Import external mock results** (CSV) | importer | N | P10 | 🟢 |

## M16 · Platform

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M16.1 | **Backup/export/restore** (one zip) | script | N | P10 | 🟢 |
| M16.2 | **Secure secrets** (API keys, Telegram session) | `safeStorage` | N | P1 | 🟢 |
| M16.3 | **Privacy panel** ("kya store ho raha hai") | UI | N | P3 | 🟢 |
| M16.4 | **Hindi/English UI** | i18n | N | P10 | 🟡 |
| M16.5 | **Quota ledger** (kis provider se kitna use hua) | DB | U | P1 | 🟢 |
| M16.6 | **Offline mode** (local model only) | routing | U | P1 | 🟡 |
| M16.7 | **Updater / version pinning of sidecars** | script | N | P10 | 🟡 |
| M16.8 | **Report bad question / wrong fact** | UI | N | P2 | 🟢 |

---

## Jo main jaan-boojh kar *nahi* bana raha (aur kyun)

| Feature | Kyun nahi |
|---|---|
| Paywalled newspaper scraping | ToS/legal risk. RSS use hoga. |
| Telegram protected-content bypass | ToS/copyright. |
| "Predicted UPSC marks" | Koi tool ye reliably nahi bata sakta. "Practice score" hi dikhayenge. |
| Public leaderboard | Comparison anxiety. Optional baad mein. |
| Phone ko lock karna | Desktop app se possible nahi. Telegram-bot nudges alternative. |
| Auto "AI detects cheating" | Self-study app hai, honesty aapki. |

---

## Addendum (2026-11-01): owner inputs + repo brainstorm

> Naye IDs existing modules mein jode gaye hain (module number same). Detail: `docs/06`, `07`, `08`.

| ID | Feature | Kaise | Origin | Phase | Diff |
|---|---|---|---|---|---|
| M1.11 | **Decision Heads** (syllabus-node, grounded, relevance, directive, trap flags) via `DecisionClient`, bake-off se adopt | laya / fastembed+LR / SetFit | U | P0 | 🔴 |
| M1.12 | **Prompt regression tests** (CI) | promptfoo ya pytest golden | N | P1 | 🟡 |
| M2.10 | **Sociology optional ontology** (Paper I & II, thinkers + concepts) official syllabus se | ontology YAML + owner review | U | P2 | 🟡 |
| M3.14 | **ActivityWatch-powered "aaj kahan time gaya"** weekly view | ActivityWatch sidecar | N | P3 | 🟡 |
| M4.11 | **Scanned PDF → searchable** automatic | OCRmyPDF + Tesseract | N | P7 | 🟡 |
| M5.7 | **Vault dashboards** (coverage/due/streak) bina UI code | Obsidian Dataview | N | P2 | 🟢 |
| M5.8 | **Mind-map per syllabus node** | markmap | N | P3 | 🟢 |
| M5.9 | **Personal FSRS parameters** | fsrs-optimizer | N | P10 | 🟡 |
| M6.16 | **Official PYQ dataset (Markdown)**: Prelims GS-I + CSAT, Mains GS I–IV + Essay, Sociology I & II, provenance + verification | `tools/pyq` | U | P0 | 🔴 |
| M6.17 | **Official syllabus + answer-key ingest** (sirf official) | `tools/pyq` | N | P0 | 🟡 |
| M7.17 | **Sociology answer templates** (directive + thinkers + Indian sociologists) | rubric + LLM | N | P5 | 🟡 |
| M7.18 | **Diagram trainer** (flowchart/hub-spoke, timed) | excalidraw | N | P5 | 🟡 |
| M12.9 | **Verified quote bank** (public-domain texts mein exact-match + citation) | script + owner review | N | P3 | 🟡 |
| M12.10 | **Wellbeing via OpenPets plugins** (Focus Buddy, Mood Check-in, Water, Anxiety Aid) | openpets | U | P3 | 🟢 |
| M16.9 | **Phone revision pack** (`.apkg` export → Anki mobile) | genanki | N | P10 | 🟢 |
| M16.10 | **Windows-first packaging + CRLF-safe hooks** | `.gitattributes`, NSIS later | N | P1/P10 | 🟡 |

---

## Count
- Kul features: **166** (16 modules; addendum shamil) · P0: 3 · P1–P2: 40 · P3: 34 · baaki P4–P10
- Sabko ek saath mat banao. Phase 2 ka 7-din dogfood complete hone ke baad hi aage badho.
