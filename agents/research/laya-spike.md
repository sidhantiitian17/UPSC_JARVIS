---
type: research
status: active
tags: [research, llm, risk, external]
informs: ["[[roadmap/PHASE_0]]"]
---

# Laya spike (WU-P00-008) — partial result

Date: 2026-11-01 · Machine: **cloud sandbox** (Intel Xeon 2.8 GHz, 4 cores, 15 GB RAM, Linux, Python 3.12.3). **This is not the owner's laptop** (Windows, 16 GB RAM, Ryzen 5 5600H, RX 5500M 4 GB).
Status of the WU: **blocked** — licence read, sandbox AND owner-laptop measurements are done (laptop column below, 2026-11-01); the 50-PYQ zero-shot check is not (needs OCR'd PYQ data, see `agents/roadmap/ALL.md`).

## What was verified (with how)
| Claim | Evidence |
|---|---|
| Weights licence is **Apache-2.0** for `laya`, `laya-multilingual`, `laya-typed-decisions` | HF API `GET /api/models/convaiinnovations/<name>` → `cardData.license = apache-2.0`, tag `license:apache-2.0` |
| `laya-typed-decisions` weights are 842.6 MB | HF API with `blobs=true` (`model.safetensors`) |
| `laya==0.4.20` installs with CPU torch (2.15) in a fresh venv | `uv pip install "laya==0.4.20" torch --extra-index-url https://download.pytorch.org/whl/cpu` |
| `english` checkpoint downloads and runs on CPU | `agents/research/laya-spike-report-sandbox-english.json` |
| Typed-decisions checkpoint is a *specialist* (4 synthetic workflows), choice questions should stay **under ~20 options**, confidence is over-confident/uncalibrated | model card "Limits" section (HF raw README) |
| Loading emits: "this checkpoint ships invalid temperatures or values outside [0.5, 5] … treat confidence as uncalibrated" | warning captured in the run log |

## Measurements (sandbox, `english`, 1 question with 6 options, 20 timed runs after 2 warm-ups)
| Metric | Value |
|---|---|
| Import | 0.11 s |
| First call (includes download + load) | 28.2 s |
| RSS before / after load | 42.8 MB / **2,167.6 MB** |
| Latency p50 / p95 / max | **521 ms** / 598 ms / 741 ms |
| Zero-shot smoke: 6-way subject (n=36) | **86.1%** (random 16.7%) |
| Zero-shot smoke: 10-way directive (n=30) | **80.0%** (random 10%) |

## Owner laptop (Windows 11, Ryzen 5 5600H 12 threads, Python 3.13.5, CPU only) — same command, 2026-11-01
Raw report: `agents/research/laya-spike-report-laptop.json`.
| Metric | Sandbox (Xeon, 4 cores) | Laptop |
|---|---|---|
| First call (download + load) | 28.2 s | **112.6 s** (network-bound, one-time) |
| RSS after load | 2,167.6 MB | **2,081.8 MB** |
| Latency p50 / p95 / max | 521 / 598 / 741 ms | **911 / 981 / 985 ms** |
| Zero-shot smoke 6-way / 10-way | 86.1% / 80.0% | **86.1% / 80.0%** (identical: deterministic, same hand-written data) |

Reading (honest): the laptop is ~1.75x **slower** than the sandbox per call, despite more threads, so laya on this machine fails the 300 ms interactive budget by 3x; RAM is ~2.1 GB. Why it is slower is **unverified** (candidates: thread oversubscription, power plan, background load, torch build; I did not profile or retry with other settings). Python 3.13.5 was used here although the project targets 3.11/3.12 (CLAUDE.md); results may differ on 3.12. Conclusion for the Decision Brain: use laya only for ingest-time (batch) heads, never interactive ones, until a tuned run (ONNX / `max_loaded=1` / thread count) says otherwise. GPU not tried (CPU-first plan).

## How to read these numbers (honestly)
- The smoke data (`tools/brain/src/brain/spike_data.py`) was **hand-written by the assistant**. It is not PYQ data, not a benchmark, and the items are lexically easy (a directive word appears in the stem). With n=30–36 the sampling noise is roughly ±10–15 points.
- The directive result shows laya is the wrong tool for that head: a regex on the stem's first directive word should beat 80%. The Decision-Heads table now routes H4 to rules.
- 521 ms p50 fails the **300 ms interactive budget** (a hypothesis set in `docs/06`) on this 4-core Xeon, and 2.17 GB RSS is slightly over the 2 GB hypothesis. Whether the owner's laptop does better is **unmeasured**. The budget now applies only to interactive heads; ingest-time heads are judged on throughput.
- The earlier statement "zero-shot ≈ chance" belongs to laya's own *typed-decisions benchmark*. It was overstated for simple topic classification; harder heads (hundreds of micro-themes, trap flags, grounding) still need the bake-off.

## Reproduce on the owner's Windows laptop (this produces the numbers that matter)
```powershell
cd tools\brain
uv sync --extra laya
$env:USE_TF = "0"
uv run python -m brain.laya_spike --model english --out laya-spike-report-laptop.json
```
Then compare `latency_one_question.p50_ms`, `rss_mb.after_load` and the first-call time with the table above. If you have an AMD GPU, ignore it for now: CPU-first is the plan (see `docs/06` §6).

## Open items
1. ~~Laptop run~~ done (see above); remaining: profile why it is slower than the sandbox and test ONNX/`max_loaded=1`/thread tuning.
2. 50-PYQ zero-shot → needs WU-P00-003/004 output (blocked on `upsc.gov.in`, see `agents/roadmap/ALL.md`).
3. Licence of the *original* `laya` checkpoint's base model and training data: not checked (the card only says "fine-tuned from `convaiinnovations/laya`").
4. Calibration: temperatures ship invalid → refit per head on held-out data (part of the bake-off).
