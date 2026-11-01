"""WU-P02-001: ontology schema + loader + tree API (specs/syllabus-ontology.feature)."""

import pytest
import yaml
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.db.migrate import connect, migrate
from jarvis.syllabus.ontology import OntologyError, build_tree, load_ontology, sync_ontology

TOKEN = "t" * 32
H = {"Authorization": f"Bearer {TOKEN}"}


def write(d, name, nodes):
    (d / name).write_text(yaml.safe_dump({"version": 1, "nodes": nodes}), encoding="utf-8")


def node(id, title, kind="topic", **kw):
    return {"id": id, "title": title, "kind": kind, **kw}


@pytest.fixture
def conn():
    c = connect(":memory:")
    migrate(c)
    yield c
    c.close()


def test_loads_nested_nodes_with_parent_order_and_paper(tmp_path, conn):
    write(
        tmp_path,
        "polity.yaml",
        [
            node(
                "polity",
                "Polity",
                "subject",
                paper="GS2",
                children=[node("polity.fr", "Fundamental Rights"), node("polity.dpsp", "DPSP")],
            )
        ],
    )
    nodes = load_ontology(tmp_path)
    assert [n.id for n in nodes] == ["polity", "polity.fr", "polity.dpsp"]
    sync_ontology(conn, nodes)
    rows = {r["id"]: dict(r) for r in conn.execute("select * from syllabus_node")}
    assert rows["polity.fr"]["parent_id"] == "polity" and rows["polity.dpsp"]["sort_order"] == 1
    assert rows["polity.fr"]["paper"] == "GS2"  # inherited from the parent
    assert rows["polity"]["source"] == "draft" and rows["polity"]["reviewed"] == 0


def test_duplicate_ids_across_files_fail(tmp_path):
    write(tmp_path, "a.yaml", [node("x", "X", "subject")])
    write(tmp_path, "b.yaml", [node("x", "Again", "subject")])
    with pytest.raises(OntologyError, match="duplicate id 'x'"):
        load_ontology(tmp_path)


@pytest.mark.parametrize(
    "bad,msg",
    [
        (node("a", "A", "chapter"), "kind"),
        (node("a", "", "topic"), "title"),
        (node("Bad Id!", "A", "topic"), "id"),
        (node("a", "A", "topic", source="draft", reviewed=True), "reviewed"),
    ],
)
def test_invalid_nodes_are_rejected_naming_the_node(tmp_path, bad, msg):
    write(tmp_path, "a.yaml", [bad])
    with pytest.raises(OntologyError, match=msg):
        load_ontology(tmp_path)


def test_reload_is_idempotent_keeps_links_and_prunes_only_unlinked(tmp_path, conn):
    write(tmp_path, "a.yaml", [node("s", "S", "subject", children=[node("s.a", "A"), node("s.b", "B")])])
    sync_ontology(conn, load_ontology(tmp_path))
    conn.execute(
        "insert into link(src_type,src_id,dst_type,dst_id,kind) values ('chunk','1','node','s.a','tag')"
    )
    write(tmp_path, "a.yaml", [node("s", "S renamed", "subject")])  # s.a (linked) and s.b removed
    stats = sync_ontology(conn, load_ontology(tmp_path))
    ids = {r["id"]: r["title"] for r in conn.execute("select id,title from syllabus_node")}
    assert ids == {"s": "S renamed", "s.a": "A"}
    assert stats == {"upserted": 1, "pruned": 1, "kept_linked": 1}


def test_build_tree_nests_in_order(tmp_path, conn):
    write(tmp_path, "a.yaml", [node("s", "S", "subject", children=[node("s.2", "Two"), node("s.1", "One")])])
    sync_ontology(conn, load_ontology(tmp_path))
    tree = build_tree(conn)
    assert [t["id"] for t in tree] == ["s"]
    assert [c["id"] for c in tree[0]["children"]] == ["s.2", "s.1"]  # file order, not alphabetical
    assert tree[0]["children"][0]["children"] == [] and tree[0]["source"] == "draft"


def test_shipped_ontology_files_are_valid():
    from jarvis.state import DEFAULT_SYLLABUS

    nodes = load_ontology(DEFAULT_SYLLABUS)
    assert nodes and all(n.source in {"draft", "official", "owner"} for n in nodes)


def test_api_tree_and_reload(tmp_path):
    syl = tmp_path / "syl"
    syl.mkdir()
    write(syl, "a.yaml", [node("s", "S", "subject", children=[node("s.a", "A")])])
    client = TestClient(create_app(TOKEN, data_dir=tmp_path / "d", syllabus_dir=syl))
    assert client.get("/syllabus/tree").status_code == 401
    tree = client.get("/syllabus/tree", headers=H).json()
    assert tree[0]["children"][0]["id"] == "s.a"
    write(syl, "a.yaml", [node("s", "S2", "subject")])
    out = client.post("/syllabus/reload", headers=H).json()
    assert out["upserted"] == 1 and client.get("/syllabus/tree", headers=H).json()[0]["title"] == "S2"


def test_api_reload_reports_invalid_ontology_as_422(tmp_path):
    syl = tmp_path / "syl"
    syl.mkdir()
    write(syl, "a.yaml", [node("s", "S", "subject")])
    client = TestClient(create_app(TOKEN, data_dir=tmp_path / "d", syllabus_dir=syl))
    write(syl, "a.yaml", [node("s", "S", "chapter")])
    r = client.post("/syllabus/reload", headers=H)
    assert r.status_code == 422 and "kind" in r.json()["detail"]
