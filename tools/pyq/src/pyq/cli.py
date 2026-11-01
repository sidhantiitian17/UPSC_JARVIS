from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

from pyq import pipeline
from pyq.extract import extract_pdf
from pyq.fetch import DEFAULT_UA, Fetcher, HttpxClient, Throttle
from pyq.keys import apply_key, parse_answer_key
from pyq.render import load_md, render_md
from pyq.review import verify_questions
from pyq.syllabus import syllabus_to_md

DEFAULT_OUT = Path("datasets/pyq")


def _summary(records) -> str:
    counts: dict[str, int] = {}
    for r in records:
        counts[r.status] = counts.get(r.status, 0) + 1
    return ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))


def cmd_fetch(a) -> int:
    f = Fetcher(HttpxClient(), a.out, Throttle(a.delay), user_agent=DEFAULT_UA)
    print("fetched:", _summary(f.run()))
    return 0


def cmd_extract(a) -> int:
    for n in pipeline.extract_all(a.out, ocr=a.ocr):
        print("note:", n)
    return 0


def cmd_parse(a) -> int:
    for n in pipeline.parse_all(a.out):
        print("note:", n)
    return 0


def cmd_validate(a) -> int:
    _, issues = pipeline.validate_all(a.out)
    errors = 0
    for key, items in sorted(issues.items()):
        for i in items:
            errors += i.level == "error"
            print(f"{i.level.upper():7} {key} {i.qid or ''} [{i.code}] {i.message}")
    print(f"{errors} error(s); report: {a.out / 'reports' / 'coverage.md'}")
    return 1 if errors else 0


def cmd_review(a) -> int:
    print("wrote", pipeline.review_all(a.out, a.seed, a.fraction))
    return 0


def cmd_verify(a) -> int:
    files = sorted((a.out / "md").rglob("*.md"))
    total = 0
    for fpath in files:
        text = fpath.read_text(encoding="utf-8")
        mine = [i for i in a.ids if f"id: {i}\n" in text]
        if mine:
            total += verify_questions(fpath, mine)
    print(f"verified {total} question(s)")
    return 0


def cmd_ingest_keys(a) -> int:
    doc = load_md(a.md.read_text(encoding="utf-8"))
    key = parse_answer_key(extract_pdf(a.pdf))
    print(f"applied {apply_key(doc, key, a.url)} answers from {a.url}")
    a.md.write_text(render_md(doc), encoding="utf-8", newline="\n")
    return 0


def cmd_ingest_syllabus(a) -> int:
    pages = extract_pdf(a.pdf)
    sha = hashlib.sha256(a.pdf.read_bytes()).hexdigest()
    dest = a.out / "syllabus" / (a.pdf.stem + ".md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(syllabus_to_md(pages, title=a.title, source_url=a.url, sha256=sha,
                                   retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                    encoding="utf-8", newline="\n")
    print("wrote", dest)
    return 0


def cmd_run(a) -> int:
    for step in (cmd_fetch, cmd_extract, cmd_parse):
        step(a)
    rc = cmd_validate(a)
    cmd_review(a)
    return rc


def _guarded(fn, a) -> int:
    import httpx

    from pyq.fetch import FetchError, StructureChangedError

    try:
        return fn(a)
    except httpx.HTTPError as e:
        print(f"network error: {e}. Is the host allowed by your network policy? Nothing was downloaded.", file=sys.stderr)
    except StructureChangedError as e:
        print(f"page structure changed: {e}. A snapshot was saved under snapshots/; fix parse_listing.", file=sys.stderr)
    except PermissionError as e:
        print(f"blocked by robots.txt: {e}", file=sys.stderr)
    except FetchError as e:
        print(f"fetch failed: {e}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pyq", description="Official UPSC PYQ dataset pipeline")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("fetch", cmd_fetch), ("extract", cmd_extract), ("parse", cmd_parse),
                     ("validate", cmd_validate), ("review", cmd_review), ("run", cmd_run)):
        sp = sub.add_parser(name)
        sp.add_argument("--delay", type=float, default=2.0, help="seconds between requests (min 2.0 recommended)")
        sp.add_argument("--ocr", action="store_true")
        sp.add_argument("--seed", type=int, default=13)
        sp.add_argument("--fraction", type=float, default=0.10)
        sp.set_defaults(fn=fn)
    sp = sub.add_parser("verify")
    sp.add_argument("ids", nargs="+")
    sp.set_defaults(fn=cmd_verify)
    sp = sub.add_parser("ingest-keys")
    sp.add_argument("md", type=Path)
    sp.add_argument("pdf", type=Path)
    sp.add_argument("--url", required=True, help="official URL the key PDF came from")
    sp.set_defaults(fn=cmd_ingest_keys)
    sp = sub.add_parser("ingest-syllabus")
    sp.add_argument("pdf", type=Path)
    sp.add_argument("--url", required=True)
    sp.add_argument("--title", required=True)
    sp.set_defaults(fn=cmd_ingest_syllabus)
    a = p.parse_args(argv)
    return _guarded(a.fn, a)


if __name__ == "__main__":
    sys.exit(main())
