"""Apply a BootstrapPlan: write/extend depends_on frontmatter on target files."""
import io
from pathlib import Path

from ruamel.yaml import YAML

from swerdlow.types import BootstrapPlan, Proposal


def apply(plan: BootstrapPlan) -> tuple[int, list[str]]:
    """Apply each proposal. Return (files_updated, warnings)."""
    yaml = YAML(typ="rt")  # round-trip mode preserves comments and order
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    updated = 0
    warnings: list[str] = []
    for prop in plan.proposals:
        if not prop.file.exists():
            warnings.append(f"skip: {prop.file} not found")
            continue
        text = prop.file.read_text()
        new_text = _apply_to_text(text, prop.add_depends_on, yaml)
        if new_text != text:
            prop.file.write_text(new_text)
            updated += 1
    return updated, warnings


def _apply_to_text(text: str, add_deps: list[str], yaml: YAML) -> str:
    if text.startswith("---\n"):
        return _apply_existing(text, add_deps, yaml)
    return _apply_greenfield(text, add_deps, yaml)


def _apply_greenfield(text: str, add_deps: list[str], yaml: YAML) -> str:
    """Prepend a new minimal frontmatter block."""
    fm = {"depends_on": list(add_deps)}
    buf = io.StringIO()
    yaml.dump(fm, buf)
    fm_text = buf.getvalue()
    return f"---\n{fm_text}---\n{text}"


def _apply_existing(text: str, add_deps: list[str], yaml: YAML) -> str:
    """Round-trip the frontmatter block; append new deps non-destructively."""
    lines = text.split("\n")
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i] == "---":
            end_idx = i
            break
    if end_idx is None:
        return _apply_greenfield(text, add_deps, yaml)
    fm_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:])

    fm = yaml.load(fm_text) or {}
    existing = list(fm.get("depends_on", []) or [])
    new_only = [d for d in add_deps if d not in existing]
    if not new_only:
        return text  # idempotent: nothing to add
    fm["depends_on"] = existing + new_only

    buf = io.StringIO()
    yaml.dump(fm, buf)
    new_fm_text = buf.getvalue().rstrip("\n")
    return f"---\n{new_fm_text}\n---\n{body}"
