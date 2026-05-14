# Swerdlow

A markdown-to-markdown dependency layer for AI-assisted codebases. Indexes a corpus of markdown documents, builds a dependency graph from declared frontmatter, and answers: **"what files should I load to work on document X?"**

## Install

```bash
# From source:
git clone <repo>
cd Swerdlow
pip install -e ".[dev]"
```

## Quickstart

```bash
$ cd ~/your-project
$ swerdlow init                       # writes .swerdlow/config.yaml — edit to set globs
$ swerdlow bootstrap                  # scans corpus, writes .swerdlow/bootstrap.plan.yaml
$ ${EDITOR:-vi} .swerdlow/bootstrap.plan.yaml   # review / adjust / enrich
$ swerdlow bootstrap --apply          # writes depends_on: into your markdown files
$ swerdlow context Combat             # prints ordered context bundle for Combat.md
```

## Concepts

- **Indexed doc** — a markdown file matching the `include` glob with a frontmatter block (even empty `---\n---`).
- **`depends_on:`** — frontmatter list of ids the doc needs as context. Each id defaults to filename stem.
- **Bundle / context** — the target doc plus all transitive `depends_on` deps, deepest first.
- **Bootstrap** — scan for existing markdown links, propose `depends_on:` entries, write to a plan file you review before applying.

See `docs/superpowers/specs/2026-05-14-swerdlow-v0.1-design.md` for the design.

## Status

v0.1. Read + write + context query. No visualization, MCP, reverse lookup, or `check` yet — see the design doc for v0.2+ scope.
