"""Command-line interface for swerdlow."""
import argparse
import sys
from pathlib import Path

DEFAULT_CONFIG = '''include:
  - "Docs/**/*.md"
exclude:
  - "node_modules/**"
  - "archive/**"
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="swerdlow")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create .swerdlow/config.yaml")
    p_init.add_argument("--force", action="store_true",
                        help="Overwrite existing config")

    p_boot = sub.add_parser("bootstrap", help="Scan corpus or apply plan")
    p_boot.add_argument("--apply", action="store_true",
                        help="Apply the plan file (mutates source files)")
    p_boot.add_argument("--force", action="store_true",
                        help="Overwrite existing plan (scan only)")

    p_ctx = sub.add_parser("context", help="Print ordered context bundle for a doc id")
    p_ctx.add_argument("doc_id", help="The id of the doc you're starting work on")
    p_ctx.add_argument("--for", dest="for_modes", default=None,
                       help="Comma-separated mode tags (e.g., narration,plan)")

    args = parser.parse_args(argv)
    project_root = Path.cwd()

    if args.cmd == "init":
        return _cmd_init(project_root, force=args.force)
    if args.cmd == "bootstrap":
        if args.apply:
            return _cmd_bootstrap_apply(project_root)
        return _cmd_bootstrap_scan(project_root, force=args.force)
    if args.cmd == "context":
        return _cmd_context(project_root, args.doc_id, args.for_modes)
    return 1


def _cmd_init(project_root: Path, force: bool) -> int:
    cfg_dir = project_root / ".swerdlow"
    cfg_path = cfg_dir / "config.yaml"
    if cfg_path.exists() and not force:
        print(f"error: {cfg_path} already exists. Pass --force to overwrite.",
              file=sys.stderr)
        return 1
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(DEFAULT_CONFIG)
    print(f"Created {cfg_path}. Edit to set include/exclude globs.")
    return 0


def _cmd_bootstrap_scan(project_root: Path, force: bool) -> int:
    from swerdlow.bootstrap.scan import scan_and_write
    try:
        plan_path = scan_and_write(project_root, force=force)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Wrote plan to {plan_path}.")
    print(f"Edit the plan, then run: swerdlow bootstrap --apply")
    return 0


def _cmd_bootstrap_apply(project_root: Path) -> int:
    from swerdlow.bootstrap.apply import apply
    from swerdlow.bootstrap.plan import PLAN_FILENAME, load_plan
    plan_path = project_root / ".swerdlow" / PLAN_FILENAME
    if not plan_path.exists():
        print(f"error: no plan file at {plan_path}. Run 'swerdlow bootstrap' first.",
              file=sys.stderr)
        return 3
    plan = load_plan(plan_path)
    updated, warnings = apply(plan)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"Updated {updated} file(s).")
    return 0


def _cmd_context(project_root: Path, doc_id: str, for_modes: str | None) -> int:
    from swerdlow.config import ConfigError
    from swerdlow.context import ContextError, context
    from swerdlow.loader import load_graph
    try:
        graph = load_graph(project_root)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for issue in graph.issues:
        print(f"{issue.type}: {issue.doc_id}: {issue.detail}", file=sys.stderr)

    modes = None
    if for_modes is not None:
        modes = [m.strip() for m in for_modes.split(",") if m.strip()]
        corpus_modes: set[str] = set()
        for e in graph.edges:
            corpus_modes.update(e.when)
        unknown = [m for m in modes if m not in corpus_modes]
        if unknown:
            sorted_corpus = sorted(corpus_modes)
            corpus_list = ", ".join(sorted_corpus) if sorted_corpus else "(none)"
            for u in unknown:
                print(
                    f"warning: mode {u!r} is not present on any edge.\n"
                    f"         Modes used in this corpus: {corpus_list}",
                    file=sys.stderr,
                )

    try:
        paths, cycle_issues = context(graph, doc_id, modes=modes)
    except ContextError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for issue in cycle_issues:
        print(f"{issue.type}: {issue.doc_id}: {issue.detail}", file=sys.stderr)
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
