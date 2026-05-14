"""Tests for swerdlow.loader.load_graph."""
from pathlib import Path

import pytest

from swerdlow.loader import load_graph


def test_simple_graph(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    assert set(g.nodes.keys()) == {"a", "b"}
    assert g.edges == [("a", "b")]
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
