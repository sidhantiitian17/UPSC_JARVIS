# UPSC JARVIS — Blueprint Evaluation Report (Hinglish)

> Date: 2026-11-01 · Evaluated file: `docs/source/UPSC_Jarvis_App_Blueprint.original.md`
> Method: har claim ko code/GitHub se verify kiya. Jahan verify nahi ho paya, wahan "verify nahi" likha hai. Andaaza ko fact nahi banaya.

---

## 1. Seedha verdict (TL;DR)

| Cheez | Score | Matlab |
|---|---|---|
| **Vision / pedagogy** (study loop, trap-decoding, active recall, mistake autopsy) | **9/10** | Idea bahut strong hai. Isse hi top-ranker jaisa discipline banta hai. |
| **Blueprint jaisa likha hai, waisa build karna** (solo vibe coder ke liye) | **4/10** | 30+ repos, 4 languages, Postgres+AGE, Go gateway, Rust CLI. Ye jodna ek poori team ka kaam hai. |
| **Legal / ToS safety** | **4/10** | Unlicensed base repo, consumer chat UI automation, Telegram ke pirated PDFs. |
| **Vibe-coder friendliness** | **3/10** | Har repo ka alag setup aur alag breaking change hota hai. |

(Ye mera judgement hai, koi benchmark nahi.)

**Meri recommendation:** blueprint ko *chhota karo, tarteeb badlo*. Pehle sirf **"Study Loop"** banao: PDF padho → start/end bookmark → 50 min timer → recall gate → spaced repetition → syllabus progress bar. Baaki sab features is loop ke upar ek-ek karke lagte jayenge. Poora plan `agents/roadmap/` mein 10 phases ke roop mein hai.

**Aapki "existing GitHub repo":** `sidhantiitian17/UPSC_JARVIS` khaali hai (0 commits). Isko hi monorepo banaya hai. **Naya repo banane ki zaroorat nahi.** Baaki 40+ repos ko fork nahi karna. Unhe dependency, sidecar ya reference ki tarah use karna hai (section 5).

---

## 1b. Errata aur owner ke jawab (2026-11-01)

| Cheez | Update |
|---|---|
| **Row 5 ("JEV model") sudhaar** | Maine pehle likha tha ki JEV real nahi lagta. Maine search nahi kiya tha, **galat tha**. **Jev = TypeSafe ka hosted decision API**, **Laya (`NandhaKishorM/laya`) uska open-source vikalp.** Blueprint ka full-form "Judgment, Evaluation & Verification" phir bhi unsupported hai. Laya generator nahi, decision engine hai, aur zero-shot kamzor hai, isliye **fine-tune zaroori** → `docs/06-BRAIN-DECISION-MODEL.md`. |
| Pet | **OpenPets confirmed.** Windows installer + `@open-pets/client` IPC; official plugins use honge. |
| OS | **Windows** (RAM/GPU abhi pata nahi). |
| Optional | **Sociology.** |
| Medium | **English.** |
| PYQ | **Official site se dataset → Markdown** → `docs/07-PYQ-DATASET.md`. Tooling ready (`tools/pyq`, 35 tests). **Blocker:** `upsc.gov.in` is cloud IP ka TLS handshake reset karta hai (network policy ab theek hai); laptop par chalana hoga. |
| Repo visibility | GitHub repo **public**; owner ne generated PYQ md commit karne ki permission di (raw PDFs nahi). **Branch:** owner decision — `claude/gallant-volta-orla5n` hi default/working branch hai, `main` nahi banega. |
| Brainstorm | `docs/08-REPO-BRAINSTORM.md` |

## 2. Maine kya verify kiya (evidence)

| Check | Result |
|---|---|
| 46 repo-naam `git ls-remote` se | **45 exist karte hain.** `V1rtual-Desk-Pet` ka owner blueprint mein tha hi nahi, isliye woh unverified hai. |
| 8 repos ka code clone karke dekha (`upsc-os`, `ExamEdge`, `UPSC-Star`, `prelimspattern`, `UPSC-Answer-Generator`, `OmniRoute`, `open-browser-use`, `openpets`) | Section 4 mein findings. Kuch blueprint claims **galat nikle**. |
| 12 key libraries ke LICENSE files | Section 4 aur `docs/02-REPO-BOM.md` mein. |
| Jo main verify **nahi** kar paya | Stars, release dates, "380 providers / 150+ free" jaise README ke apne claims, Qwen3.6-35B-A3B model ka naam, free-tier ke exact numbers. Ye sab time ke saath badalte hain. Build karte waqt dashboard par live dekho. |

Ye clones untrusted data the. Maine koi code run nahi kiya, sirf padha.

---

## 3. Blueprint mein jo bilkul sahi hai (rakhna hai)

1. **Core loop**: padho → recall test → spaced repetition → progress. Yehi asli value hai.
2. **Prelims trap patterns** (extreme words, data-direction, word-substitution, contradiction pairs). Ye useful *hints* hain. Inhe hard rules nahi, *statistics* banana hai (section 4, row 11).
3. **Mistake Autopsy** (Conceptual / Revision / Silly / Over-elimination). Ye best insight hai. Isse mock tests ka analysis automatic ho jata hai.
4. **Bouncer questions** aur **Green/Amber/Red confidence tagging**. Isse calibration aur exam sense banta hai.
5. **Reverse-tracking** (current affairs padha → static base check karo). Pedagogically sahi hai.
6. **Local-first** socha hai (data aapki machine par). Privacy aur zero-cost, dono ke liye sahi.
7. **Modular approach** (existing tools jodna). Direction sahi hai, par execution bahut heavy hai.

---

## 4. Claim-by-claim reality check

| # | Blueprint ka claim | Reality (evidence) | Verdict | Fix |
|---|---|---|---|---|
| 1 | `Sachin23991/upsc-os` ko base banao | 48 files, 1.2 MB, **LICENSE nahi** (legal taur par aap copy/modify nahi kar sakte). **Firebase** par based hai (cloud login), JavaScript hai (TypeScript nahi). Last commit 2026-01-16. | ❌ Base ke liye galat | Sirf UX reference. Apna Vite+React+TS shell, local-first. |
| 2 | `UPSC-Star` PYQ dataset hai | Sirf **Mains** questions: GS-I 191, GS-II 185, GS-III 189 (kul 565). Last commit 2022. **Prelims MCQ nahi, answers nahi, LICENSE nahi.** | ⚠️ Bahut limited | PYQ corpus khud banana hai, official UPSC PDFs se, aur manual verify karna hai (Phase 4). |
| 3 | `laleetborse/UPSC-Answer-Generator` strict rubric se *evaluate* karta hai | 6 files, ek `main.py` (Streamlit), Gemini se answer **generate** karta hai. Evaluator nahi hai. LICENSE nahi. | ❌ Claim galat | Sirf prompt ka reference. Rubric-based evaluator hum khud banayenge. |
| 4 | `ExamEdge` mein "Shastra framework" aur handwritten evaluator hai | MIT license hai. README: Firebase auth, resource library, quiz, leaderboard, n8n automation. `shastra` / `handwritten` ke hits sirf `src/data/resources*.json` (data) mein hain, **evaluator code nahi mila**. | ❌ Claim galat | Leaderboard/library UI se idea le sakte ho. Evaluator nahi hai. |
| 5 | "JEV (Judgment, Evaluation & Verification) model" | Ye kisi real model ya paper ka naam **nahi lagta**. Aapke original message mein "jev based model (laya open sourced)" tha, aur blueprint ne iska full-form khud bana diya. Mujhe iska asli matlab pata nahi. | ⚠️ Unclear term | Humne ise **"Jarvis Brain"** naam diya (section 6). |
| 6 | SLM ko UPSC par train karo | Ek non-coder ke liye scratch se SLM train karna practical nahi. Data aur GPU dono chahiye, aur quality pehle se maujood models se kam rahegi. | ❌ Practical nahi | **RAG + rules + small local model.** LoRA fine-tune sirf tab, jab 3000+ verified examples ho jayein (`docs/architecture.md`). |
| 7 | LightRAG + PostgreSQL (pgvector + Apache AGE) | LightRAG (MIT) asli hai, par uska default storage **file-based** hai (NetworkX + NanoVectorDB), Postgres ki zaroorat nahi. Aur LightRAG har chunk par LLM se entity-extraction chalata hai, yaani **bahut saare LLM calls**. Ye aapke "free quota bachana hai" goal ke khilaf hai. | ⚠️ Overkill + quota-hungry | **SQLite + FTS5 + vectors**, aur **syllabus tree hi knowledge graph**. LightRAG baad mein, sirf measurable trigger par. |
| 8 | `QuantumNous/new-api` ko gateway banao | License **AGPL-3.0** (network copyleft). Go app hai. | ⚠️ Risky | **OmniRoute** (MIT) use karo. Aapne khud "omni route" bola tha. Neeche row 9 dekho. |
| 9 | (Aapka idea) OmniRoute | **Asli aur bahut active** (last commit 2026-11-01), MIT license. OpenAI-compatible endpoint `localhost:20128/v1/chat/completions`, `npm install -g omniroute`, dashboard, auto-fallback. README ke hisaab se 150+ free providers (ye README ka claim hai, maine verify nahi kiya). Par repo **bahut bada** hai (clone 862 MB, 27k files). | ✅ Best fit | **Fork mat karo.** Alag service ki tarah chalao (sidecar) aur apna `LLMClient` ke peeche rakho (ek hi file badalni pade). |
| 10 | `open-browser-use` se Claude/ChatGPT/Gemini ke **consumer web UI** automate karo | Tool asli hai (MIT, browser extension + CLI + SDKs). Par uska Electron-IAB package abhi **npm par published nahi** hai (source-only). Aur consumer chat UI ko bot se chalana **unke ToS ke khilaf ho sakta hai**: account ban ka risk, DOM baar-baar badalta hai, aur Cloudflare/captcha. | ⚠️ Fragile + risky | **Human-in-loop Web Assist**: app prompt ko clipboard mein copy kare, aap Send dabao, phir "Capture answer" dabao. Full-auto sirf experimental, default OFF (`docs/03-FREE-AI-STRATEGY.md`). |
| 11 | Prelims trap rules ("UPSC govt ko kabhi negative nahi dikhata", "possibility wale statements aksar sahi hote hain") | Ye *aksar sahi* heuristics hain, universal rules nahi. Blind elimination ki aadat se student ko nuksan ho sakta hai. | ⚠️ Overgeneralised | Har trap-flag ke saath **aapka apna hit-rate** dikhao (aapke PYQ attempts se). Jo flag kaam na kare, use hata do. |
| 12 | `sioyek` ko PDF reader banao | Sioyek **native C++/Qt app** hai (GPL-3.0). Electron/React ke andar **embed nahi ho sakta**. | ❌ Technically galat | **pdf.js** (Mozilla, Apache-2.0) React ke andar. Split-window, highlight aur bookmark sab possible hain. |
| 13 | `@cliqz/adblocker-electron` | Cliqz repo (`cliqz-oss/adblocker`) maujood hai, par maintained fork **`ghostery/adblocker`** (MPL-2.0) hai. Maine npm package ka naam verify nahi kiya. | ⚠️ Naam badla | Ghostery wala use karo (WU mein exact package verify karna). |
| 14 | MediaPipe `mp.solutions.*` | Ye **legacy API** hai. Google ab MediaPipe **Tasks** API recommend karta hai. Tasks ka JavaScript version Electron renderer mein seedha chal sakta hai. | ⚠️ Purana approach | **@mediapipe/tasks-vision** renderer mein. Isse interview feature ke liye Python ki zaroorat nahi padegi. |
| 15 | `datalab-to/chandra` + `surya` + `marker` handwriting OCR ke liye | Code Apache-2.0 hai. **Model weights ka license alag** (OpenRAIL-M): personal/research free hai, par commercial/public distribution ke liye shartein hain. Chandra ek bhaari VLM hai. Ye hardware par chalna mushkil ho sakta hai. | ⚠️ Heavy + license note | Primary: **Gemini vision** (free tier). Surya sirf optional: legibility ke liye line-level confidence. |
| 16 | Telegram se coaching/standard books ke PDFs crawl karo | Telegram par aise PDFs zyadatar **copyrighted aur pirated** hote hain. Blueprint "restricted groups" wale tool (`Neet-Nestor`) ka bhi zikr karta hai. Wo protected content ko bypass karne ke liye hota hai. | ⚠️ Legal / ban risk | Telethon se **sirf aapke apne account ke chats**, rate-limit ke saath. **Protected/forward-restricted content bypass nahi karenge.** Pehle free official sources (NCERT, PIB, PRS, Economic Survey, ARC reports). |
| 17 | Obsidian spaced-repetition plugin ko app chalaye | Plugins Obsidian ke andar chalte hain, headless nahi. App unhe drive nahi kar sakta. | ⚠️ Architecture mismatch | **FSRS app ke andar** (`py-fsrs`, MIT). Obsidian vault = **plain markdown mirror** (aap chaho to plugin se bhi review kar sakte ho). |
| 18 | 4 pet repos (openpets, Cyrene, V1rtual, VPet) | `OpenPetsHQ/openpets` **MIT hai aur ready-made desktop app + plugin SDK + CLI/MCP control** deta hai (last commit 2026-10-30). Baaki pet repos ki zaroorat nahi. | ✅ Simplify | **Sirf OpenPets**, alag app ki tarah. JARVIS usse CLI/MCP se control kare (Phase 3). |
| 19 | The Hindu ePaper ke "internal CDN" se scrape karo | Paywalled content scrape karna ToS aur legal dono risk hai. Site badalte hi scraper tootta hai. | ❌ Mat karo | **RSS + page-level extraction** (PIB, PRS, RBI, ISRO, DST, MoEFCC, Down To Earth, newspapers ke public RSS). |
| 20 | 50 min ke baad **mandatory 30 MCQ** | Idea sahi hai, par har baar fixed 30 questions: quota bhi khaata hai aur thakaa bhi deta hai. LLM-generated MCQ **galat bhi ho sakte hain**. | ⚠️ Needs guardrails | **Adaptive N (10–30)**, har question ke saath `source quote + page`, validation pass, "Report bad question" button, emergency skip (cost ke saath). |
| 21 | Interview ka "predicted score", body-language ke saath | Posture/gaze/tone ke metrics heuristic hain, validated nahi. Asli board mein content ka weight sabse zyada hota hai. | ⚠️ Over-claim | Output ko **"practice score" + coaching metrics** kaho, "UPSC predicted marks" nahi. |
| 22 | Pathway streaming (UPSC-LLM) | Ek hobby repo ke liye streaming framework: overkill. (Maine ye repo sirf `ls-remote` se verify kiya, andar ka code nahi dekha.) | ⚠️ Overkill | Daily cron job + RSS kaafi hai. |

---

## 5. "Repo-stitching" ko kaise sahi karein

Blueprint ka asli risk ye hai: har repo ek alag ecosystem hai, to **40 dependencies = 40 jagah toot sakti hain**. Fix: har repo ko ek hi label do:

| Label | Matlab | Examples |
|---|---|---|
| **LIBRARY** | `npm`/`pip` dependency. Version pin karo. | pdf.js, py-fsrs, Telethon, faster-whisper, MediaPipe Tasks, Ghostery adblocker |
| **SIDECAR** | Alag app ki tarah chalao, sirf HTTP/CLI se baat karo. Code mat chhuo. | OmniRoute, Ollama, OpenPets |
| **REFERENCE** | Padho, idea lo, code copy mat karo. | upsc-os, ExamEdge, UPSC-Answer-Generator, UPSC-Star |

Poori table `docs/02-REPO-BOM.md` mein hai.

---

## 6. Do shabd jo mujhe clear nahi the

- **"JEV model"**: iska koi real project nahi mila. Maine ise **"Jarvis Brain"** maana. Ye ek model nahi, ek *system* hai: rules + syllabus tree + retrieval + FSRS + LLM router + aapka student-profile. Agar aapka matlab kuch aur tha (koi specific model/repo), to bata dena, main adjust kar dunga.
- **"OKF"**: iska pakka matlab mujhe nahi pata. Maine ise **knowledge graph / ontology** (syllabus tree + links) maana.

---

## 7. Top risks (bade se chhote)

1. **Question quality**: LLM galat MCQ bana sakta hai aur student galat cheez yaad kar lega. → har question source-quote ke saath, verify pass, report button.
2. **Free quota ka churn**: providers free tier badalte/band karte rehte hain. → ek gateway, caching, local fallback, quota ledger.
3. **ToS / ban**: consumer chat UI automation, Telegram userbot. → human-in-loop, rate limits, naye/kam-kimti accounts par hi experiments.
4. **Over-scope**: sabse bada risk ye hai ki builder (aap) thak ke chhod do. → Phase 2 tak sirf core loop. Har WU chhota aur testable.
5. **Mains evaluation ki reliability**: LLM judge lenient aur inconsistent hota hai. → rubric-anchored, 2-pass median, score range dikhao, exemplar answers.
6. **Gamification ka nuksan**: "koi dekh raha hai" wali feeling anxiety bana sakti hai. Sleep aur burnout ka dhyaan zaroori hai. → Coach/Strict/Silent modes, sleep guard, streak freeze (`docs/04-UX-STRATEGY.md`).
7. **Copyright**: coaching PDFs/notes. → personal local use, bypass nahi, official sources pehle.
8. **Hardware**: local LLM + Whisper + webcam CV ek saath heavy hain. → features alag-alag chalte hain, ek time par ek heavy job.

---

## 8. Maine kya improve/add kiya

| Improvement | Kahan |
|---|---|
| Simplified stack: Electron + React + TS, ek Python sidecar, SQLite. Postgres/AGE/Go/Rust hata diye. | `docs/architecture.md` |
| **Syllabus tree = knowledge graph**; derived artifacts (notes, MCQs, tags) ek baar bana ke store → "context baar-baar dene ki zaroorat nahi" | `docs/architecture.md`, `docs/03-FREE-AI-STRATEGY.md` |
| 5-tier free-AI strategy + quota ledger + **Brain Context Pack** (~2k tokens ka persistent student profile) | `docs/03-FREE-AI-STRATEGY.md` |
| **FSRS** (SM-2 se behtar spaced repetition) | `docs/architecture.md` |
| 166 features, 16 modules, priorities aur kaise banega | `docs/01-FEATURES.md` |
| North-Star metric **"Verified Retained Minutes"**, UX strategy, ethics check | `docs/04-UX-STRATEGY.md` |
| Spec-first Gherkin scenarios (core loop) | `specs/*.feature` |
| Vibe-coding playbook (copy-paste prompts) | `docs/05-VIBE-CODING-PLAYBOOK.md` |
| 10-phase Work Unit Roadmap | `agents/roadmap/` |

---

## 9. Assumptions aur open questions

**Maine ye maana (galat ho to bolo):**
- **Hardware (owner ne bataya, 2026-11-01):** 16 GB RAM; GPU: **discrete AMD Radeon RX 5500M (4 GB VRAM, RDNA1)** plus the Ryzen 5 5600H's integrated AMD Radeon Graphics; Windows. 4 GB VRAM mein ~3B (q4) model comfortably fit hota hai; 7–8B (q4, ~4.5–5 GB) poora VRAM mein nahi aayega (partial offload ya CPU). Ollama ke docs (https://docs.ollama.com/gpu) ke hisaab se Windows par AMD ke liye ROCm ya Vulkan hai; RX 5500 XT unki ROCm table mein hai aur RX 5500M shayad wahi gfx1012 hai, par **ye confirm nahi** (docs mein 5500M ka naam nahi mila), to Vulkan sabse sambhavit raasta hai. Do GPU hone se Ollama integrated GPU chun sakta hai: tab discrete wala `GGML_VK_VISIBLE_DEVICES` se chuno (docs ke hisaab se). **Maine kuch chalakar verify nahi kiya.** PyTorch CUDA AMD par nahi hota, to laya default CPU par; ONNX Runtime DirectML sirf experiment. **Policy: CPU-first default; GPU acceleration ek optional experiment hai jo Ollama server log se verify hoga, kabhi requirement nahi.** Detail `docs/06` §6.
- Sirf aap use karoge (single user). Cloud sync/login nahi.
- Budget ₹0. Koi paid API/billing enable nahi hogi.
- Aapke Gemini Pro subscription se API quota milta hai ya nahi, mujhe pakka nahi pata. Meri jaankari mein subscription aur API key alag cheezein hain. Aap apne Google AI Studio account par check kar lena.

**Ab bache hue sawal (jawab nahi diya to defaults se aage badhenge):**
1. Prelims ka **target attempt kab** hai? (Backward planner ke liye.)
2. **PYQ download:** kya aap apne Windows laptop par `uv run pyq run` chalane ko tayyar ho? (commands: `datasets/pyq/README.md`; cloud se `upsc.gov.in` nahi khulta.)
3. **Laya spike:** laptop par `uv run python -m brain.laya_spike --model english --out laya-spike-report-laptop.json` chalakar JSON bhej sakte ho? (agents/research/laya-spike.md mein steps.)
4. **SweetClaude:** laptop par Claude Code mein `/plugin marketplace add carson-sweet/sweetclaude@main`, `/plugin install sweetclaude@sweetclaude-stable`, restart, phir `/sweetclaude:init`. Ye aap hi kar sakte ho (user-side commands).

(Pehle ke sawal "OS", "optional subject", "medium" ab answered hain, upar §1b.)

---

## 10. Process note (skills ka use)

- **planfirst**: `docs/architecture.md` (greenfield flow).
- **wur (Work Unit Roadmap)**: `agents/` workspace + git hooks (har commit ek Work Unit).
- **n360-engineering:large-feature**: Design → tasks → review gates ka structure (`agents/roadmap/PHASE_*.md`).
- **design-skills:ux-strategy**: `docs/04-UX-STRATEGY.md`.
- **novibe**: spec-first Gherkin (`specs/`). Iska interactive interview (ek-ek scenario par aapse puchna) maine skip kiya, kyunki aapne kam manual interaction maanga tha. Phase 2 shuru hone par ye spec aapke saath finalize hoga.
- **sweetclaude** (2026-11-01, teen baar check kiya). Nishkarsh: (a) cloud container mein plugin sirf `synced/` folder se load hua hai, `~/.claude/plugins/installed_plugins.json` nahi hai, isliye `preflight.sh` `SC_PLUGIN_OK=false` deta hai aur `init`/`doctor` ruk jaate hain; (b) loaded plugin **4.5.2** hai jabki official repo `main` par **5.1.2** hai (maine repo clone karke dekha: structure alag hai, par registry requirement wahi); (c) official install sirf user-side slash commands se hota hai (`/plugin marketplace add carson-sweet/sweetclaude@main`, `/plugin install sweetclaude@sweetclaude-stable`, restart); (d) Claude Code docs ke hisaab se repo ki `.claude/settings.json` marketplace register karti hai par plugin install nahi karti, aur cloud sessions mein ye keys load nahi hoti (subagent ke summary par based, partly verified), isliye wo file maine commit nahi ki. **Maine `installed_plugins.json` haath se likhkar gate bypass nahi kiya**, kyunki wo installer ki nakal hoti, install nahi. Rasta: aapke Windows laptop par upar ke teen commands, phir `/sweetclaude:init`. Dhyan: WUR aur SweetClaude dono ek hi repo mein do tracking systems honge.
