# Activity Log

Append-only. One line per event. Never edit past entries.

| Date | Event | Detail |
|---|---|---|
| 2026-11-01 | workspace-init | default branch: main (remote empty; to be created at first merge); hooks installed + smoke-tested |
| 2026-11-01 | docs-added | blueprint evaluated (45/46 repos exist; 8 inspected; 12 licences checked); architecture, features, BOM, AI strategy, UX strategy, playbook, specs written; phases 1–10 planned |
| 2026-11-01 | docs-commit | WU-TW-001 adds docs/, specs/, CLAUDE.md, AGENTS.md, README.md |
| 2026-11-01 | commit-index | recorded hashes for WU-TW-000 and WU-TW-001 |
| 2026-11-01 | research | laya inspected (README/BENCHMARKS/finetune/structured, PyPI 0.4.20); OpenPets cli/mcp/ipc/plugins docs read; upsc.gov.in blocked by egress policy (403); 40 repos batch-verified via GitHub API; repo is public, default branch is the feature branch |
| 2026-11-01 | roadmap | Phase 0 added; Sociology ontology WU in P2; OpenPets + ActivityWatch in P3; P4 consumes P0 dataset; ADR-013/014 + 3 agent rules; .gitattributes (LF hooks) and dataset gitignore |
| 2026-11-01 | commit-index | recorded hashes for WU-TW-003 and WU-TW-004 |
| 2026-11-01 | owner-inputs | Hardware recorded (16 GB RAM, Ryzen 5 5600H, GPU model unconfirmed => CPU-first); owner opted in to committing generated PYQ md (raw PDFs stay ignored; repo to be made private after all work; history keeps public-period commits); owner says all domains allowed but running cloud session still gets 403 (checked via curl, httpx and proxy status); SweetClaude pre-flight: plugin installed, project not configured, init not run (needs owner yes) |
| 2026-11-01 | WU-P00-001 | Fetcher tooling done and tested on synthetic HTML + fake HTTP (9 tests). Status blocked: acceptance needs a real run against upsc.gov.in, which this session cannot reach (proxy 403) |
| 2026-11-01 | WU-P00-002 | Extractor + scanned detection + language detection + optional OCRmyPDF path; fixture PDFs generated with reportlab (3 tests) |
| 2026-11-01 | WU-P00-003 | Prelims parser + markdown renderer/loader + JSON Schema, spec-first (13 tests incl. numbered-statements ambiguity, failed-segment flagging, substring-of-source). Status blocked: needs real-PDF runs on >=3 years; heuristic accuracy on real layouts is UNVERIFIED |
