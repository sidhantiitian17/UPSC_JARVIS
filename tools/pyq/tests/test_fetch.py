"""Scenarios from specs/pyq-dataset.feature (fetcher part)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pyq.fetch import (
    LISTING_URL,
    Fetcher,
    Response,
    StructureChangedError,
    Throttle,
    classify,
    parse_listing,
)
from pyq.manifest import load_manifest

FIX = Path(__file__).parent / "fixtures"
PDF_BYTES = b"%PDF-1.4 synthetic"


class FakeHttp:
    def __init__(self, listing_html: str, robots: str = "User-agent: *\nAllow: /\n", etag="v1"):
        self.listing_html, self.robots, self.etag = listing_html, robots, etag
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, headers: dict | None = None) -> Response:
        headers = headers or {}
        self.calls.append((url, headers))
        if url.endswith("/robots.txt"):
            return Response(200, {}, self.robots.encode())
        if url == LISTING_URL:
            return Response(200, {}, self.listing_html.encode())
        if headers.get("If-None-Match") == self.etag:
            return Response(304, {"ETag": self.etag}, b"")
        return Response(200, {"ETag": self.etag, "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"}, PDF_BYTES)

    def pdf_calls(self):
        return [c for c in self.calls if c[0].endswith(".pdf")]


class Clock:
    def __init__(self):
        self.t = 0.0
        self.waits: list[float] = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.waits.append(s)
        self.t += s


def make(tmp_path, http, clock=None, min_interval=2.0):
    clock = clock or Clock()
    th = Throttle(min_interval, clock=clock.now, sleep=clock.sleep)
    f = Fetcher(http, tmp_path, th, user_agent="upsc-jarvis-pyq/0.1 (personal study tool)",
                now=lambda: "2026-11-01T00:00:00Z")
    return f, clock


def listing(name="listing_basic.html"):
    return (FIX / name).read_text(encoding="utf-8")


def test_parse_listing_reads_year_phase_category():
    entries = parse_listing(listing(), LISTING_URL)
    soc = [e for e in entries if "Sociology" in e.title]
    assert {e.year for e in soc} == {2024}
    assert all(e.phase == "mains" and e.category == "Optional" for e in soc)
    assert any(e.phase == "prelims" and "CSAT" in e.title for e in entries)


def test_classify_scope_and_language():
    papers = {(e.phase, e.title): classify(e) for e in parse_listing(listing(), LISTING_URL)}
    assert papers[("prelims", "General Studies Paper-I")] == ("gs-paper-1", "en")
    assert papers[("prelims", "General Studies Paper-II (CSAT)")] == ("csat", "en")
    assert papers[("mains", "General Studies Paper-IV")] == ("gs-4", "en")
    assert papers[("mains", "Essay")] == ("essay", "en")
    assert papers[("mains", "Sociology Paper-II")] == ("sociology-2", "en")
    assert papers[("prelims", "General Studies Paper-I (Hindi)")][1] == "hi"
    assert papers[("mains", "Mystery Booklet")][0] is None


def test_fetcher_is_polite_and_identifies_itself(tmp_path):
    http = FakeHttp(listing())
    f, clock = make(tmp_path, http)
    f.run()
    assert http.calls, "no requests made"
    assert all(h.get("User-Agent", "").startswith("upsc-jarvis-pyq") for _, h in http.calls)
    assert clock.waits and min(clock.waits) >= 2.0 - 1e-9
    # every request after the first was preceded by a >=2s gap
    assert len(clock.waits) >= len(http.calls) - 1


def test_fetcher_resumes_with_etag_and_skips_unchanged(tmp_path):
    http = FakeHttp(listing())
    f, _ = make(tmp_path, http)
    f.run()
    first_pdf_calls = len(http.pdf_calls())
    http2 = FakeHttp(listing())
    f2, _ = make(tmp_path, http2)
    records = f2.run()
    assert len(http2.pdf_calls()) == first_pdf_calls  # re-requested, but conditionally
    assert all("If-None-Match" in h for _, h in http2.pdf_calls())
    assert any(r.status == "unchanged" for r in records)
    # file content not rewritten / still hashed
    rec = next(r for r in records if r.paper == "sociology-1")
    assert rec.sha256 == hashlib.sha256(PDF_BYTES).hexdigest()


def test_fetcher_refuses_to_guess_when_structure_changes(tmp_path):
    http = FakeHttp(listing("listing_changed.html"))
    f, _ = make(tmp_path, http)
    with pytest.raises(StructureChangedError):
        f.run()
    assert not http.pdf_calls()
    snaps = list((tmp_path / "snapshots").glob("listing-*.html"))
    assert len(snaps) == 1 and "redesigned" in snaps[0].read_text(encoding="utf-8")
    assert not (tmp_path / "raw").exists() or not any((tmp_path / "raw").rglob("*.pdf"))


def test_manifest_has_provenance_and_pdfs_land_in_raw(tmp_path):
    f, _ = make(tmp_path, FakeHttp(listing()))
    f.run()
    recs = load_manifest(tmp_path / "manifest.jsonl")
    soc = next(r for r in recs if r.paper == "sociology-1")
    for field in ("url", "exam", "year", "phase", "paper", "sha256", "bytes", "retrieved_at"):
        assert getattr(soc, field) not in (None, ""), field
    assert soc.url.startswith("https://upsc.gov.in/") or soc.url.startswith("https://www.upsc.gov.in/")
    assert Path(tmp_path / soc.local_path).read_bytes() == PDF_BYTES
    assert soc.local_path.startswith("raw/")


def test_hindi_is_skipped_but_recorded(tmp_path):
    http = FakeHttp(listing())
    f, _ = make(tmp_path, http)
    f.run()
    recs = load_manifest(tmp_path / "manifest.jsonl")
    hi = next(r for r in recs if r.lang == "hi")
    assert hi.status == "skipped" and hi.sha256 is None
    assert not any(c[0].endswith("gs1-hi.pdf") for c in http.pdf_calls())


def test_out_of_scope_unclassified_and_non_official_are_recorded_not_downloaded(tmp_path):
    http = FakeHttp(listing())
    f, _ = make(tmp_path, http)
    f.run()
    recs = load_manifest(tmp_path / "manifest.jsonl")
    geo = next(r for r in recs if "Geography" in r.title)
    assert geo.status == "out-of-scope"
    mystery = next(r for r in recs if "Mystery" in r.title)
    assert mystery.status == "unclassified"
    evil = next(r for r in recs if "evil.example.com" in r.url)
    assert evil.status == "blocked-non-official"
    assert not any("evil.example.com" in c[0] or "geo1" in c[0] or "mystery" in c[0] for c in http.pdf_calls())


def test_robots_disallow_is_respected(tmp_path):
    http = FakeHttp(listing(), robots="User-agent: *\nDisallow: /sites/default/files/\n")
    f, _ = make(tmp_path, http)
    f.run()
    assert not http.pdf_calls()
    recs = load_manifest(tmp_path / "manifest.jsonl")
    assert any(r.status == "blocked-by-robots" for r in recs)


def test_manifest_output_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        f, _ = make(d, FakeHttp(listing()))
        f.run()
    assert (a / "manifest.jsonl").read_bytes() == (b / "manifest.jsonl").read_bytes()
    json.loads((a / "manifest.jsonl").read_text().splitlines()[0])
