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


def test_scan_issue_outside_corpus(fixture_dir):
    plan = scan(fixture_dir / "scan-out-of-scope")
    outside = [i for i in plan.issues if i.detail == "target outside indexed corpus"]
    assert len(outside) == 1
    assert "old.md" in outside[0].link


def test_scan_issue_missing_target(fixture_dir):
    plan = scan(fixture_dir / "scan-out-of-scope")
    missing = [i for i in plan.issues if i.detail == "target file does not exist"]
    assert len(missing) == 1
    assert "does-not-exist.md" in missing[0].link


def test_scan_idempotent_subtracts_existing_deps(fixture_dir):
    plan = scan(fixture_dir / "scan-idempotent")
    # b is already in a's depends_on; scan must not re-propose it.
    a_proposals = [p for p in plan.proposals if p.file.name == "a.md"]
    assert a_proposals == []
