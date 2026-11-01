"""Polite, resumable, manifest-driven fetcher for the OFFICIAL UPSC previous-question-papers page.

The listing structure assumed here (year grouping > table caption > category rows > ul/li/a) was
read from the MIT-licensed scraper realyuvishere/upsc-pyq. It has NOT been verified against the live
site from this sandbox (network was blocked), so a structure mismatch fails loudly (see
StructureChangedError) instead of guessing.
"""
from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.robotparser
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from pyq.manifest import SourceRecord, load_manifest, save_manifest

LISTING_URL = "https://upsc.gov.in/examinations/previous-question-papers"
DEFAULT_UA = "upsc-jarvis-pyq/0.1 (personal study tool; contact: repo owner)"


class StructureChangedError(RuntimeError):
    """The listing page no longer has the expected structure."""


class FetchError(RuntimeError):
    pass


@dataclass
class Response:
    status: int
    headers: dict
    content: bytes


class Http(Protocol):
    def get(self, url: str, headers: dict | None = None) -> Response: ...


class HttpxClient:
    def __init__(self, timeout: float = 60.0):
        import httpx

        self._c = httpx.Client(timeout=timeout, follow_redirects=True)

    def get(self, url: str, headers: dict | None = None) -> Response:
        r = self._c.get(url, headers=headers)
        return Response(r.status_code, dict(r.headers), r.content)


def is_official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "upsc.gov.in" or host.endswith(".upsc.gov.in")


@dataclass
class ListingEntry:
    year: int | None
    phase: str
    category: str
    title: str
    url: str


_YEAR = re.compile(r"\b(19|20)\d{2}\b")


def parse_listing(html: str, base_url: str) -> list[ListingEntry]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[ListingEntry] = []
    cse_tables = 0
    for table in soup.find_all("table"):
        cap = table.find("caption")
        cap_text = cap.get_text(" ", strip=True) if cap else ""
        if "civil services" not in cap_text.lower():
            continue
        cse_tables += 1
        low = cap_text.lower()
        phase = "prelims" if "prelim" in low else "mains" if "main" in low else "unknown"
        year = None
        grouping = table.find_parent(class_="view-grouping")
        header = grouping.find(class_="view-grouping-header") if grouping else None
        for text in (header.get_text(" ", strip=True) if header else "", cap_text):
            m = _YEAR.search(text)
            if m:
                year = int(m.group(0))
                break
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            category = tds[0].get_text(" ", strip=True)
            for li in tr.find_all("li"):
                a = li.find("a", href=True)
                if not a or not a["href"].lower().split("?")[0].endswith(".pdf"):
                    continue
                anchor = a.get_text(" ", strip=True)
                title = " ".join(li.get_text(" ", strip=True).replace(anchor, "").split()) or anchor
                y = year
                if y is None:
                    m = _YEAR.search(title)
                    y = int(m.group(0)) if m else None
                entries.append(ListingEntry(y, phase, category, title, urljoin(base_url, a["href"])))
    if cse_tables == 0 or not entries:
        raise StructureChangedError("no 'Civil Services' tables with PDF links found on the listing page")
    return entries


_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "1": 1, "2": 2, "3": 3, "4": 4}
_PAPER_NUM = re.compile(r"paper[\s\-–—]*\(?(iv|iii|ii|i|[1-4])\b", re.IGNORECASE)


def _paper_num(title: str) -> int | None:
    m = _PAPER_NUM.search(title)
    return _ROMAN[m.group(1).lower()] if m else None


def classify(e: ListingEntry) -> tuple[str | None, str]:
    """Return (paper code | None, language)."""
    text = f"{e.title} {e.category}"
    lang = "hi" if re.search(r"hindi|हिन्दी|हिंदी", text, re.IGNORECASE) else "en"
    t, cat, num = e.title.lower(), e.category.lower(), _paper_num(e.title)
    if "sociology" in t:
        return (f"sociology-{num}" if num in (1, 2) else None), lang
    if e.phase == "prelims":
        if "csat" in t:
            return "csat", lang
        if "general studies" in t or "general studies" in cat:
            return {1: "gs-paper-1", 2: "csat"}.get(num), lang
        return None, lang
    if e.phase == "mains":
        if "essay" in t:
            return "essay", lang
        if "general studies" in t or "general studies" in cat:
            return (f"gs-{num}" if num in (1, 2, 3, 4) else None), lang
    return None, lang


class Throttle:
    def __init__(self, min_interval: float = 2.0, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        self.min_interval, self.clock, self.sleep, self.last = min_interval, clock, sleep, None

    def wait(self) -> None:
        if self.last is not None:
            gap = self.clock() - self.last
            if gap < self.min_interval:
                self.sleep(self.min_interval - gap)
        self.last = self.clock()


def _hdr(headers: dict, name: str) -> str | None:
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return None


class Fetcher:
    def __init__(self, http: Http, out_dir: Path, throttle: Throttle, user_agent: str = DEFAULT_UA,
                 now: Callable[[], str] | None = None, listing_url: str = LISTING_URL):
        self.http, self.out, self.throttle, self.ua = http, Path(out_dir), throttle, user_agent
        self.now = now or (lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        self.listing_url = listing_url

    def _get(self, url: str, headers: dict | None = None) -> Response:
        self.throttle.wait()
        return self.http.get(url, headers={"User-Agent": self.ua, **(headers or {})})

    def _robots(self) -> urllib.robotparser.RobotFileParser:
        rp = urllib.robotparser.RobotFileParser()
        resp = self._get(urljoin(self.listing_url, "/robots.txt"))
        if resp.status == 200:
            rp.parse(resp.content.decode("utf-8", "replace").splitlines())
        elif 400 <= resp.status < 500:
            rp.allow_all = True
        else:
            rp.disallow_all = True  # RFC 9309: unreachable robots.txt => assume disallow
        return rp

    def run(self) -> list[SourceRecord]:
        manifest_path = self.out / "manifest.jsonl"
        existing = {r.url: r for r in load_manifest(manifest_path)}
        robots = self._robots()
        if not robots.can_fetch(self.ua, self.listing_url):
            raise PermissionError("robots.txt disallows the listing page")
        resp = self._get(self.listing_url)
        if resp.status != 200:
            raise FetchError(f"listing page returned HTTP {resp.status}")
        html = resp.content.decode("utf-8", "replace")
        try:
            entries = parse_listing(html, self.listing_url)
        except StructureChangedError:
            snap_dir = self.out / "snapshots"
            snap_dir.mkdir(parents=True, exist_ok=True)
            stamp = re.sub(r"[^0-9A-Za-z]+", "", self.now())
            (snap_dir / f"listing-{stamp}.html").write_text(html, encoding="utf-8")
            raise
        records = [self._process(e, existing.get(e.url), robots) for e in entries]
        seen = {r.url for r in records}
        records += [r for u, r in existing.items() if u not in seen]
        save_manifest(manifest_path, records)
        return records

    def _process(self, e: ListingEntry, prev: SourceRecord | None, robots) -> SourceRecord:
        paper, lang = classify(e)
        rec = SourceRecord(url=e.url, exam="cse", year=e.year, phase=e.phase, category=e.category,
                           title=e.title, paper=paper, lang=lang, status="pending")
        if not is_official(e.url):
            return replace(rec, status="blocked-non-official")
        if lang == "hi":
            return replace(rec, status="skipped", note="Hindi-medium file (out of scope)")
        if paper is None:
            known_other_optional = ("optional" in e.category.lower() or "literature" in e.category.lower()) \
                and _paper_num(e.title) is not None
            lang_qualifying = "language" in e.category.lower()
            return replace(rec, status="out-of-scope" if known_other_optional or lang_qualifying else "unclassified")
        if not robots.can_fetch(self.ua, e.url):
            return replace(rec, status="blocked-by-robots")
        headers = {}
        if prev and prev.sha256 and prev.local_path and (self.out / prev.local_path).exists():
            if prev.etag:
                headers["If-None-Match"] = prev.etag
            elif prev.last_modified:
                headers["If-Modified-Since"] = prev.last_modified
        resp = self._get(e.url, headers)
        if resp.status == 304 and prev:
            return replace(prev, title=e.title, category=e.category, status="unchanged")
        if resp.status != 200:
            return replace(rec, status="failed", note=f"HTTP {resp.status}")
        digest = hashlib.sha256(resp.content).hexdigest()
        rel = f"raw/{e.year}/{e.phase}/{paper}-{hashlib.sha1(e.url.encode()).hexdigest()[:8]}.pdf"
        dest = self.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(resp.content)
        os.replace(tmp, dest)
        return replace(rec, status="downloaded", sha256=digest, bytes=len(resp.content), retrieved_at=self.now(),
                       etag=_hdr(resp.headers, "etag"), last_modified=_hdr(resp.headers, "last-modified"),
                       local_path=rel)
