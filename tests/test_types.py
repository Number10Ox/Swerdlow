"""Tests for swerdlow.types — frozen dataclasses, no behavior."""
from pathlib import Path

import pytest

from swerdlow.types import BootstrapIssue, BootstrapPlan, Edge, Graph, Issue, Node, Proposal


def test_node_is_frozen():
    n = Node(id="a", path=Path("a.md"), frontmatter={})
    with pytest.raises(Exception):
        n.id = "b"


def test_node_fields():
    n = Node(id="a", path=Path("a.md"), frontmatter={"depends_on": ["b"]})
    assert n.id == "a"
    assert n.path == Path("a.md")
    assert n.frontmatter == {"depends_on": ["b"]}


def test_issue_fields():
    i = Issue(type="missing_ref", doc_id="a", detail="depends_on 'x' missing")
    assert i.type == "missing_ref"
    assert i.doc_id == "a"
    assert i.detail == "depends_on 'x' missing"


def test_graph_fields():
    n = Node(id="a", path=Path("a.md"), frontmatter={})
    e = Edge(from_id="a", to_id="b")
    g = Graph(nodes={"a": n}, edges=[e], issues=[])
    assert g.nodes == {"a": n}
    assert g.edges == [e]
    assert g.issues == []


def test_graph_is_frozen():
    g = Graph(nodes={}, edges=[], issues=[])
    with pytest.raises(Exception):
        g.nodes = {"a": "x"}


def test_proposal_fields():
    p = Proposal(file=Path("a.md"), add_depends_on=["b", "c"])
    assert p.file == Path("a.md")
    assert p.add_depends_on == ["b", "c"]


def test_bootstrap_issue_fields():
    bi = BootstrapIssue(file=Path("a.md"), link="../x.md", detail="outside corpus")
    assert bi.file == Path("a.md")
    assert bi.link == "../x.md"
    assert bi.detail == "outside corpus"


def test_bootstrap_plan_fields():
    p = Proposal(file=Path("a.md"), add_depends_on=["b"])
    bi = BootstrapIssue(file=Path("c.md"), link="../x.md", detail="missing")
    plan = BootstrapPlan(proposals=[p], issues=[bi])
    assert plan.proposals == [p]
    assert plan.issues == [bi]


def test_bootstrap_plan_defaults_empty():
    plan = BootstrapPlan()
    assert plan.proposals == []
    assert plan.issues == []


def test_edge_fields_default_empty_when():
    e = Edge(from_id="a", to_id="b")
    assert e.from_id == "a"
    assert e.to_id == "b"
    assert e.when == ()


def test_edge_with_when_tuple():
    e = Edge(from_id="a", to_id="b", when=("narration",))
    assert e.when == ("narration",)


def test_edge_is_frozen():
    e = Edge(from_id="a", to_id="b")
    with pytest.raises(Exception):
        e.from_id = "c"


def test_edge_is_hashable():
    e1 = Edge(from_id="a", to_id="b", when=("x",))
    e2 = Edge(from_id="a", to_id="b", when=("x",))
    assert hash(e1) == hash(e2)
    assert {e1, e2} == {e1}
