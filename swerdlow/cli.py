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

    args = parser.parse_args(argv)
    project_root = Path.cwd()

    if args.cmd == "init":
        return _cmd_init(project_root, force=args.force)
    if args.cmd == "bootstrap":
        if args.apply:
            return _cmd_bootstrap_apply(project_root)
        return _cmd_bootstrap_scan(project_root, force=args.force)
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


if __name__ == "__main__":
    sys.exit(main())
