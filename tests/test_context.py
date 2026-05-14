"""Tests for swerdlow.context."""
from pathlib import Path

import pytest

from swerdlow.context import ContextError, context
from swerdlow.loader import load_graph


def test_context_no_deps(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    paths, issues = context(g, "b")
    assert [p.name for p in paths] == ["b.md"]
    assert issues == []


def test_context_one_dep(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    paths, issues = context(g, "a")
    assert [p.name for p in paths] == ["b.md", "a.md"]
    assert issues == []


def test_context_transitive(fixture_dir):
    g = load_graph(fixture_dir / "transitive")
    paths, issues = context(g, "top")
    assert [p.name for p in paths] == ["bottom.md", "mid.md", "top.md"]
    assert issues == []


def test_context_same_depth_in_declaration_order(fixture_dir):
    g = load_graph(fixture_dir / "same-depth")
    paths, issues = context(g, "root")
    assert [p.name for p in paths] == ["bravo.md", "alpha.md", "charlie.md", "root.md"]
    assert issues == []
