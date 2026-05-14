"""Config file loading and validation."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ConfigError(Exception):
    """Raised on missing, invalid, or unparseable config."""


@dataclass(frozen=True)
class Config:
    project_root: Path
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


def load_config(project_root: Path) -> Config:
    cfg_path = project_root / ".swerdlow" / "config.yaml"
    if not cfg_path.exists():
        raise ConfigError(f"config.yaml not found at {cfg_path}")
    try:
        raw = yaml.safe_load(cfg_path.read_text()) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"failed to parse {cfg_path}: {e}") from e
    include = raw.get("include", []) or []
    exclude = raw.get("exclude", []) or []
    if not include:
        raise ConfigError("config must declare at least one include pattern")
    return Config(project_root=project_root, include=list(include), exclude=list(exclude))
