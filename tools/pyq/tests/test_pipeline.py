"""Integration: extract -> parse -> validate -> review over an output dir; CLI error handling."""
from __future__ import annotations

import hashlib

import pytest
from conftest import paginate, prelims_lines

from pyq import pipeline
from pyq.manifest import SourceRecord, save_manifest


def setup_out(tmp_path, write_pdf_fn):
    rel = "raw/2024/prelims/gs-paper-1-abc12345.pdf"
    write_pdf_fn(tmp_path / rel, paginate(prelims_lines(30)))
    rec = SourceRecord(url="https://upsc.gov.in/x.pdf", exam="cse", year=2024, phase="prelims", category="General Studies",
                       title="General Studies Paper-I", paper="gs-paper-1", lang="en", status="downloaded",
                       sha256="ab" * 32, bytes=1, retrieved_at="2026-11-01T00:00:00Z", local_path=rel)
    save_manifest(tmp_path / "manifest.jsonl", [rec])
    return tmp_path


@pytest.fixture
def write_pdf_fn():
    from conftest import write_pdf

    def _w(path, pages):
        path.parent.mkdir(parents=True, exist_ok=True)
        return write_pdf(path, pages)

    return _w


def test_end_to_end_offline_pipeline_and_rerun_identity(tmp_path, write_pdf_fn):
    out = setup_out(tmp_path, write_pdf_fn)
    assert pipeline.extract_all(out) == []
    assert pipeline.parse_all(out) == []
    md = out / "md" / "prelims" / "2024" / "gs-paper-1.md"
    assert md.exists()
    first = hashlib.sha256(md.read_bytes()).hexdigest()
    docs, issues = pipeline.validate_all(out)
    assert len(docs[0].questions) == 30
    assert [i for i in issues["prelims/2024/gs-paper-1"] if i.level == "error"] == []
    assert (out / "reports" / "coverage.md").exists()
    pipeline.parse_all(out)  # re-run without source changes
    assert hashlib.sha256(md.read_bytes()).hexdigest() == first
    sample = pipeline.review_all(out)
    assert sample.exists() and "### PRE-2024-GS1-" in sample.read_text(encoding="utf-8")


def test_scanned_pdf_is_reported_not_parsed(tmp_path, write_pdf_fn):
    rel = "raw/2024/prelims/gs-paper-1-abc12345.pdf"
    write_pdf_fn(tmp_path / rel, [[""], [""]])  # no text layer
    save_manifest(tmp_path / "manifest.jsonl", [SourceRecord(
        url="https://upsc.gov.in/x.pdf", exam="cse", year=2024, phase="prelims", category="c", title="t",
        paper="gs-paper-1", lang="en", status="downloaded", sha256="00", bytes=1, retrieved_at="t", local_path=rel)])
    assert any("scanned" in n for n in pipeline.extract_all(tmp_path))
    assert any("scanned" in n for n in pipeline.parse_all(tmp_path))
    assert not (tmp_path / "md").exists()


def test_cli_reports_network_and_structure_errors_cleanly(tmp_path, monkeypatch, capsys):
    import httpx

    from pyq import cli
    from pyq.fetch import StructureChangedError

    class Boom:
        def __init__(self, exc):
            self.exc = exc

        def run(self):
            raise self.exc

    for exc, needle in ((httpx.ProxyError("403 Forbidden"), "network"), (StructureChangedError("x"), "structure"),
                        (PermissionError("robots"), "robots")):
        monkeypatch.setattr(cli, "Fetcher", lambda *a, _e=exc, **k: Boom(_e))
        assert cli.main(["--out", str(tmp_path), "fetch"]) == 2
        assert needle in capsys.readouterr().err.lower()
