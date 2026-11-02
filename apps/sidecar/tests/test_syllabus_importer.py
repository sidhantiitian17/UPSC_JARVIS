"""WU-P02-013: ontology generated from the owner-supplied syllabus (specs/syllabus-official.feature)."""

import re
from pathlib import Path

import pytest

from jarvis.syllabus.importer import TYPO_FIXES, build_ontology, main, write_ontology
from jarvis.syllabus.ontology import load_ontology

MD = Path(__file__).resolve().parents[3] / "datasets" / "syllabus" / "cse-2026-mains.md"


@pytest.fixture(scope="module")
def roots():
    return build_ontology(MD.read_text(encoding="utf-8"))


def flat(node):
    yield node
    for c in node.get("children", []):
        yield from flat(c)


def by_id(roots):
    return {n["id"]: n for r in roots for n in flat(r)}


def topics(roots, paper_id):
    paper = next(r for r in roots if r["id"] == paper_id)
    return [n for n in flat(paper) if n["kind"] == "topic"]


@pytest.mark.parametrize("paper,count", [("gs1", 12), ("gs2", 20), ("gs3", 20), ("gs4", 9)])
def test_point_counts_match_the_totals_the_document_states(roots, paper, count):
    assert len(topics(roots, paper)) == count


def test_subjects_follow_the_document_headings(roots):
    ids = by_id(roots)
    for sid in (
        "gs1.culture", "gs1.history", "gs1.society", "gs1.geography",
        "gs2.polity", "gs2.governance", "gs2.socialjustice", "gs2.ir",
        "gs3.economy", "gs3.agriculture", "gs3.scitech", "gs3.environment", "gs3.disaster", "gs3.security",
        "gs4.ethics",
    ):  # fmt: skip
        assert ids[sid]["kind"] == "subject"
    assert len(ids["gs2.polity"]["children"]) == 9 and len(ids["gs3.security"]["children"]) == 5
    assert len(ids["gs4.ethics"]["children"]) == 9


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def test_every_title_is_the_documents_text_apart_from_listed_spelling_fixes(roots):
    body = MD.read_text(encoding="utf-8").split("---\n", 2)[2]
    body = _norm(re.sub(r"<!-- page \d+ -->", " ", body))
    for wrong, right in TYPO_FIXES.items():
        body = body.replace(wrong, right)
    for n in by_id(roots).values():
        if n["kind"] in ("paper", "subject") and not n["id"].startswith(("soc1.s", "soc2.")):
            continue  # headings of GS papers/subjects are the compiler's own labels
        assert _norm(n["title"]) in body, n["id"]


def test_sociology_paper_one_structure(roots):
    p1 = next(r for r in roots if r["id"] == "soc1")
    sections = p1["children"]
    assert len(sections) == 10 and sections[0]["title"] == "Sociology - The Discipline"
    assert [len(s["children"]) for s in sections] == [3, 5, 3, 6, 4, 3, 4, 3, 5, 5]
    thinkers = sections[3]["children"]
    assert all(t["kind"] == "thinker" for t in thinkers)
    assert thinkers[1]["title"].startswith("Emile Durkheim") and "Talcott Parsons" in thinkers[3]["title"]


def test_sociology_paper_two_structure(roots):
    p2 = next(r for r in roots if r["id"] == "soc2")
    parts = {p["id"]: p for p in p2["children"]}
    assert set(parts) == {"soc2.a", "soc2.b", "soc2.c"}
    assert [len(parts[k]["children"]) for k in ("soc2.a", "soc2.b", "soc2.c")] == [2, 6, 7]
    group = parts["soc2.a"]["children"][0]
    assert group["kind"] == "topic" and [i["kind"] for i in group["children"]] == ["microtheme"] * 3
    assert "G.S. Ghurye" in group["children"][0]["title"]
    last = parts["soc2.c"]["children"][6]
    assert len(last["children"]) == 6 and last["children"][-1]["title"].startswith("Illiteracy")


def test_source_spelling_mistakes_are_fixed_only_in_titles(roots):
    titles = " ".join(n["title"] for n in by_id(roots).values())
    for wrong in ("Durkhteim", "Talcolt", "G.S. Ghure", "func tionalist", "oflabour", "Contem porary"):
        assert wrong not in titles
    raw = MD.read_text(encoding="utf-8")
    assert "Durkhteim" in raw and "Talcolt" in raw


def test_all_generated_nodes_are_owner_supplied_and_unreviewed(roots):
    for n in by_id(roots).values():
        assert n["source"] == "owner" and n["reviewed"] is False


def test_generated_files_load_with_unique_ids(roots, tmp_path):
    write_ontology(roots, tmp_path)
    assert sorted(p.name for p in tmp_path.glob("*.yaml")) == [
        "gs1.yaml",
        "gs2.yaml",
        "gs3.yaml",
        "gs4.yaml",
        "sociology.yaml",
    ]
    nodes = load_ontology(tmp_path)
    assert len({n.id for n in nodes}) == len(nodes) and len(nodes) > 150
    assert {n.paper for n in nodes} == {"GS1", "GS2", "GS3", "GS4", "SOC1", "SOC2"}


def test_regenerating_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    assert main([str(MD), str(a)]) == 0 and main([str(MD), str(b)]) == 0
    for p in a.glob("*.yaml"):
        assert p.read_bytes() == (b / p.name).read_bytes()
        assert b"\r" not in p.read_bytes()


def test_a_document_without_the_expected_structure_is_rejected():
    with pytest.raises(ValueError):
        build_ontology("---\nx: y\n---\nnothing useful here")
