# Brain / Decision Model — `laya` research aur plan (Hinglish)

> Date: 2026-11-01 · Repo inspected: `NandhaKishorM/laya` (clone + docs padhe) · Status: **research + plan. Kuch bhi train/benchmark nahi hua.**

## 0. Pehle ek correction (meri galti)
Pichle evaluation (`00-EVALUATION.md` row 5) mein maine likha tha ki "JEV koi real model nahi lagta". **Maine tab search nahi kiya tha, wo meri galti thi.** Ab ye pata chala:

- **Jev** = TypeSafe ka *hosted, closed* decision-model API (laya ke BENCHMARKS mein "Jev … third-party published, never measured here — no TypeSafe API access").
- **Laya** = uska **open-source** alternative: Apache-2.0 code, aur `laya-serve` Jev-compatible HTTP protocol deta hai (`choice` / `score` / `noul` answers).
- Blueprint ka full-form "Judgment, Evaluation & Verification" **phir bhi unsupported hai** (kisi source mein nahi mila). Nayi samajh: JEV = *Jev-style typed decision model*, aur hamara engine = **laya**.

## 1. Laya kya hai (aur kya nahi)

| Baat | Detail | Source |
|---|---|---|
| Type | **Non-autoregressive "System 1" decision engine.** Text *generate nahi karta*; ek forward pass mein typed decision deta hai. | README |
| Answer types | `choice` (≤ **32** options), `noul` (yes/no probability), `score` (≤ **10** levels) | `docs/structured.md` (`MAX_OPTIONS=32`, `MAX_SCORE_LEVELS=10`) |
| Size | English aur typed-decisions checkpoints ≈ **421M** parameters; multilingual ≈ **322M** | README (Model setup) |
| Speed (author ka claim) | ~33 ms, 1 question, T4 GPU. **CPU/Windows laptop latency unmeasured** | BENCHMARKS.md |
| Languages | English + multilingual checkpoint (100+ languages) | README |
| Windows | Windows PowerShell instructions + `start.bat`; Windows + Python 3.14 crash fix 0.3.7 mein | README |
| Package | PyPI `laya` **0.4.20** (maine `pip index` se verify kiya); extras: `serve`, `mcp`, `onnx`, … | PyPI |
| Code license | **Apache-2.0** | LICENSE |
| Weights | Hugging Face Hub par. **Weights ka license maine verify nahi kiya**, kyunki sandbox se HF reachable nahi (HTTP 000). Public karne se pehle model card padhna | — |
| Popularity | ★34,782, last push 2026-11-01 (GitHub API) | GitHub |
| Fine-tune | `laya-train` (CSV/JSONL, CPU/CUDA/MPS) + Kaggle **2×T4 free** notebook | `docs/finetune.md` |

**Laya kya *nahi* kar sakta:** MCQ banana, explanation likhna, summary, Mains answer ka remark likhna. Ye sab LLM tiers (`03-FREE-AI-STRATEGY.md`) ka kaam hai.

## 2. Sabse zaroori finding: **fine-tune karna padega**
Laya ke apne docs (`docs/finetune.md`) kehte hain: typed-decisions par base checkpoints **zero-shot lagbhag chance ke barabar** hain (**0.36 aur 0.35**, random baseline 0.318), jabki fine-tuned checkpoint **0.766** (author ka claim). Matlab: *UPSC ke apne decisions ke liye laya ko hamare data par train karna hoga.* Zero-shot par bharosa nahi.

Is-liye plan sirf "laya install karo" nahi, balki **"data banao → bake-off → fine-tune"** hai.

## 3. JARVIS ke "Decision Heads" (jahan laya fit hota hai)

| # | Head | Type | Options/levels | Kaam | Kab banega |
|---|---|---|---|---|---|
| H1 | `syllabus_node` | choice, **hierarchical** (paper→subject→topic→micro-theme; har level ≤ 32) | ≤ 32 per level | chunk / PYQ / CA item ko syllabus node se jodna | P2 (data) → P4 |
| H2 | `grounded` | noul | yes/no | "kya ye answer iss `source_quote` se supported hai?" (MCQ validation) | P2 |
| H3 | `upsc_relevance` | score | 0–4 | CA item / YouTube title / Telegram file kitna relevant | P6, P8 |
| H4 | `directive` | choice | ~12 directives | Mains question ka directive (Discuss, Critically examine…) → structure template | P5 |
| H5 | `trap_flag` | noul × k | per-trap | extreme modifier, word-substitution, contradiction pair (**aapke hit-rate ke saath measure hoga**) | P4 |
| H6 | `pyq_format` | choice | statement / match / assertion-reason / direct | question format | P4 |
| H7 | `mistake_type` | choice | Conceptual / Revision / Silly / Over-elimination | aapke galat jawab ka auto-suggest (aap confirm karoge) | P4+ |
| H8 | `distraction` | choice | study / neutral / distraction | window/app title (ActivityWatch se) | P3 (rules pehle) |
| H9 | `needs_heavy_llm` | choice | local / free-cloud / vision | routing hint | P1+ (rule-based pehle) |

**Rule:** har head ke peeche ek **`DecisionClient`** interface hoga. Backend options: (a) simple rules, (b) baseline classifier, (c) laya, (d) LLM teacher. Jo head bake-off jeete, wahi use hoga (section 5).

**Hierarchical tagging kyun:** laya ek question mein ≤ 32 options leta hai, aur syllabus mein 600+ micro-themes honge. Isliye 3–4 level ka tree: har level par ≤ 32 siblings.

## 4. Training data plan (honest numbers)

**Problem:** PYQs kam hain. Mera rough andaaza (arithmetic, verify karna hai `07-PYQ-DATASET.md` ke coverage report se): Prelims GS ~100 Q/saal × ~15 saal ≈ 1,500; Mains GS + Sociology milakar ≈ 2,000–3,000. 600+ micro-themes par ye sirf **2–5 examples/node** hai. Isliye:

| Data | Kaam | Source |
|---|---|---|
| **PYQs (official)** | **Gold / evaluation set** (train mein nahi, test mein) | P0 dataset |
| **Book chunks** (NCERT, standard books jo aap add karo) | **Training set** (teacher se labelled) | P2 library |
| **Teacher labels** | Free LLM (OmniRoute/Gemini) se **probabilities** nikalo; laya ka `gold` JSONL format teacher probabilities support karta hai | `docs/finetune.md` |
| **Human-verified subset** | Aap har head ke liye **300–500 items** verify karoge (hypothesis: itne kaafi honge; learning-curve se check hoga) | owner |

Ye wahi principle hai jo `03-FREE-AI-STRATEGY.md` mein hai: **LLM quota ek baar label karne mein lagao, phir local model hamesha free.**

Dhyan do (labeling noise): teacher LLM bhi galat hota hai. Isliye gold set sirf human-verified labels se banega, aur teacher-vs-human agreement report mein dikhega.

## 5. Bake-off (kaun sa model sabse best?)

Aapne kaha "research karke best dhoondo ya fine-tune plan karo." Sach ye hai ki **bina aapke data par naap-tol ke "best" batana andaza hoga.** Isliye measured bake-off:

| Contender | Kya hai | Kyun |
|---|---|---|
| **A. Embeddings + Logistic Regression / kNN** | `fastembed` (Apache-2.0, ONNX, CPU, torch ki zaroorat nahi) + sklearn | Sabse simple baseline. Windows par halka. |
| **B. SetFit** | `huggingface/setfit` (Apache-2.0, ★2,858) — few-shot sentence-transformer fine-tune | Chhote data ke liye strong |
| **C. Laya (fine-tuned)** | `laya-train` | Aapki pasand; multi-head, calibrated probabilities, Jev-compatible |
| **D. LLM zero/few-shot** | `LLMClient` ke through free LLM | Teacher + upper-bound reference |

**Metrics (har head par):** accuracy, macro-F1, calibration (ECE), CPU latency (aapke Windows laptop par), RAM, disk, training cost (time/quota).

**Decision rule (hypothesis, pehle se likha taaki post-hoc na ho):**
1. Head ke liye **laya adopt** hoga agar macro-F1 baseline A se **≥ 3 points** behtar ho, **ya** F1 barabar ho par ECE aadha ho.
2. Warna **baseline A** (simple, halka). Laya "Add Later".
3. Latency: CPU par ek decision **≤ 300 ms** (UI block nahi hona chahiye) aur RAM ≤ 2 GB resident. Fail → ONNX/`max_loaded=1`/ya baseline.
4. Agar laya ≥ 3 heads par jeete → laya ko "Decision Brain" ke roop mein ek hi service mein chalayenge (multi-head advantage).

(3 points / 300 ms / 2 GB — ye **starting hypotheses** hain, tuned data ke baad badal sakte hain.)

## 6. Windows deployment (aapka laptop)
- Python **3.11 ya 3.12** pin karo (3.14 par laya ka purana crash fix ho chuka hai, par naya version risk kyun lena).
- `uv` se venv; `pip install laya` (extras: `serve` ya `onnx` zaroorat par).
- Pehle **sidecar ke andar** (Python `laya` package) run. ONNX / `laya-ts` (Electron mein seedha) baad mein, agar latency chahiye.
- Models lazy-load, `Router(max_loaded=1)` (RAM bachane ke liye).
- First download ke liye internet (Hugging Face) chahiye. Aapke laptop par hoga, hamare cloud sandbox mein nahi.
- **Hardware (owner):** 16 GB RAM; GPU: **discrete AMD Radeon RX 5500M (4 GB VRAM, RDNA1)** plus the Ryzen 5 5600H's integrated AMD Radeon Graphics; Windows. Laya (≈ 421M params) 16 GB RAM mein comfortably fit hona chahiye (**andaaza, spike mein measure hoga**). 4 GB VRAM mein ~3B (q4) model comfortably fit hota hai; 7–8B (q4, ~4.5–5 GB) poora VRAM mein nahi aayega (partial offload ya CPU). Ollama ke docs (https://docs.ollama.com/gpu) ke hisaab se Windows par AMD ke liye ROCm ya Vulkan hai; RX 5500 XT unki ROCm table mein hai aur RX 5500M shayad wahi gfx1012 hai, par **ye confirm nahi** (docs mein 5500M ka naam nahi mila), to Vulkan sabse sambhavit raasta hai. Do GPU hone se Ollama integrated GPU chun sakta hai: tab discrete wala `GGML_VK_VISIBLE_DEVICES` se chuno (docs ke hisaab se). **Maine kuch chalakar verify nahi kiya.** PyTorch CUDA AMD par nahi hota, to laya default CPU par; ONNX Runtime DirectML sirf experiment. **Policy: CPU-first default; GPU acceleration ek optional experiment hai jo Ollama server log se verify hoga, kabhi requirement nahi.** Fine-tuning laptop par nahi, **Kaggle free 2×T4** par (laya ke docs ka notebook).
- **Local LLM (Ollama):** interactive kaam ke liye 3–4B (q4) model; 7–8B raat ke batch jobs ke liye (dheema). GPU acceleration ka status upar.

## 7. Spike aur fine-tune: Work Units
(`agents/roadmap/PHASE_0.md` mein)

| WU | Kya |
|---|---|
| WU-P00-008 | **Laya Windows CPU spike**: install, 10 sample decisions, latency + RAM measure, zero-shot accuracy on 50 PYQs (expected near chance — confirm) |
| WU-P00-009 | **Bake-off harness**: gold set loader, A/B/C/D contenders, metrics report, decision-rule evaluation |
| WU-P00-010 | **First fine-tune** (sirf agar bake-off kehta hai): teacher-label chunks, owner verification, Kaggle 2×T4 run, calibration, report |

## 8. Risks aur unverified cheezein
| Risk | Detail | Mitigation |
|---|---|---|
| Benchmarks author ke apne hain | 0.766 / 33 ms / "Jev se behtar" sab self-reported; Jev numbers third-party, unmeasured | Hamara bake-off hi final |
| Weights license unverified | HF unreachable yahan se | WU-P00-008 mein model card padho; public distribution se pehle verify |
| Single-maintainer, fast-moving | 0.4.20, bahut releases | Version pin; `DecisionClient` ke peeche swap |
| Windows CPU latency unmeasured | 421M params | Spike; ONNX/baseline fallback |
| Label noise (teacher LLM) | galat labels | Human-verified gold set; agreement report |
| Hierarchical error compounding | L1 galat → L2 galat | Confidence threshold; "unsure" → LLM / human |
| Over-engineering | Laya na ho to bhi app chalna chahiye | Har head ka rule/baseline fallback; P1–P2 laya ke bina chalte hain |

## 9. Kya badla (architecture mein)
- `docs/architecture.md`: **ADR-013** (Decision Brain), ADR-014 (Windows).
- `CLAUDE.md`: Agent Rule — decision heads sirf `DecisionClient` se; laya generation ke liye nahi.
- `agents/roadmap/PHASE_0.md`: spike + bake-off + fine-tune.
- Laya **Add Later** nahi, balki *"Phase 0 mein evaluate, jeete to adopt"*.

Sources (verified by me): `NandhaKishorM/laya` — README.md, BENCHMARKS.md, `docs/finetune.md`, `docs/structured.md`, LICENSE (clone 2026-11-01); PyPI index; GitHub API metadata.
