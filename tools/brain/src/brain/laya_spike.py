"""WU-P00-008 spike: install check, load time, RAM, latency and a ZERO-SHOT smoke test of laya on this machine.

Run on the owner's Windows laptop to get the numbers that matter (the cloud sandbox is not that machine):
    uv sync --extra laya
    uv run python -m brain.laya_spike --model english --out laya-spike-report.json
The smoke data is hand-written (brain.spike_data), tiny, and NOT a benchmark.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

os.environ.setdefault("USE_TF", "0")  # laya model card: TensorFlow probing can deadlock model construction

from brain.spike_data import DIRECTIVE_ITEMS, DIRECTIVES, SUBJECT_ITEMS, SUBJECTS, build_question
from brain.stats import accuracy, majority_baseline, summarize_latency


def rss_mb() -> float | None:
    try:
        import psutil
    except ImportError:  # optional dependency: install with `uv sync --extra laya`
        return None
    return round(psutil.Process().memory_info().rss / 1e6, 1)


def _pick(result: dict, qid: str) -> str:
    return result["answers"][qid]["choice"]


def run(model: str, runs: int, warmup: int) -> dict:
    t0 = time.perf_counter()
    from laya import Router  # imported late so --help works without torch

    import_s = time.perf_counter() - t0
    rss0 = rss_mb()
    router = Router(max_loaded=1)
    q_subject = {"subject": build_question("subject", "Which UPSC subject does this question belong to?", SUBJECTS)}
    q_direct = {"directive": build_question("directive", "Which UPSC answer directive does this question use?", DIRECTIVES)}

    t1 = time.perf_counter()
    first = router.predict(SUBJECT_ITEMS[0][0], q_subject, model=model)  # includes any first-time download
    first_call_s = time.perf_counter() - t1
    rss1 = rss_mb()
    for _ in range(warmup):
        router.predict(SUBJECT_ITEMS[1][0], q_subject, model=model)

    lat: list[float] = []
    for i in range(runs):
        text = SUBJECT_ITEMS[i % len(SUBJECT_ITEMS)][0]
        s = time.perf_counter()
        router.predict(text, q_subject, model=model)
        lat.append(time.perf_counter() - s)

    def zero_shot(items, questions, qid):
        pred = [_pick(router.predict(t, questions, model=model), qid) for t, _ in items]
        gold = [g for _, g in items]
        return {"n": len(gold), "accuracy": round(accuracy(pred, gold), 3),
                "majority_baseline": round(majority_baseline(gold), 3),
                "random_baseline": round(1 / len(set(gold)), 3)}

    return {
        "model": model,
        "routing_model_used": first.get("routing", {}).get("model"),
        "env": {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(),
                "cpu_count": os.cpu_count()},
        "import_s": round(import_s, 2),
        "first_call_s_includes_download": round(first_call_s, 2),
        "rss_mb": {"before_load": rss0, "after_load": rss1, "after_runs": rss_mb()},
        "latency_one_question": {k: round(v, 1) if isinstance(v, float) else v
                                 for k, v in summarize_latency(lat).items()},
        "zero_shot_smoke": {"subject_6_way": zero_shot(SUBJECT_ITEMS, q_subject, "subject"),
                            "directive_10_way": zero_shot(DIRECTIVE_ITEMS, q_direct, "directive")},
        "caveat": "hand-written smoke data (not PYQs, not a benchmark); sample too small for conclusions",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="english", choices=["english", "multilingual", "typed-decisions"])
    p.add_argument("--runs", type=int, default=20)
    p.add_argument("--warmup", type=int, default=2)
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args(argv)
    report = run(a.model, a.runs, a.warmup)
    text = json.dumps(report, indent=2)
    print(text)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
