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


def test_apply_preserves_other_fields_and_order(fixture_dir, tmp_path):
    project = _copy_fixture(fixture_dir / "apply-preserve", tmp_path)
    a_path = project / "docs" / "a.md"
    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["new"])])
    apply(plan)
    after = a_path.read_text()
    # The non-depends_on fields must appear in the same order.
    assert after.index("title:") < after.index("status:") < after.index("owners:")
    # title still has its quoted value.
    assert 'title: "Mission Design"' in after or "title: Mission Design" in after
    # The comment is preserved.
    assert "# Hand-curated frontmatter" in after
    # Body untouched.
    assert "Body text." in after
    # Only the depends_on section grew.
    assert "existing" in after
    assert "new" in after


def test_apply_diff_minimal(fixture_dir, tmp_path):
    """Stricter check: line-count delta is small (just the new dep)."""
    project = _copy_fixture(fixture_dir / "apply-preserve", tmp_path)
    a_path = project / "docs" / "a.md"
    before_lines = a_path.read_text().splitlines()
    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["new"])])
    apply(plan)
    after_lines = a_path.read_text().splitlines()
    # Exactly one line added (the new dep).
    assert len(after_lines) == len(before_lines) + 1


def test_apply_missing_target_warns_and_continues(fixture_dir, tmp_path):
    project = _copy_fixture(fixture_dir / "apply-append", tmp_path)
    real_path = project / "docs" / "a.md"
    missing_path = project / "docs" / "does-not-exist.md"
    plan = BootstrapPlan(proposals=[
        Proposal(file=missing_path, add_depends_on=["x"]),
        Proposal(file=real_path, add_depends_on=["new-dep"]),
    ])
    updated, warnings = apply(plan)
    # Real file got updated; missing one logged.
    assert updated == 1
    assert len(warnings) == 1
    assert "does-not-exist.md" in warnings[0]
    assert "new-dep" in real_path.read_text()


def test_apply_preserves_crlf_line_endings(tmp_path):
    # Build a CRLF file directly — don't rely on the fixture directory
    # since git may normalize line endings there.
    a_path = tmp_path / "a.md"
    original_bytes = b"---\r\ndepends_on:\r\n  - existing\r\n---\r\n# A\r\n\r\nBody.\r\n"
    a_path.write_bytes(original_bytes)

    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["new"])])
    apply(plan)

    new_bytes = a_path.read_bytes()
    # CRLF preserved on every original line; new line added (also CRLF).
    assert b"\r\n" in new_bytes
    # No bare-LF lines snuck in (every LF preceded by CR).
    text = new_bytes.decode("utf-8")
    for i, ch in enumerate(text):
        if ch == "\n":
            assert text[i-1] == "\r", f"bare LF at offset {i}"
    # Body preserved.
    assert b"# A" in new_bytes
    assert b"Body." in new_bytes
    # Both deps present.
    assert b"existing" in new_bytes
    assert b"new" in new_bytes


def test_apply_preserves_lf_line_endings_greenfield(tmp_path):
    """Sanity: LF files stay LF (regression check after CRLF fix)."""
    a_path = tmp_path / "a.md"
    original_bytes = b"# A\n\nBody.\n"
    a_path.write_bytes(original_bytes)

    plan = BootstrapPlan(proposals=[Proposal(file=a_path, add_depends_on=["new"])])
    apply(plan)

    new_bytes = a_path.read_bytes()
    assert b"\r\n" not in new_bytes  # didn't accidentally introduce CRLF
    assert b"# A" in new_bytes
    assert b"new" in new_bytes
