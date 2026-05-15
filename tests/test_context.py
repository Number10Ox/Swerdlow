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


def test_context_cycle_terminates_and_emits_issue(fixture_dir):
    g = load_graph(fixture_dir / "cycle")
    paths, issues = context(g, "a")
    # All three docs are reachable; traversal must terminate.
    assert {p.name for p in paths} == {"a.md", "b.md", "c.md"}
    cycle_issues = [i for i in issues if i.type == "cycle_detected"]
    assert len(cycle_issues) >= 1


def test_context_missing_target_raises(fixture_dir):
    g = load_graph(fixture_dir / "simple-graph")
    with pytest.raises(ContextError, match="no indexed doc with id"):
        context(g, "does-not-exist")


def test_context_no_modes_returns_v01_behavior(fixture_dir):
    g = load_graph(fixture_dir / "mode-filter-narration")
    paths, _ = context(g, "NarrativeDesign", modes=None)
    names = {p.name for p in paths}
    assert names == {
        "NarrativeDesign.md", "GamePillars.md",
        "MissionGameplay.md", "InteriorAssets.md",
        "PlanTemplate.md", "DeliverableSpec.md",
    }


def test_context_single_mode_cuts_non_matching_edges(fixture_dir):
    g = load_graph(fixture_dir / "mode-filter-narration")
    paths, _ = context(g, "NarrativeDesign", modes=["narration"])
    names = {p.name for p in paths}
    # NarrativeDesign + always (GamePillars) + narration-edge (MissionGameplay).
    # InteriorAssets cut because its incoming edge from MissionGameplay is design-only.
    # PlanTemplate cut because its incoming edge from NarrativeDesign is plan-only.
    assert names == {"NarrativeDesign.md", "GamePillars.md", "MissionGameplay.md"}


def test_context_filter_at_every_hop(fixture_dir):
    """Spec §7 worked example: A->MissionGameplay (narration kept) -> InteriorAssets (design cut)."""
    g = load_graph(fixture_dir / "mode-filter-narration")
    paths, _ = context(g, "NarrativeDesign", modes=["narration"])
    names = {p.name for p in paths}
    # InteriorAssets must NOT be in bundle even though NarrativeDesign->MissionGameplay survived.
    assert "InteriorAssets.md" not in names


def test_context_multi_mode_union(fixture_dir):
    g = load_graph(fixture_dir / "mode-filter-multi")
    paths, _ = context(g, "root", modes=["m1", "m2"])
    names = {p.name for p in paths}
    assert names == {"root.md", "alpha.md", "bravo.md", "charlie.md"}


def test_context_mode_filter_with_plan_only(fixture_dir):
    g = load_graph(fixture_dir / "mode-filter-narration")
    paths, _ = context(g, "NarrativeDesign", modes=["plan"])
    names = {p.name for p in paths}
    assert names == {"NarrativeDesign.md", "GamePillars.md", "PlanTemplate.md", "DeliverableSpec.md"}


def test_context_unknown_mode_returns_always_only(fixture_dir):
    g = load_graph(fixture_dir / "mode-filter-narration")
    paths, _ = context(g, "NarrativeDesign", modes=["nonexistent"])
    names = {p.name for p in paths}
    assert names == {"NarrativeDesign.md", "GamePillars.md"}


def test_context_v01_signature_still_works(fixture_dir):
    """Backward compatibility: context(graph, id) without modes still works."""
    g = load_graph(fixture_dir / "simple-graph")
    paths, issues = context(g, "a")
    assert [p.name for p in paths] == ["b.md", "a.md"]
    assert issues == []
