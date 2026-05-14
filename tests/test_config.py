"""Tests for swerdlow.config — load and validate .swerdlow/config.yaml."""
from pathlib import Path

import pytest

from swerdlow.config import Config, ConfigError, load_config


def test_load_config_basic(tmp_path):
    cfg_dir = tmp_path / ".swerdlow"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        'include:\n  - "Docs/**/*.md"\nexclude:\n  - "archive/**"\n'
    )
    cfg = load_config(tmp_path)
    assert cfg.include == ["Docs/**/*.md"]
    assert cfg.exclude == ["archive/**"]
    assert cfg.project_root == tmp_path


def test_load_config_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="config.yaml not found"):
        load_config(tmp_path)


def test_load_config_empty_include(tmp_path):
    cfg_dir = tmp_path / ".swerdlow"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("include: []\n")
    with pytest.raises(ConfigError, match="at least one include pattern"):
        load_config(tmp_path)


def test_load_config_no_exclude(tmp_path):
    cfg_dir = tmp_path / ".swerdlow"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text('include:\n  - "*.md"\n')
    cfg = load_config(tmp_path)
    assert cfg.include == ["*.md"]
    assert cfg.exclude == []


def test_load_config_malformed_yaml(tmp_path):
    cfg_dir = tmp_path / ".swerdlow"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("include: [unclosed\n")
    with pytest.raises(ConfigError, match="failed to parse"):
        load_config(tmp_path)
