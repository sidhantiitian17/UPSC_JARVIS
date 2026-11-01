"""WU-P01-004: schema v1, reversible migrations, FTS5, sqlite-vec and graph (recursive CTE) queries."""

import sqlite3

import pytest

from jarvis.db.migrate import connect, current_version, latest_version, migrate

EXPECTED_TABLES = {
    "syllabus_node",
    "link",
    "document",
    "chunk",
    "chunk_fts",
    "study_session",
    "question",
    "attempt",
    "card",
    "review_log",
    "llm_cache",
    "llm_usage",
    "setting",
}


@pytest.fixture
def db():
    conn = connect(":memory:")
    migrate(conn)
    yield conn
    conn.close()


def schema(conn):
    rows = conn.execute(
        "select type, name from sqlite_master where name not like 'sqlite_%' and name != 'schema_migrations' "
        "and name not like 'chunk_fts_%' order by type, name"
    ).fetchall()
    return [tuple(r) for r in rows]


def test_migrate_up_creates_all_tables(db):
    names = {r["name"] for r in db.execute("select name from sqlite_master where type in ('table')")}
    assert EXPECTED_TABLES <= names
    assert current_version(db) == latest_version() >= 1


def test_migrate_is_idempotent(db):
    before = schema(db)
    migrate(db)
    assert schema(db) == before


def test_migrations_are_reversible():
    conn = connect(":memory:")
    migrate(conn)
    full = schema(conn)
    migrate(conn, target=0)
    assert current_version(conn) == 0
    assert schema(conn) == []
    migrate(conn)
    assert schema(conn) == full


def test_unknown_target_raises(db):
    with pytest.raises(ValueError):
        migrate(db, target=999)


def test_foreign_keys_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "insert into chunk(document_id,page,ordinal,text,char_start,char_end) values (999,1,0,'x',0,1)"
        )


def test_check_constraints_reject_bad_values(db):
    db.execute("insert into question(kind,source,stem,created_at) values ('mcq','generated','q','t')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("insert into attempt(question_id,correct,confidence,answered_at) values (1,1,'X','t')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("insert into question(kind,source,stem,created_at) values ('essay','generated','q','t')")


def add_doc(db):
    db.execute("insert into document(sha256,path,title,added_at) values ('h','/a.pdf','A','t')")
    return db.execute("select id from document").fetchone()["id"]


def test_fts5_search_stays_in_sync_with_chunks(db):
    d = add_doc(db)
    insert = "insert into chunk(document_id,page,ordinal,text,char_start,char_end) values (?,1,?,?,?,?)"
    db.execute(insert, (d, 0, "The Money Bill is introduced only in Lok Sabha", 0, 44))
    db.execute(insert, (d, 1, "Monsoon winds reverse in summer", 45, 76))
    hit = db.execute("select rowid from chunk_fts where chunk_fts match 'money'").fetchall()
    assert [r[0] for r in hit] == [1]
    db.execute("update chunk set text='Federalism in India' where id=1")
    assert db.execute("select count(*) from chunk_fts where chunk_fts match 'money'").fetchone()[0] == 0
    assert db.execute("select count(*) from chunk_fts where chunk_fts match 'federalism'").fetchone()[0] == 1
    db.execute("delete from chunk where id=1")
    assert db.execute("select count(*) from chunk_fts where chunk_fts match 'federalism'").fetchone()[0] == 0


def test_recursive_cte_walks_the_syllabus_tree(db):
    rows = [
        ("polity", None, "Polity", "subject"),
        ("polity.parl", "polity", "Parliament", "topic"),
        ("polity.parl.money", "polity.parl", "Money Bill", "microtheme"),
        ("polity.parl.ordinary", "polity.parl", "Ordinary Bill", "microtheme"),
        ("eco", None, "Economy", "subject"),
    ]
    db.executemany("insert into syllabus_node(id,parent_id,title,kind) values (?,?,?,?)", rows)
    got = db.execute(
        """with recursive sub(id, depth) as (
               select id, 0 from syllabus_node where id = 'polity'
               union all
               select n.id, sub.depth + 1 from syllabus_node n join sub on n.parent_id = sub.id)
           select id, depth from sub order by depth, id"""
    ).fetchall()
    assert [(r["id"], r["depth"]) for r in got] == [
        ("polity", 0),
        ("polity.parl", 1),
        ("polity.parl.money", 2),
        ("polity.parl.ordinary", 2),
    ]


def test_deleting_a_node_cascades_to_children(db):
    db.executemany(
        "insert into syllabus_node(id,parent_id,title,kind) values (?,?,?,?)",
        [("a", None, "A", "subject"), ("a.b", "a", "B", "topic")],
    )
    db.execute("delete from syllabus_node where id='a'")
    assert db.execute("select count(*) from syllabus_node").fetchone()[0] == 0


def test_sqlite_vec_is_loaded_and_nearest_neighbour_works(db):
    import sqlite_vec

    assert db.execute("select vec_version()").fetchone()[0].startswith("v")
    db.execute("create virtual table v using vec0(embedding float[3])")
    db.execute("insert into v(rowid, embedding) values (1, ?)", (sqlite_vec.serialize_float32([1, 0, 0]),))
    db.execute("insert into v(rowid, embedding) values (2, ?)", (sqlite_vec.serialize_float32([0, 1, 0]),))
    near = db.execute(
        "select rowid from v where embedding match ? and k = 1",
        (sqlite_vec.serialize_float32([0.9, 0.1, 0]),),
    ).fetchone()
    assert near[0] == 1


def test_file_database_uses_wal_and_foreign_keys(tmp_path):
    conn = connect(tmp_path / "jarvis.db")
    assert conn.execute("pragma journal_mode").fetchone()[0] == "wal"
    assert conn.execute("pragma foreign_keys").fetchone()[0] == 1
    conn.close()
