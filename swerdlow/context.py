"""Compute the ordered file list for an LLM context bundle."""
from pathlib import Path

from swerdlow.types import Graph, Issue


class ContextError(Exception):
    """Raised when context() can't produce a result (e.g., target id not in graph)."""


def context(graph: Graph, doc_id: str) -> tuple[list[Path], list[Issue]]:
    """Return (ordered_paths, cycle_issues). Deepest deps first, target last."""
    if doc_id not in graph.nodes:
        raise ContextError(f"no indexed doc with id '{doc_id}'")
    adjacency = _adjacency(graph)
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


def _adjacency(graph: Graph) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {nid: [] for nid in graph.nodes}
    # Preserve declaration order — iterate frontmatter['depends_on'] not graph.edges.
    for node in graph.nodes.values():
        for dep in node.frontmatter.get("depends_on", []) or []:
            if dep in graph.nodes:
                adj[node.id].append(dep)
    return adj
