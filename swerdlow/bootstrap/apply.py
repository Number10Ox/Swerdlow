"""Apply a BootstrapPlan: write/extend depends_on frontmatter on target files."""
import io
from pathlib import Path

from ruamel.yaml import YAML

from swerdlow.types import BootstrapPlan, Proposal


def _detect_line_ending(raw_bytes: bytes) -> str:
    r"""Return '\r\n' if the file uses CRLF, else '\n'.

    A file with any CRLF is treated as CRLF (preserves the dominant convention
    on Windows-authored files even if a stray LF snuck in).
    """
    return "\r\n" if b"\r\n" in raw_bytes else "\n"


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
        raw_bytes = prop.file.read_bytes()
        line_ending = _detect_line_ending(raw_bytes)
        # Decode and normalize to LF for internal processing.
        text = raw_bytes.decode("utf-8")
        if line_ending == "\r\n":
            text = text.replace("\r\n", "\n")
        new_text = _apply_to_text(text, prop.add_depends_on, yaml)
        # Convert back to the file's original convention before comparing/writing.
        if line_ending == "\r\n":
            new_bytes = new_text.replace("\n", "\r\n").encode("utf-8")
        else:
            new_bytes = new_text.encode("utf-8")
        if new_bytes != raw_bytes:
            # write_bytes avoids any newline translation surprises.
            prop.file.write_bytes(new_bytes)
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
