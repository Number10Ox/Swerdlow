"""Compute the ordered file list for an LLM context bundle."""
from pathlib import Path

from swerdlow.types import Edge, Graph, Issue


class ContextError(Exception):
    """Raised when context() can't produce a result (e.g., target id not in graph)."""


def context(
    graph: Graph,
    doc_id: str,
    modes: list[str] | None = None,
) -> tuple[list[Path], list[Issue]]:
    """Return (ordered_paths, cycle_issues). Deepest deps first, target last.

    If modes is None, every edge is included (v0.1 behavior).
    If modes is a list, an edge is included iff its when is empty (always) OR
    its when intersects modes. Filter applies at every traversal hop.
    """
    if doc_id not in graph.nodes:
        raise ContextError(f"no indexed doc with id '{doc_id}'")
    adjacency = _adjacency(graph, modes)
    visited: set[str] = set()
    order: list[str] = []
    cycle_issues: list[Issue] = []

    def visit(node_id: str, ancestors: set[str]) -> None:
        if node_id in visited:
            return
        if node_id in ancestors:
            cycle_issues.append(Issue(
                type="cycle_detected",
                doc_id=node_id,
                detail=f"cycle edge into '{node_id}' from ancestor chain",
            ))
            return
        ancestors = ancestors | {node_id}
        for dep in adjacency.get(node_id, []):
            visit(dep, ancestors)
        visited.add(node_id)
        order.append(node_id)

    visit(doc_id, set())
    return [graph.nodes[nid].path for nid in order], cycle_issues


def _adjacency(graph: Graph, modes: list[str] | None) -> dict[str, list[str]]:
    """Build adjacency dict, applying mode filter if modes is not None.

    Walks frontmatter['depends_on'] (not graph.edges) to preserve declaration order.
    Cross-references graph.edges via (from_id, to_id) lookup to get Edge.when.
    """
    edge_index: dict[tuple[str, str], Edge] = {(e.from_id, e.to_id): e for e in graph.edges}
    adj: dict[str, list[str]] = {nid: [] for nid in graph.nodes}
    for node in graph.nodes.values():
        for raw in node.frontmatter.get("depends_on", []) or []:
            if isinstance(raw, str):
                target_id = raw
            elif isinstance(raw, dict) and isinstance(raw.get("id"), str):
                target_id = raw["id"]
            else:
                continue
            edge = edge_index.get((node.id, target_id))
            if edge is None:
                continue
            if _edge_passes_filter(edge, modes):
                adj[node.id].append(target_id)
    return adj


def _edge_passes_filter(edge: Edge, modes: list[str] | None) -> bool:
    """Edge passes iff modes is None, edge.when is empty (always), or when intersects modes."""
    if modes is None:
        return True
    if not edge.when:
        return True
    return any(w in modes for w in edge.when)
