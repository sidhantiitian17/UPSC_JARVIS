"""Validation of generated MCQs. Nothing reaches the owner without a verbatim, in-range source quote."""

from __future__ import annotations

MIN_QUOTE_CHARS = 15


def _norm(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def _find_chunk(quote: str, chunks: list[dict]) -> int | None:
    q = _norm(quote)
    if len(q) < MIN_QUOTE_CHARS:
        return None
    for c in chunks:
        if q in _norm(c["text"]):
            return c["id"]
    return None


def validate_batch(
    raw: list[dict], chunks: list[dict], seen_stems: set[str] | None = None
) -> tuple[list[dict], list[dict]]:
    """Split raw model output into (accepted, discarded). `chunks` is exactly the range that was read."""
    seen = set(seen_stems or ())
    accepted: list[dict] = []
    discarded: list[dict] = []

    def reject(item: object, reason: str) -> None:
        stem = item.get("stem", "") if isinstance(item, dict) else ""
        discarded.append({"stem": str(stem)[:80], "reason": reason})

    for item in raw:
        if not isinstance(item, dict):
            reject(item, "not an object")
            continue
        stem = str(item.get("stem", "")).strip()
        options = item.get("options")
        idx = item.get("answer_index")
        if not stem:
            reject(item, "stem is empty")
        elif (
            not isinstance(options, list)
            or len(options) != 4
            or not all(isinstance(o, str) and o.strip() for o in options)
        ):
            reject(item, "needs exactly four options")
        elif len({_norm(o) for o in options}) != 4:
            reject(item, "options are not distinct")
        elif not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < 4:
            reject(item, "answer_index is outside the options")
        elif _norm(stem) in seen:
            reject(item, "repeated stem")
        else:
            chunk_id = _find_chunk(str(item.get("source_quote", "")), chunks)
            if chunk_id is None:
                reject(item, "source_quote is not verbatim from a single chunk in the range")
                continue
            seen.add(_norm(stem))
            style = item.get("style") if item.get("style") in ("recall", "application") else "recall"
            accepted.append(
                {
                    "stem": stem,
                    "options": [o.strip() for o in options],
                    "answer_index": idx,
                    "explanation": str(item.get("explanation", "")),
                    "source_quote": str(item["source_quote"]).strip(),
                    "source_chunk_id": chunk_id,
                    "style": style,
                }
            )
    return accepted, discarded
