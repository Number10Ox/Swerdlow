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

    args = parser.parse_args(argv)
    project_root = Path.cwd()

    if args.cmd == "init":
        return _cmd_init(project_root, force=args.force)
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


if __name__ == "__main__":
    sys.exit(main())
