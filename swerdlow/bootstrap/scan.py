"""Scan the corpus for markdown links and propose depends_on additions."""
from pathlib import Path
from urllib.parse import urlparse

import frontmatter
import mistune

from swerdlow.bootstrap.plan import PLAN_FILENAME, write_plan
from swerdlow.config import load_config
from swerdlow.loader import _walk_corpus
from swerdlow.types import BootstrapIssue, BootstrapPlan, Proposal


def scan(project_root: Path) -> BootstrapPlan:
    cfg = load_config(project_root)
    paths = _walk_corpus(cfg)
    indexed_stems = {p.stem for p in paths}

    proposals: list[Proposal] = []
    issues: list[BootstrapIssue] = []

    for path in paths:
        text = path.read_text()
        # Extract existing depends_on so we can subtract for idempotency.
        existing_deps: set[str] = set()
        has_frontmatter = text.startswith("---")
        if has_frontmatter:
            try:
                post = frontmatter.loads(text)
                existing_deps = set(post.metadata.get("depends_on", []) or [])
            except Exception:
                pass  # parse_error handled by loader, not scan

        link_targets = _extract_markdown_link_targets(text)
        new_deps: list[str] = []
        for link in link_targets:
            if _is_url(link) or not link.endswith(".md"):
                continue
            stem = Path(link).stem
            if stem in indexed_stems:
                if stem not in existing_deps and stem not in new_deps and stem != path.stem:
                    new_deps.append(stem)
            else:
                target_exists = (path.parent / link).resolve().exists()
                detail = (
                    "target file does not exist" if not target_exists
                    else "target outside indexed corpus"
                )
                issues.append(BootstrapIssue(file=path, link=link, detail=detail))

        if new_deps:
            proposals.append(Proposal(file=path, add_depends_on=new_deps))

    # Ensure every indexed file without frontmatter gets at least an empty-deps
    # Proposal so apply will frontmatter it and the loader will index it. This
    # subsumes the Task-25 leaf-target fix (link-targets that lack frontmatter)
    # and also covers "true orphans" — files in the include set with neither
    # incoming nor outgoing markdown links — which would otherwise stay
    # unfrontmatter'd and silently unindexed. Skip files already in proposals
    # and files that already have frontmatter (idempotency).
    proposed_files = {p.file for p in proposals}
    for path in paths:
        if path in proposed_files:
            continue
        if path.read_text().startswith("---"):
            continue
        proposals.append(Proposal(file=path, add_depends_on=[]))

    return BootstrapPlan(proposals=proposals, issues=issues)


def _extract_markdown_link_targets(text: str) -> list[str]:
    """Walk the mistune AST and return all link destinations (NOT image destinations).
    Skip links inside code blocks and inline code spans."""
    md = mistune.create_markdown(renderer="ast")
    ast = md(text)
    targets: list[str] = []
    _walk(ast, targets)
    return targets


def _walk(nodes, targets: list[str]) -> None:
    if isinstance(nodes, list):
        for n in nodes:
            _walk(n, targets)
        return
    if not isinstance(nodes, dict):
        return
    t = nodes.get("type")
    if t == "link":
        targets.append(nodes.get("attrs", {}).get("url", "") or nodes.get("link", ""))
        return  # don't recurse into link children
    if t == "image":
        return  # skip images entirely
    if t in {"block_code", "code_span", "codespan", "code"}:
        return  # skip code blocks/spans
    for key in ("children", "tokens"):
        if key in nodes:
            _walk(nodes[key], targets)


def _is_url(link: str) -> bool:
    parsed = urlparse(link)
    return parsed.scheme in {"http", "https", "ftp", "mailto"}


def scan_and_write(project_root: Path, force: bool = False) -> Path:
    plan = scan(project_root)
    plan_path = project_root / ".swerdlow" / PLAN_FILENAME
    write_plan(plan, plan_path, force=force)
    return plan_path
