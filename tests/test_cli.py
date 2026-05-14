"""Tests for swerdlow.cli — exercise the CLI via subprocess or direct main() invocation."""
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
