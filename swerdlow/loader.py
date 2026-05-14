"""Build the in-memory graph by reading frontmatter from indexed markdown files."""
from pathlib import Path

import frontmatter
import pathspec

from swerdlow.config import Config, load_config
from swerdlow.types import Graph, Issue, Node


def load_graph(project_root: Path) -> Graph:
    cfg = load_config(project_root)
    paths = _walk_corpus(cfg)
    nodes, issues = _build_nodes(paths)
    edges, more_issues = _build_edges(nodes)
    return Graph(nodes=nodes, edges=edges, issues=issues + more_issues)


def _walk_corpus(cfg: Config) -> list[Path]:
    inc = pathspec.PathSpec.from_lines("gitwildmatch", cfg.include)
    exc = pathspec.PathSpec.from_lines("gitwildmatch", cfg.exclude)
    matched: list[Path] = []
    for p in cfg.project_root.rglob("*.md"):
        rel = p.relative_to(cfg.project_root)
        rel_str = str(rel)
        if inc.match_file(rel_str) and not exc.match_file(rel_str):
            matched.append(p)
    # Lexical sort for deterministic first-wins on duplicate ids (spec §7).
    matched.sort()
    return matched


def _build_nodes(paths: list[Path]) -> tuple[dict[str, Node], list[Issue]]:
    nodes: dict[str, Node] = {}
    issues: list[Issue] = []
    for path in paths:
        text = path.read_text()
        if not text.startswith("---"):
            continue  # no frontmatter block: unindexed, not an error
        try:
            post = frontmatter.loads(text)
        except Exception as e:
            issues.append(Issue(
                type="parse_error",
                doc_id=path.stem,
                detail=f"{path}: failed to parse frontmatter ({e})",
            ))
            continue
        doc_id = post.metadata.get("id") or path.stem
        if doc_id in nodes:
            existing_path = nodes[doc_id].path
            issues.append(Issue(
                type="duplicate_id",
                doc_id=doc_id,
                detail=f"{existing_path} kept; {path} shadowed",
            ))
            continue
        nodes[doc_id] = Node(id=doc_id, path=path, frontmatter=dict(post.metadata))
    return nodes, issues


def _build_edges(nodes: dict[str, Node]) -> tuple[list[tuple[str, str]], list[Issue]]:
    edges: list[tuple[str, str]] = []
    issues: list[Issue] = []
    for node in nodes.values():
        for dep in node.frontmatter.get("depends_on", []) or []:
            if dep in nodes:
                edges.append((node.id, dep))
            else:
                issues.append(Issue(
                    type="missing_ref",
                    doc_id=node.id,
                    detail=f"depends_on '{dep}' has no indexed target",
                ))
    return edges, issues
