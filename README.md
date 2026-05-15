# Swerdlow

A markdown-to-markdown dependency layer for AI-assisted codebases. Indexes a corpus of markdown documents, builds a dependency graph from declared frontmatter, and answers: **"what files should I load to work on document X?"**

## Where Swerdlow fits

AI coding tools have converged on four mechanisms for deciding what context to load:

| Trigger | Mechanism | Example |
|---|---|---|
| Always-on | Convention file loaded every session | `CLAUDE.md`, `AGENTS.md`, `.cursorrules` |
| Skill invocation | User types `/X` | Claude Code skills, Cursor slash commands |
| File-path match | Editing a file matching a pattern | Cline `paths:`, Cursor `.mdc` globs, `.claude/rules/` |
| Agent discretion | LLM tool-calls its way to context | Continue.dev, Cline 3.7+, Goose |

**Swerdlow adds a fifth: task/topic-scoped declarative loading.** When you start work on a document, you (or an LLM session) ask `swerdlow context <doc> --for <mode>` and get a deterministic, minimal set of files the doc's author declared as prerequisites for that mode of work.

Why this matters: file-path triggers can't distinguish *two different kinds of work on the same file* — narration work on `NarrativeDesign.md` needs different context than planning work on the same doc. Mode tags on edges (`when: [narration]` vs `when: [plan]`) capture that distinction.

Swerdlow is **complementary to**, not replacing:
- **AGENTS.md / CLAUDE.md** for universal always-on context (vision, terminology, conventions). Anthropic and Augment's empirical data converges on a ~150-200 line ceiling for these files — past that, models stop reliably following the content. Progressive disclosure into linked docs is structurally required, and `@import` doesn't help (imports inline at launch, not on demand).
- **Agent-driven exploration** for filling gaps the graph didn't anticipate. The structured prelude + LLM exploration combination is more cost-effective than either alone.

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

## What belongs where

A practical division for projects already using AGENTS.md or CLAUDE.md:

| Content kind | Lives in | Why |
|---|---|---|
| Vision, pillars, terminology, banned vocabulary | `CLAUDE.md` / `AGENTS.md` | Universal — every session needs it. Keep under ~200 lines. |
| Authoring rules ("when writing scenes, do X") | Skills or path-scoped rules | Triggered by the work itself, not loaded blindly. |
| Subsystem prerequisites ("to understand X, read Y first") | Swerdlow `depends_on:` | What your `swerdlow context` calls resolve. |
| How the code works | (nowhere) | Code is the source of truth. Doc-redundancy rots. |

The operational test (per published research from Anthropic, ETH Zurich, and Augment): **"What would a new teammate need that they can't infer from the code?"** Content that fails this test doesn't belong in a doc at all.

**Roots-as-leaves heuristic:** in a dep graph, "I need this for context" inverts the editorial hierarchy. Vision docs (e.g. GDD, TDD) sit at the top editorially, but in the dep graph subsystems depend on them — not the other way around. So vision docs should either have `depends_on: []` (be graph leaves) or move to the always-on layer entirely.

## Why declared deps vs. just letting the LLM explore?

Both approaches work. Tradeoffs:

- **Declared deps (Swerdlow):** deterministic (same answer every time), free (no LLM round-trips), user-controlled (author intent, not LLM heuristic). Best for corpora the author knows well — design docs, system specs, runbooks.
- **Agent-driven exploration (Continue, Cline 3.7+, Goose):** adaptive, no annotation cost, finds things the author didn't anticipate. Costs many tool-call round-trips per session and depends on LLM heuristics.

The "structured prelude + exploration from there" combination is usually better than either alone: Swerdlow gives the LLM a deterministic starting bundle, and the LLM explores from there if the bundle is incomplete. Future Swerdlow may expose itself as an MCP tool so exploring agents call it as step 1 (v0.4+ idea).

## Status

v0.2.0 — typed edges, mode scoping, mode discovery. Visualize / reverse / `check` / MCP server are v0.3+.

See `docs/superpowers/specs/2026-05-14-swerdlow-v0.2-design.md` for the v0.2 design and `docs/pilots/2026-05-14-contextdrift-phase-a.md` for the ContextDrift pilot findings.
