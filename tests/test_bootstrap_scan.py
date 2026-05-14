"""Tests for swerdlow.bootstrap.scan."""
from pathlib import Path

import pytest

from swerdlow.bootstrap.scan import scan


def test_scan_detects_simple_link(fixture_dir):
    plan = scan(fixture_dir / "scan-greenfield")
    assert len(plan.proposals) == 1
    assert plan.proposals[0].file.name == "a.md"
    assert plan.proposals[0].add_depends_on == ["b"]


def test_scan_filters_urls_images_code(fixture_dir):
    plan = scan(fixture_dir / "scan-filtered-links")
    proposals = [p for p in plan.proposals if p.file.name == "main.md"]
    assert len(proposals) == 1
    # Only the real markdown link to other.md should be proposed.
    assert proposals[0].add_depends_on == ["other"]


def test_scan_proposes_nothing_for_empty_docs(fixture_dir):
    plan = scan(fixture_dir / "simple-graph")
    # simple-graph already has depends_on in frontmatter, no NEW deps in prose.
    files = {str(p.file) for p in plan.proposals}
    assert files == set()  # idempotent: already declared, nothing new
