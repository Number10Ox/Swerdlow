"""Public data types for swerdlow."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Node:
    id: str
    path: Path
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Issue:
    type: str        # "missing_ref" | "duplicate_id" | "parse_error" | "cycle_detected"
    doc_id: str
    detail: str


@dataclass(frozen=True)
class Edge:
    from_id: str
    to_id: str
    when: tuple[str, ...] = ()


@dataclass(frozen=True)
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


@dataclass(frozen=True)
class Proposal:
    file: Path
    add_depends_on: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BootstrapIssue:
    file: Path
    link: str
    detail: str


@dataclass(frozen=True)
class BootstrapPlan:
    proposals: list[Proposal] = field(default_factory=list)
    issues: list[BootstrapIssue] = field(default_factory=list)
