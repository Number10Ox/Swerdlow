"""Tests for swerdlow.bootstrap.apply."""
import shutil
from pathlib import Path

import pytest

from swerdlow.bootstrap.apply import apply
from swerdlow.types import BootstrapPlan, Proposal


def _copy_fixture(src: Path, tmp_path: Path) -> Path:
    dest = tmp_path / src.name
    shutil.copytree(src, dest)
    return dest


def test_apply_greenfield_no_frontmatter(fixture_dir, tmp_path):
    project = _copy_fixture(fixture_dir / "apply-greenfield", tmp_path)
    a_path = project / "docs" / "a.md"
    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["b"])])
    apply(plan)
    new_text = a_path.read_text()
    assert new_text.startswith("---\n")
    assert "depends_on:" in new_text
    assert "- b" in new_text
    # Body must be preserved verbatim after the new frontmatter block.
    assert "# A" in new_text
    assert "Body content with no frontmatter." in new_text


def test_apply_appends_to_existing_depends_on(fixture_dir, tmp_path):
    project = _copy_fixture(fixture_dir / "apply-append", tmp_path)
    a_path = project / "docs" / "a.md"
    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["new-dep"])])
    apply(plan)
    text = a_path.read_text()
    # Both deps present, existing first then new.
    assert "existing-dep" in text
    assert "new-dep" in text
    assert text.index("existing-dep") < text.index("new-dep")
    # Body preserved.
    assert "# A" in text
    assert "Body." in text


def test_apply_idempotent_second_call_zero_diff(fixture_dir, tmp_path):
    project = _copy_fixture(fixture_dir / "apply-append", tmp_path)
    a_path = project / "docs" / "a.md"
    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["existing-dep"])])
    before = a_path.read_text()
    apply(plan)
    after = a_path.read_text()
    assert before == after  # already declared; nothing to add
