"""Syllabus ontology: YAML schema, loader, DB sync and nested tree (specs/syllabus-ontology.feature)."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

Kind = Literal["paper", "subject", "topic", "microtheme", "thinker", "concept"]
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")


class OntologyError(ValueError):
    """The ontology files are invalid; the message names the file and node."""


class OntologyNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    kind: Kind
    paper: str | None = None
    target_pages: int | None = Field(default=None, ge=0)
    source: Literal["draft", "official", "owner"] = "draft"
    reviewed: bool = False
    children: list[OntologyNode] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not ID_RE.match(v):
            raise ValueError("id must be lowercase letters, digits, '.', '_' or '-'")
        return v

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @model_validator(mode="after")
    def _draft_is_not_reviewed(self) -> OntologyNode:
        if self.reviewed and self.source == "draft":
            raise ValueError("reviewed content cannot have source 'draft'")
        return self


class OntologyFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    nodes: list[OntologyNode]


@dataclass(frozen=True)
class FlatNode:
    id: str
    parent_id: str | None
    title: str
    kind: str
    paper: str | None
    sort_order: int
    target_pages: int | None
    reviewed: bool
    source: str


def _flatten(
    nodes: list[OntologyNode],
    parent: str | None,
    paper: str | None,
    out: list[FlatNode],
    seen: dict[str, str],
    file: str,
) -> None:
    for order, n in enumerate(nodes):
        if n.id in seen:
            raise OntologyError(f"{file}: duplicate id {n.id!r} (first defined in {seen[n.id]})")
        seen[n.id] = file
        eff_paper = n.paper or paper
        out.append(
            FlatNode(n.id, parent, n.title, n.kind, eff_paper, order, n.target_pages, n.reviewed, n.source)
        )
        _flatten(n.children, n.id, eff_paper, out, seen, file)


def _describe(e: ValidationError, file: str) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(p) for p in err["loc"])
        parts.append(f"{loc or 'node'}: {err['msg']}")
    return f"{file}: invalid ontology ({'; '.join(parts)})"


def load_ontology(directory: Path) -> list[FlatNode]:
    out: list[FlatNode] = []
    seen: dict[str, str] = {}
    for path in sorted(Path(directory).glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            parsed = OntologyFile.model_validate(raw)
        except yaml.YAMLError as e:
            raise OntologyError(f"{path.name}: not valid YAML ({e})") from e
        except ValidationError as e:
            raise OntologyError(_describe(e, path.name)) from e
        _flatten(parsed.nodes, None, None, out, seen, path.name)
    return out


def sync_ontology(conn: sqlite3.Connection, nodes: list[FlatNode]) -> dict[str, int]:
    """Upsert nodes (ids, hence links, persist). Prune absent nodes unless they or a descendant are linked."""
    for n in nodes:
        conn.execute(
            "insert into syllabus_node"
            "(id,parent_id,title,kind,paper,sort_order,target_pages,reviewed,source) "
            "values (?,?,?,?,?,?,?,?,?) on conflict(id) do update set parent_id=excluded.parent_id, "
            "title=excluded.title, kind=excluded.kind, paper=excluded.paper, sort_order=excluded.sort_order, "
            "target_pages=excluded.target_pages, reviewed=excluded.reviewed, source=excluded.source",
            (
                n.id,
                n.parent_id,
                n.title,
                n.kind,
                n.paper,
                n.sort_order,
                n.target_pages,
                int(n.reviewed),
                n.source,
            ),
        )
    wanted = {n.id for n in nodes}
    parents = {r["id"]: r["parent_id"] for r in conn.execute("select id,parent_id from syllabus_node")}
    linked = {
        r[0]
        for r in conn.execute(
            "select dst_id from link where dst_type='node' "
            "union select src_id from link where src_type='node'"
        )
    }
    protected: set[str] = set()
    for node_id in linked & parents.keys():
        cur: str | None = node_id
        while cur is not None and cur not in protected:
            protected.add(cur)
            cur = parents.get(cur)
    absent = set(parents) - wanted
    prune = absent - protected
    for node_id in prune:
        conn.execute(
            "delete from syllabus_node where id = ?", (node_id,)
        )  # cascade removes unprotected descendants
    return {"upserted": len(nodes), "pruned": len(prune), "kept_linked": len(absent & protected)}


def build_tree(conn: sqlite3.Connection) -> list[dict]:
    rows = [dict(r) for r in conn.execute("select * from syllabus_node order by sort_order, rowid")]
    by_id = {r["id"]: {**r, "reviewed": bool(r["reviewed"]), "children": []} for r in rows}
    roots: list[dict] = []
    for r in rows:
        node = by_id[r["id"]]
        parent = by_id.get(r["parent_id"]) if r["parent_id"] else None
        (parent["children"] if parent else roots).append(node)
    return roots
