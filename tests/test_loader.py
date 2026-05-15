"""Tests for swerdlow.loader.load_graph."""
from pathlib import Path

import pytest

from swerdlow.loader import load_graph
from swerdlow.types import Edge


def test_simple_graph(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    assert set(g.nodes.keys()) == {"a", "b"}
    assert g.edges == [Edge(from_id="a", to_id="b")]
    assert g.issues == []


def test_node_paths_are_absolute(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    for node in g.nodes.values():
        assert node.path.is_absolute()


def test_deterministic_across_runs(fixture_dir):
    g1 = load_graph(fixture_dir / "simple-graph")
    g2 = load_graph(fixture_dir / "simple-graph")
    assert list(g1.nodes.keys()) == list(g2.nodes.keys())
    assert g1.edges == g2.edges


def test_no_frontmatter_block_is_silent_skip(fixture_dir):
    g = load_graph(fixture_dir / "unindexed")
    assert set(g.nodes.keys()) == {"indexed"}
    assert g.issues == []


def test_malformed_yaml_records_parse_error(fixture_dir):
    g = load_graph(fixture_dir / "parse-error")
    assert "good" in g.nodes
    assert "broken" not in g.nodes
    parse_errors = [i for i in g.issues if i.type == "parse_error"]
    assert len(parse_errors) == 1
    assert "broken" in parse_errors[0].detail or "broken.md" in parse_errors[0].detail


def test_missing_ref_records_issue_no_edge(fixture_dir):
    g = load_graph(fixture_dir / "missing-ref")
    assert "orphan" in g.nodes
    assert g.edges == []
    missing = [i for i in g.issues if i.type == "missing_ref"]
    assert len(missing) == 1
    assert missing[0].doc_id == "orphan"
    assert "ghost" in missing[0].detail


def test_duplicate_id_first_wins_lexically(fixture_dir):
    g = load_graph(fixture_dir / "duplicate-id")
    assert "note" in g.nodes
    # dir-a sorts before dir-b lexically, so dir-a/note.md wins
    assert "dir-a" in str(g.nodes["note"].path)
    dups = [i for i in g.issues if i.type == "duplicate_id"]
    assert len(dups) == 1
    assert "dir-a/note.md" in dups[0].detail
    assert "dir-b/note.md" in dups[0].detail


def test_explicit_id_overrides_filename_stem(fixture_dir):
    g = load_graph(fixture_dir / "id-override")
    assert "custom-id" in g.nodes
    assert "some-file" not in g.nodes


def test_loader_produces_edge_instances(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    # Was: [("a", "b")]; now: [Edge(from_id="a", to_id="b", when=())]
    assert len(g.edges) == 1
    edge = g.edges[0]
    assert isinstance(edge, Edge)
    assert edge.from_id == "a"
    assert edge.to_id == "b"
    assert edge.when == ()


def _find_edge(graph, from_id: str, to_id: str):
    matches = [e for e in graph.edges if e.from_id == from_id and e.to_id == to_id]
    assert len(matches) == 1, f"expected exactly one edge {from_id}→{to_id}, got {len(matches)}"
    return matches[0]


def test_loader_dict_entry_no_when(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-basic")
    e = _find_edge(g, "a", "dict-form-no-when")
    assert e.when == ()


def test_loader_dict_entry_single_mode_in_list(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-basic")
    e = _find_edge(g, "a", "dict-with-single-mode")
    assert e.when == ("narration",)


def test_loader_dict_entry_multi_mode(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-basic")
    e = _find_edge(g, "a", "dict-with-multi-modes")
    assert e.when == ("narration", "plan")


def test_loader_dict_entry_when_as_single_string_coerces(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-basic")
    e = _find_edge(g, "a", "dict-with-string-when")
    assert e.when == ("narration",)


def test_loader_bare_string_still_works(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-basic")
    e = _find_edge(g, "a", "bare-string-form")
    assert e.when == ()


def test_loader_when_empty_list_is_parse_error(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-when-empty")
    assert all(e.to_id != "target" for e in g.edges)
    parse_errors = [i for i in g.issues if i.type == "parse_error"]
    assert len(parse_errors) >= 1
    assert any("when" in e.detail.lower() for e in parse_errors)


def test_loader_malformed_dict_entries(fixture_dir):
    g = load_graph(fixture_dir / "typed-edges-malformed")
    parse_errors = [i for i in g.issues if i.type == "parse_error"]
    # 4 malformed entries → 4 parse_error issues.
    assert len(parse_errors) == 4
    # No edges added for any of the malformed entries.
    assert g.edges == []
