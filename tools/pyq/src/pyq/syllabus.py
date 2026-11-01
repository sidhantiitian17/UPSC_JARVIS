"""Official syllabus text -> Markdown with provenance. Verbatim text only; no interpretation."""
from __future__ import annotations

from pyq.extract import PageText
from pyq.fetch import is_official


def syllabus_to_md(pages: list[PageText], *, title: str, source_url: str, sha256: str, retrieved_at: str) -> str:
    if not is_official(source_url):
        raise ValueError(f"refusing syllabus from non-official source: {source_url}")
    head = (f"---\ndataset: upsc-syllabus\nschema_version: 1\ntitle: \"{title}\"\nsource_url: \"{source_url}\"\n"
            f"source_sha256: \"{sha256}\"\nretrieved_at: \"{retrieved_at}\"\npage_count: {len(pages)}\n"
            f"status: verbatim-unreviewed\n---\n\n# {title}\n")
    body = "\n".join(f"\n<!-- page {p.number} -->\n\n{p.text.strip()}\n" for p in pages)
    return head + body
