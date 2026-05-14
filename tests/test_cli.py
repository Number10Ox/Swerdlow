"""Tests for swerdlow.cli — exercise the CLI via subprocess or direct main() invocation."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "swerdlow", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_cli_init_creates_config(tmp_path):
    result = _run(["init"], cwd=tmp_path)
    assert result.returncode == 0
    cfg = tmp_path / ".swerdlow" / "config.yaml"
    assert cfg.exists()
    assert "include" in cfg.read_text()


def test_cli_init_refuses_overwrite(tmp_path):
    _run(["init"], cwd=tmp_path)
    result = _run(["init"], cwd=tmp_path)
    assert result.returncode != 0
    assert "already exists" in (result.stderr + result.stdout).lower()


def test_cli_init_force_overwrites(tmp_path):
    _run(["init"], cwd=tmp_path)
    result = _run(["init", "--force"], cwd=tmp_path)
    assert result.returncode == 0


def _setup_corpus(fixture_dir: Path, tmp_path: Path) -> Path:
    project = tmp_path / "p"
    shutil.copytree(fixture_dir / "scan-greenfield", project)
    return project


def test_cli_bootstrap_writes_plan(fixture_dir, tmp_path):
    project = _setup_corpus(fixture_dir, tmp_path)
    result = _run(["bootstrap"], cwd=project)
    assert result.returncode == 0
    assert (project / ".swerdlow" / "bootstrap.plan.yaml").exists()


def test_cli_bootstrap_refuses_overwrite(fixture_dir, tmp_path):
    project = _setup_corpus(fixture_dir, tmp_path)
    _run(["bootstrap"], cwd=project)
    result = _run(["bootstrap"], cwd=project)
    assert result.returncode != 0
    assert "already exists" in (result.stderr + result.stdout).lower()


def test_cli_bootstrap_force(fixture_dir, tmp_path):
    project = _setup_corpus(fixture_dir, tmp_path)
    _run(["bootstrap"], cwd=project)
    result = _run(["bootstrap", "--force"], cwd=project)
    assert result.returncode == 0


def test_cli_bootstrap_apply(fixture_dir, tmp_path):
    project = _setup_corpus(fixture_dir, tmp_path)
    _run(["bootstrap"], cwd=project)
    result = _run(["bootstrap", "--apply"], cwd=project)
    assert result.returncode == 0
    a_text = (project / "docs" / "a.md").read_text()
    assert "depends_on" in a_text
    assert "- b" in a_text


def test_cli_bootstrap_apply_missing_plan(tmp_path):
    """Apply with no plan file → exit code 3."""
    (tmp_path / ".swerdlow").mkdir()
    (tmp_path / ".swerdlow" / "config.yaml").write_text('include:\n  - "*.md"\n')
    result = _run(["bootstrap", "--apply"], cwd=tmp_path)
    assert result.returncode == 3
