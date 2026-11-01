# datasets/pyq

Spec: `docs/07-PYQ-DATASET.md`. Raw PDFs and generated Markdown are **gitignored** (public repo). `manifest.jsonl` is tracked once WU-P00-001 runs.

## Commands (from `tools/pyq`)

```bash
uv sync
uv run pyq --out ../../datasets/pyq run        # fetch -> extract -> parse -> validate -> review sample
uv run pyq --out ../../datasets/pyq verify PRE-2024-GS1-001 PRE-2024-GS1-002
```

Raw PDFs and snapshots stay gitignored. Generated md/keys/syllabus/reports are committed (owner opt-in; see `docs/07-PYQ-DATASET.md` section 3).
