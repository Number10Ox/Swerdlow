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
$ swerdlow modes                      # discover modes used in this corpus
$ swerdlow context Combat --for narration  # filter the bundle to narration-mode edges
```

## Concepts

- **Indexed doc** — a markdown file matching the `include` glob with a frontmatter block (even empty `---\n---`).
- **`depends_on:`** — frontmatter list of ids the doc needs as context. Each id defaults to filename stem.
- **Bundle / context** — the target doc plus all transitive `depends_on` deps, deepest first.
- **Bootstrap** — scan for existing markdown links, propose `depends_on:` entries, write to a plan file you review before applying.
- **Typed edges** — `depends_on` entries can be bare strings (always relevant) or `{id, when: [mode1, mode2]}` dicts (only relevant for the listed modes). `when: []` is a parse error; use bare string or omit `when:` for "always."
- **Mode filtering** — `swerdlow context X --for narration,plan` walks only the edges whose `when:` includes `narration` or `plan`, plus all always-edges. Filter applies at every traversal hop, so non-matching branches cut their descendants too.
- **Mode discovery** — `swerdlow modes` lists the mode tags present in the corpus with edge and doc counts. Use it to spot typos before they bite.

See `docs/superpowers/specs/2026-05-14-swerdlow-v0.1-design.md` for the design.

## Status

v0.2.0 — typed edges, mode scoping, mode discovery. Visualize / reverse / check / MCP remain v0.3+.
