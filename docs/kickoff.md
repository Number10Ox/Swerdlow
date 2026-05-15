# Swerdlow — Project Kickoff

A lightweight markdown-to-markdown dependency layer for AI-assisted codebases. Named for the chronicler from the Nexus comic — the character who records and tracks events across the system.

> This is a kickoff brief, not a final spec. A fresh Claude session should read it cold, then talk to Jon about v0.1 scope before writing any code.

---

## Why this project exists

When you have a project with many markdown docs (specs, ADRs, runbooks, glossaries, design notes), three problems compound:

1. **Implicit dependencies.** Every doc assumes context: a glossary, an architecture overview, upstream module specs. Without a declared dependency graph, every reader — human or LLM — has to guess what else to load. Defaults are bad: copy-paste (each doc re-encodes context) or silent assumption (docs become incomprehensible to outsiders).
2. **Lifecycle blur.** Drafts, accepted specs, superseded specs, frozen audits, and stale plans all share one directory. Nobody knows what's authoritative. LLMs load contradictions and act on them.
3. **No agent-callable graph.** When an AI session is working on feature X, it should be able to ask "which docs govern this work?" and get a minimal correct answer. Today it greps and guesses.

Existing spec-driven dev tools (Spec Kit, BMad, Kiro, OpenSpec, Tessl, GSD) solve the *workflow phase* problem — proposal → spec → design → tasks → code. None of them, as of May 2026, treat the **spec corpus itself** as a first-class graph with declared dependencies.

Swerdlow fills that gap.

## What Swerdlow is

- A tool that reads YAML frontmatter on markdown files and builds a dependency graph.
- Produces context bundles for AI sessions: "working on doc X → load docs Y, Z and source files A, B."
- Reverse-queries from code: "which docs govern `some_module.py`?"
- Detects rot: cycles, orphans, broken refs, conflicting `touches` claims.
- Exposes queries via CLI and an MCP server, so any MCP-aware agent (Claude Code, Cursor, Windsurf, Cline) can use it without project-specific glue.

## What Swerdlow is NOT

- **Not a workflow framework.** No roadmap/phase/execute/verify machinery. That's GSD/Spec Kit territory and is intentionally out of scope.
- **Not opinionated about doc format.** PRD+TDD, ADR, RFC, "design doc," lore page, runbook — all fine. Swerdlow sits underneath whatever convention a project already uses.
- **Not a doc generator.** It indexes existing docs; it doesn't write them.
- **Not narrative-specific.** Works equally well for code project docs and any other markdown corpus.
- **Not a code-doc bridge.** Unlike `lat.md`, Swerdlow's primitive is doc-to-doc dependency, not code-↔-doc linking. `touches` is supported as metadata but is not the central concept.
- **No sidecar metadata files.** Frontmatter lives in the markdown file itself. Unity-style `.meta` files are explicitly out — too painful to maintain alongside the content.

## Pilot consumers

Both already exist in Jon's workspace. Swerdlow must work for both without per-project forks.

| Project | Profile |
|---|---|
| Client production codebase ("Project B") | ~113 flat docs in `docs/`, mixed lifecycle, PRD+TDD convention, implicit cross-refs via prose. Domain-specific production system. |
| ContextDrift | Doc-heavy personal project with its own `.claude/` setup, hooks, custom doc-health check. Already has discipline around CLAUDE.md / MEMORY.md line limits. |

**Success criteria:** after retrofitting, a new Claude session in either project can ask "what do I need to load to work on doc X?" and get a correct, minimal answer.

## Usage docs live elsewhere

The *tool* lives here (`~/workspace/Swerdlow`).

The *usage playbook* — recipes for adopting Swerdlow, retrofit guides, frontmatter conventions, when to use vs. skip — lives in:

```
~/workspace/ClaudeGameDevWorkflows/recipes/swerdlow-*.md
~/workspace/ClaudeGameDevWorkflows/workflows/swerdlow-*.md
```

That repo is Jon's general "playbook to copy from and adapt" repo. Swerdlow's usage docs are workflows others can lift.

## Core concepts

### Frontmatter schema (proposed; refine in v0.1 scoping)

```yaml
---
id: feature-spec                 # stable identifier, unique per project
title: Feature Spec
status: accepted                 # draft | accepted | superseded | archived
type: spec                       # spec | adr | runbook | glossary | overview | audit | note
depends_on: [glossary, module-spec, rules-spec]
touches: [core/some_module.py, core/rules/some_gate.py]
supersedes: []                   # ids of docs this replaces
owners: [aron]
updated: 2026-04-15
---
```

Required fields: `id`, `status`, `type`. Everything else optional. Status vocabulary is project-configurable.

### Project config (`.swerdlow/config.yaml`)

```yaml
roots:
  - docs/
  - docs/audits/
file_patterns: ["*.md"]
status_vocabulary: [draft, accepted, superseded, archived]
default_status: draft
code_roots: [core/, hedgers/, scripts/]   # optional; enables reverse-from-code queries
```

Per-project tuning lives here. The tool itself stays generic.

### Core operations (CLI)

| Command | What it does |
|---|---|
| `swerdlow graph` | Render the full dependency DAG (Graphviz + Mermaid output) |
| `swerdlow bundle <id>` | Output the ordered list of doc + source files to load when working on `<id>` |
| `swerdlow reverse <path>` | Which docs declare they govern this file? |
| `swerdlow check` | Detect cycles, orphans, dead refs, conflicting `touches` claims |
| `swerdlow bootstrap` | Scan existing docs, detect implicit refs, propose frontmatter |
| `swerdlow mcp` | Run as an MCP server (stdio transport) for agent integration |

### MCP integration

Swerdlow ships an MCP server exposing the same operations as tools. One server per project (config local). Any MCP-capable agent gets the graph for free — no project-side prompt engineering required.

## Roadmap

### v0.1 — Read & walk (weekend)

- Parse frontmatter (YAML)
- Build in-memory graph
- `swerdlow graph` → Graphviz + Mermaid output
- `swerdlow bundle <id>` → ordered file list
- CLI only, no MCP yet

**Demo target:** point at a small subset of Project B docs, see the graph render correctly.

### v0.2 — Query & check (weekend)

- `swerdlow reverse <path>`
- `swerdlow check` (cycles, orphans, dead refs, conflicting `touches`)
- MCP server (stdio transport) exposing all of v0.1 + v0.2 ops as tools

**Demo target:** Claude Code session in Project B queries Swerdlow via MCP and gets a correct context bundle for `feature-spec`.

### v0.3 — Bootstrap (~1 week)

- Scan `docs/` and detect implicit cross-refs:
  - Markdown links (`[label](path/to/file.md)`)
  - Bare filename mentions (`feature_spec.md`)
  - Code file mentions matching `code_roots` patterns
  - "See also" / "based on" / "depends on" prose patterns
- Propose frontmatter additions per file
- Interactive review mode (accept/skip/edit per proposal)
- Idempotent: re-running on an already-bootstrapped doc doesn't duplicate

**Demo target:** retrofit Project B's 113-doc `docs/` directory with mostly correct frontmatter in one sitting.

### v0.4+ — Speculative (defer until v0.3 lands)

- Status-aware bundling (skip drafts unless explicitly requested)
- Schema validation against a project-defined doc skeleton
- Watch mode (regenerate graph on file change)
- Git hook: PR touches `some_module.py` without updating any doc that `touches` it → warn
- Obsidian-vault compatibility (so humans can browse the graph in Obsidian)

## Open questions (for v0.1 scoping)

1. **CLI name length.** `swerdlow` is 8 chars. Acceptable, or alias `swd` from day one?
2. **Required vs optional frontmatter fields.** How strict is the schema? Bootstrap will produce docs with missing fields — what's the tolerance?
3. **Transitive resolution.** Does `bundle X` return X's direct deps, or the full transitive closure? Probably the latter, with a `--depth` flag.
4. **Multi-root projects.** Project B has `docs/`, `docs/audits/`, plus scattered top-level `.md` files. ContextDrift has `.claude/` docs and presumably others. Does config support glob roots cleanly?
5. **Wikilink resolution.** Parse Obsidian `[[link]]` style refs natively, or stick to declared frontmatter?
6. **Identifier collisions across projects.** `id` is unique per project; what happens if Swerdlow ever indexes across multiple projects?

## Technology choices (tentative — refine in v0.1)

- **Language:** Python. Both pilot projects are Python-adjacent. Rich markdown + YAML libs (`python-frontmatter`, `mistune`, `networkx`). Anthropic Python MCP SDK is solid.
- **Packaging:** `uv tool install swerdlow` for global use. Project-local config via `.swerdlow/`.
- **Graph engine:** `networkx` in-memory. No persistence in v0.1.
- **MCP:** stdio transport, official Anthropic Python MCP SDK.

## Prior art (study these before designing)

- **[lat.md](https://github.com/1st1/lat.md)** — Code-doc bridge with MCP server. Closest existing tool, but its primitive is code-↔-doc, not doc-↔-doc. Worth studying for MCP integration patterns and `lat check` consistency enforcement.
- **[llm-wiki](https://github.com/jackwener/llm-wiki)** — Agent-native markdown wiki. Closer in spirit (md-first, agent-callable), but no declarative `depends_on`, no lifecycle, no MCP. 65 stars, modest traction.
- **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** — Workflow tool with a change-scoped dep graph. Useful for understanding how to model artifact relationships; not the same problem.
- **[Spec Kit](https://github.com/github/spec-kit)** — Workflow framework, no dep graph. Useful for understanding what Swerdlow is *not*.
- **[adrs (Rust ADR tool)](https://github.com/joshrotenberg/adrs)** — ADR-scoped dep graph via Graphviz + MCP server. Architecturally similar pattern, narrower scope.
- **[spec-compare research repo](https://github.com/cameronsjo/spec-compare)** — Confirms the gap Swerdlow fills.
- **[LEDGE paper (Springer)](https://link.springer.com/article/10.1007/s10515-026-00596-y)** — Academic, GraphRAG-based context-aware doc generation. Conceptually informs the long-term direction.

## How a new Claude session should start

1. Read this doc end-to-end. Do not skim.
2. Read sample docs from the pilot projects:
   - Project B's `CLAUDE.md` and 3–4 representative specs from its `docs/` directory.
   - `~/workspace/ContextDrift/.claude/CLAUDE.md`
3. Skim `lat.md` and `llm-wiki` on GitHub to absorb prior art patterns.
4. Ask Jon which of the open questions need decisions before v0.1.
5. Propose a v0.1 scope (1–2 paragraphs, a checklist of what's in and what's deferred). Wait for his go before writing code.

## Origin context

This brief came out of a Project B working session on 2026-05-11. Jon was investigating Project B's spec-driven workflow and noticed that no existing SDD tool handles doc-to-doc dependencies as a first-class concept. The decision was to *not* enhance Project B's workflow directly, but to build a small reusable tool that both Project B and ContextDrift could adopt without disrupting their existing conventions.

Name comes from Swerdlow, the journalist/chronicler character in Mike Baron and Steve Rude's *Nexus* comic — the figure who records and tracks events across the system. Apt for a tool that indexes a corpus.
