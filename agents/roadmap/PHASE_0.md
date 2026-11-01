---
type: phase
status: planned
tags: [state-planned, phase, data, llm, legal, content-review]
---

# Phase 0 — Data & Decision-Brain track (runs parallel to Phase 1–2)

## Goal
(1) Official UPSC site se saare relevant PYQ (Prelims GS-I + CSAT, Mains GS I–IV + Essay, **Sociology Paper I & II**) ka **verified Markdown dataset**; (2) official syllabus + answer keys (sirf official); (3) **laya** ko Windows par measure karke, bake-off se tay karna ki Decision Brain mein kaun sa model jeetega, aur zaroorat par fine-tune.

Design: `docs/07-PYQ-DATASET.md`, `docs/06-BRAIN-DECISION-MODEL.md`. Specs: `specs/pyq-dataset.feature`, `specs/decision-heads.feature`.

## Success Criteria
1. `manifest.jsonl` mein har source PDF ka official URL, sha256, retrieved_at, lang; Hindi files `skipped` ke saath record.
2. Fetcher `robots.txt` follow karta hai, ≥ 2 s delay, resume; koi login/captcha bypass nahi.
3. Prelims + Mains + Sociology md files schema-valid; `coverage.md` har (year × paper) ke liye fetched/parsed/verified/failed dikhata hai.
4. Owner spot-check: Prelims **≥ 98/100**, Mains/Sociology **≥ 47/50**.
5. Official syllabus (Sociology optional dahil) md mein; answer keys sirf official source se (na mile to `null`).
6. Laya Windows spike report (latency, RAM, zero-shot) + bake-off report + adopt/reject decision per head (rule: `docs/06` §5).

## Exit Gate
Owner `accepted` + fresh test output + coverage report + bake-off report. **Blockers:** (a) `upsc.gov.in` network access (cloud sandbox pe blocked; ya local Windows run), (b) dataset publishing policy (repo public hai → default gitignored).

## Out of Scope
PYQ Lab UI (Phase 4), tagging UI, Hindi-medium papers, language/qualifying papers, answer-key *generation* by LLM for scoring.

## Dependencies
None for WU-P00-001…007. WU-P00-008…010 need Python env; 009–010 need a gold set (from 003/004 + owner tagging) and Hugging Face access.

## Work Units
| ID | Goal | Acceptance | Scope | Deps | Verification | Status | Commit |
|---|---|---|---|---|---|---|---|
| WU-P00-001 | Manifest-driven fetcher | Parse listing page; filter CSE Prelims/Mains + Optional Sociology + Essay; `robots.txt`, UA, ≥2 s delay, resume (ETag/Last-Modified), sha256, `manifest.jsonl`; page-structure change → loud error + HTML snapshot | `tools/pyq/fetch*`, `datasets/pyq/manifest.jsonl` | network (A or B) | pytest with recorded HTML fixture + fake server (rate/resume/robots); real run evidence | blocked | — |
| WU-P00-002 | Extractor + scanned detection | Page-wise text via pdfplumber/pypdfium2 (licence verified); chars/page threshold → scanned flag; OCR path (OCRmyPDF) behind flag | `tools/pyq/extract*` | 001 | pytest on fixture PDFs (text + scanned) | ready-for-review | — |
| WU-P00-003 | Parser v1: Prelims (GS-I, CSAT) + schema + md renderer | Questions 1..N, 4 options each, marks/negative from instructions page, front matter + per-question YAML; failed segments flagged, never silently repaired; parsed text ⊂ source text | `tools/pyq/parse_prelims*`, `datasets/pyq/schema/` | 002 | pytest (spec scenarios); real-PDF run on ≥ 3 years | blocked | — |
| WU-P00-004 | Parser v2: Mains, Essay, Sociology multi-part | `parts[]` (label, marks, text), `section` A/B, `word_limit`, marks | `tools/pyq/parse_mains*` | 003 | pytest; real-PDF run; Sociology Paper I/II ≥ 3 years | blocked | — |
| WU-P00-005 | Validator + coverage report + reproducibility | JSON Schema; continuity; counts vs expected (warn); duplicates; `reports/coverage.md`; re-run gives identical output hashes | `tools/pyq/validate*`, `datasets/pyq/reports/` | 003, 004 | pytest; double-run hash equality | planned | — |
| WU-P00-006 | Official syllabus + answer-key ingest | Syllabus (Prelims, Mains, **Sociology Paper I/II**) → md with provenance; answer keys only from official pages; else `null` | `tools/pyq/ingest_official*`, `datasets/pyq/keys/`, `datasets/pyq/syllabus/` | 001, 002 | pytest; owner spot-check | planned | — |
| WU-P00-007 | Review-sample generator + verify workflow | `review-sample.md` (random 10% + flagged), PDF-page text vs parsed side-by-side; CLI `pyq verify <id>` sets status; verified count in front matter | `tools/pyq/review*` | 005 | pytest; owner completes sample | planned | — |
| WU-P00-008 | Laya Windows CPU spike | Install pinned `laya`; model-card/licence read (**needs HF access**); latency + RAM on owner's laptop; zero-shot on 50 PYQs (expect ≈ chance); report | `agents/research/laya-spike.md` | owner env | measured numbers in report | planned | — |
| WU-P00-009 | Bake-off harness | Gold-set loader; contenders A (fastembed+LR), B (SetFit), C (laya), D (LLM teacher); accuracy/macro-F1/ECE/latency/RAM; decision-rule verdict per head | `tools/brain/bakeoff*`, `agents/research/bakeoff.md` | 003, 004, owner gold labels, 008 | pytest on synthetic data; real run report | planned | — |
| WU-P00-010 | First fine-tune (**conditional**) | Only if bake-off says laya wins a head: teacher-label chunks, owner-verified subset, Kaggle 2×T4 run, calibration, report; weights stay local/private until licence verified | `tools/brain/finetune*` | 009 | held-out gold-set metrics ≥ decision rule | planned | — |

## Verification Strategy
Per WU: spec-first tests (fixtures + fake server), real-data run evidence once network allows, owner spot-checks as gates. No claims of dataset completeness without `coverage.md`.
