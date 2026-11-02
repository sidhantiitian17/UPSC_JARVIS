# datasets/syllabus

`cse-2026-mains.md` is the owner-supplied syllabus compilation (GS-I to GS-IV and Sociology) as Markdown, with provenance
and the SHA-256 of the source PDF. The PDF itself is not committed.

`config/syllabus/*.yaml` for GS-I..IV and Sociology is generated from it:

```bash
cd apps/sidecar
uv run python -m jarvis.syllabus.importer ../../datasets/syllabus/cse-2026-mains.md ../../config/syllabus
```

Generated nodes use `source: owner` and `reviewed: false` until the owner has checked them against the UPSC notification.
Prelims and Essay nodes in `config/syllabus` are still assistant-written drafts (the compilation does not cover them).
