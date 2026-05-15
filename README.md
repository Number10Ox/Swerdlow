# Swerdlow

A markdown-to-markdown dependency layer for AI-assisted codebases. Give it one anchor (a doc id or topic). It returns the ordered set of files an LLM session needs as context for that anchor's task. You don't have to enumerate the graph by hand at the start of every conversation or agent run.

Named after Swerdlow, the journalist and chronicler from Mike Baron and Steve Rude's *Nexus*. He records and tracks events across a system. Seemed fitting.

---

## Why this exists

A project with many markdown docs (specs, ADRs, runbooks, glossaries, design notes) hits three compounding problems.

**Implicit dependencies.** Every doc assumes context. A glossary. An architecture overview. Upstream module specs. Without a declared dependency graph, every reader (human or LLM) has to guess what else to load. The fallback patterns are bad. Copy-paste, where each doc re-encodes its context. Or silent assumption, where docs become incomprehensible to outsiders.

**Lifecycle blur.** Drafts, accepted specs, superseded specs, frozen audits, and stale plans all share one directory. Nobody knows what's authoritative. LLMs load contradictions and act on them.

**No agent-callable graph.** When an AI session is working on feature X, it should be able to ask "which docs govern this work?" and get a minimal correct answer. Today it greps and guesses.

Existing spec-driven dev tools (Spec Kit, BMAD, Kiro, OpenSpec, Tessl, GSD) solve the workflow problem: proposal, spec, design, tasks, code. None of them treat the spec corpus itself as a first-class graph with declared dependencies. That's the gap Swerdlow fills.

The tool came out of a working session on a client project. About 100 docs were cross-referencing each other implicitly. Loading the right context for any task required tribal knowledge. The bet was that a small generic tool would beat a project-specific workflow hack.

---

## Where Swerdlow fits

AI coding tools have converged on four mechanisms for deciding what context to load:

| Trigger | Mechanism | Example |
|---|---|---|
| Always-on | Convention file loaded every session | `CLAUDE.md`, `AGENTS.md`, `.cursorrules` |
| Skill invocation | User types `/X` | Claude Code skills, Cursor slash commands |
| File-path match | Editing a file matching a pattern | Cline `paths:`, Cursor `.mdc` globs, `.claude/rules/` |
| Agent discretion | LLM tool-calls its way to context | Continue.dev, Cline 3.7+, Goose |

Swerdlow adds a fifth: task or topic-scoped declarative loading. You ask `swerdlow context <doc> --for <mode>` at the start of a session. You get back the deterministic, minimal set of files the doc's author declared as prerequisites for that mode of work.

File-path triggers can't distinguish two different kinds of work on the same file. Narration work on `NarrativeDesign.md` needs different context than planning work on the same doc. Mode tags on edges (`when: [narration]` vs `when: [plan]`) capture that distinction.

Swerdlow is complementary to two other layers, not a replacement for them.

**AGENTS.md / CLAUDE.md** carry universal always-on context. Vision, terminology, conventions. Anthropic and Augment's empirical data converges on a 150-200 line ceiling for these files. Past that, models stop reliably following the content. Progressive disclosure into linked docs is structurally required. (`@import` doesn't help. Imports inline at launch, not on demand.)

**Agent-driven exploration** fills gaps the graph didn't anticipate. The structured prelude plus LLM exploration combination tends to beat either alone.

---

## Install

```bash
# From source:
git clone https://github.com/Number10Ox/Swerdlow.git
cd Swerdlow
pip install -e ".[dev]"
```

Python 3.11+ required.

---

## Quickstart

```bash
$ cd ~/your-project
$ swerdlow init                       # writes .swerdlow/config.yaml, edit to set globs
$ swerdlow bootstrap                  # scans corpus, writes .swerdlow/bootstrap.plan.yaml
$ ${EDITOR:-vi} .swerdlow/bootstrap.plan.yaml   # review, adjust, enrich
$ swerdlow bootstrap --apply          # writes depends_on: into your markdown files
$ swerdlow context Combat             # prints ordered context bundle for Combat.md
$ swerdlow modes                      # discover modes used in this corpus
$ swerdlow context Combat --for narration  # filter the bundle to narration-mode edges
```

---

## Concepts

**Indexed doc.** A markdown file matching the `include` glob with a frontmatter block. Even an empty block (`---\n---`) counts.

**`depends_on:`.** Frontmatter list of ids the doc needs as context. Each id defaults to the filename stem.

**Bundle (a.k.a. context).** The target doc plus all transitive `depends_on` deps, deepest first.

**Bootstrap.** Scan for existing markdown links. Propose `depends_on:` entries. Write to a plan file. You review before applying.

**Typed edges.** A `depends_on` entry is either a bare string (always relevant) or a dict `{id, when: [mode1, mode2]}` (only relevant for the listed modes). `when: []` is a parse error. Use a bare string or omit `when:` entirely for "always."

**Mode filtering.** `swerdlow context X --for narration,plan` walks only edges whose `when:` includes `narration` or `plan`, plus all always-edges. Filtering applies at every traversal hop. A non-matching edge cuts its descendants too.

**Mode discovery.** `swerdlow modes` lists the mode tags present in the corpus with edge and doc counts. Use it to spot typos before they bite.

---

## What belongs where (designing your doc corpus)

If your project already uses AGENTS.md or CLAUDE.md, here's a practical division:

| Content kind | Lives in | Why |
|---|---|---|
| Vision, pillars, terminology, banned vocabulary | `CLAUDE.md` / `AGENTS.md` | Universal. Every session needs it. Keep under ~200 lines. |
| Authoring rules ("when writing scenes, do X") | Skills or path-scoped rules | Triggered by the work itself, not loaded blindly. |
| Subsystem prerequisites ("to understand X, read Y first") | Swerdlow `depends_on:` | What your `swerdlow context` calls resolve. |
| How the code works | (nowhere) | Code is the source of truth. Doc-redundancy rots. |

Anthropic, ETH Zurich, and Augment converge on one operational test: "what would a new teammate need that they can't infer from the code?" If a piece of content fails that test, it doesn't belong in a doc.

**Roots-as-leaves.** In a dep graph, "I need this for context" inverts the editorial hierarchy. Vision docs like GDD or TDD sit at the top editorially. In the dep graph, subsystems depend on them. So vision docs should be graph leaves with `depends_on: []`, or live in the always-on layer entirely.

**Annotation discipline.** If your design doc has a "Related docs (load when touching that area)" prose table, translate the "Load when..." column straight into `when:` tags. The table you already wrote is the design source for your mode taxonomy.

---

## Design decisions

The load-bearing choices, with rationale. Full design specs in `docs/superpowers/specs/`.

### Declared (frontmatter) over inferred (RAG / NLP)

Author intent is more reliable than inference from prose. The writer of "to work on the combat system, you need the game pillars" knows what the doc needs. An embedding model guesses. Declared deps are deterministic, inspectable in git diffs, cost zero LLM round-trips at query time, and let the author control what context propagates rather than leaving it to runtime heuristics.

RAG is the right answer for "find me docs about X" on a corpus the author doesn't know well. Swerdlow is the right answer for "load the prerequisites to work on Y" on a corpus the author maintains.

### Per-edge typed metadata over doc-level scope tags

Pilot evidence (ContextDrift's "Related docs (load when touching that area)" prose tables) showed that mode-scoping is per-edge in practice. The same doc references doc Y in mode A and doc Z in mode B. Doc-level scope would force a single mode tag on all of doc Y's outbound edges, which loses information. Per-edge `{id, when: [...]}` mirrors the convention the author already writes by hand.

### Filter at every traversal hop, not just root

If filtering only applied to the root (the queried doc), a chain like `A --[narration]--> B --[design]--> C` would still pull C into a `--for narration` bundle because the A→B edge survived. That defeats the purpose. Filtering at every hop is what actually shrinks bundles in heavily-cross-linked corpora. ContextDrift's pilot saw 23-file bundles drop to 12, then to 3 once roots were repaired.

### `when: []` is a parse error

`when: []` has two natural readings. "No modes match, never load" (taking `when:` as a constraint). Or "empty constraint equals always" (taking absence as the unconstrained case). Picking one and letting the other silently mean the same thing is a foot-gun. Forbidden. Use a bare string or omit `when:` entirely for "always."

### Free-form mode tags, no enum

Modes are project-defined strings. Swerdlow ships no known-modes list. Cost: typos and case-sensitivity errors. Mitigated by `swerdlow modes` discovery and the unknown-mode warning, which lists the modes actually present in the corpus. Benefit: no "schema bureaucracy" failure mode where the tool dictates a vocabulary that doesn't fit the project.

### Backward compatibility (bare strings still work)

v0.1's bare-string `depends_on: [foo]` syntax is preserved verbatim in v0.2. A v0.1 corpus loads identically. No flag day, no migration script. Typed and untyped entries coexist in the same `depends_on:` list.

### Glob-based include/exclude, no `roots:` concept

Real corpora are messy. Some have 200+ markdown files scattered across root-level `*.md`, `docs/`, and inline `core/.../README.md`. A `roots:` config concept assumes a directory. Glob `include` / `exclude` doesn't. The same config shape works for narrow (`Docs/**/*.md`) and broad (`**/*.md` plus aggressive exclude) corpora.

### Two-phase bootstrap (scan, then user edits, then apply)

`swerdlow bootstrap` writes a plan file. You review and edit it. `bootstrap --apply` writes frontmatter to source files. The plan file is the bridge. Bootstrap's heuristic catches standard markdown links (limited recall). You or an LLM with project context enriches the plan with the prose-only dependencies the heuristic missed. Both steps refuse to overwrite without `--force`. Destructive operations require explicit consent.

### Byte-preserving frontmatter writes (`ruamel.yaml` round-trip)

`apply` uses `ruamel.yaml` in round-trip mode. It preserves comments, key order, quoting style, and flow-vs-block style on existing frontmatter. The first-pass review elevated this from "nice to have" to "v0.1 requirement." If a retrofit tool silently reformats user YAML on every edit, trust evaporates the first time someone sees a noisy git diff.

### Author intent over data-format ceremony

From the kickoff: "Not a doc generator. It indexes existing docs; it doesn't write them." Swerdlow does the minimum mutation needed (writing `depends_on:` into opt-in frontmatter blocks). Everything else stays the author's territory.

---

## Why declared deps, when the LLM can just explore?

Fair question. Both approaches work. Real tradeoffs.

**Declared deps (Swerdlow):** deterministic (same answer every time), free (no LLM round-trips), user-controlled (author intent, not LLM heuristic). Best for corpora the author knows well. Design docs, system specs, runbooks.

**Agent-driven exploration (Continue, Cline 3.7+, Goose):** adaptive, no annotation cost, finds things the author didn't anticipate. Costs many tool-call round-trips per session. Depends on LLM heuristics.

The combination tends to beat either alone. Swerdlow gives the LLM a deterministic starting bundle. The LLM explores from there if the bundle is incomplete. A future Swerdlow may expose itself as an MCP tool so exploring agents call it as step 1.

---

## Roadmap

**Shipped:**

- **v0.1.** Parse frontmatter, build graph, `swerdlow bundle <id>` (later renamed `context`), `swerdlow init`, bootstrap scan + apply, plain-text path output.
- **v0.1.1.** Byte-preservation across line endings (CRLF/LF). Bootstrap proposes empty-deps frontmatter for true orphans in the include set.
- **v0.2.** Typed edges (per-edge `when:` metadata), `--for` mode filter on `context`, filter-at-every-hop, `swerdlow modes` discovery, unknown-mode warning lists corpus modes.

**Planned for v0.3** (evidence-driven; will brainstorm after Phase B live usage):

- **`note:` field on edges.** Captures the editorial rationale ("why is this doc in the bundle?") that's currently lost at the schema layer. Forward-compatible. Swerdlow already ignores unrecognized fields.
- **F2 indirection mechanism.** A primitive for "active-deliverable" routing. `Now.md`'s deps change weekly as the in-flight work shifts. Mode-tags-as-deliverable-IDs is a workaround that doesn't scale. Likely shape: a `follow:` primitive that resolves a state pointer at query time.
- **Doc-org guidance refinement.** This README's "What belongs where" section will sharpen as more pilots happen.

**Speculative for v0.4+:**

- **MCP server.** Expose Swerdlow's `context` and `modes` operations as MCP tools so agent-driven exploration tools (Continue, Cline, Goose, etc.) can call Swerdlow as their first step. The structured-prelude plus LLM-exploration integration.
- **Graph visualization** (`swerdlow graph` to Graphviz / Mermaid output). Useful for inspecting the corpus structure.
- **Reverse lookup** (`swerdlow reverse <code-path>` to find which docs govern this code file). Requires a `touches:` frontmatter convention.
- **`swerdlow check`.** Cycle, orphan, and dead-ref report walking the unfiltered graph for canonical reporting. Distinct from query-time issues.
- **Status-aware bundling.** Skip drafts unless explicitly requested. Respect a project-defined status vocabulary.

**Explicitly not planned:**

- **Inline RAG / embedding layer.** Different problem, different tool. Swerdlow stays declarative.
- **A workflow framework** (proposal, spec, impl, ship). Swerdlow sits underneath whatever convention a project uses. GSD, Spec Kit, and BMAD live in that layer.
- **Per-section dependency declarations.** Big architectural change. Doc-granularity is sufficient for the use cases on the table.
- **Wikilink resolution (`[[brackets]]`).** Out of scope for the v0.x series. Declared frontmatter is the primary mechanism. Bootstrap may eventually detect them as candidates, but they won't be the schema.
- **Sidecar metadata files** (Unity-style `.meta`). Frontmatter lives in the markdown file. Sidecars are too painful to maintain alongside the content.

---

## References

- `docs/kickoff.md`. Original project brief.
- `docs/superpowers/specs/2026-05-14-swerdlow-v0.1-design.md`. v0.1 design (Draft v2, post-review).
- `docs/superpowers/specs/2026-05-14-swerdlow-v0.2-design.md`. v0.2 design (Draft v2).
- `docs/superpowers/plans/`. Implementation plans for v0.1 and v0.2.
- `docs/pilots/2026-05-14-contextdrift-phase-a.md`. First pilot's findings.
- `docs/research/`. Ecosystem research informing positioning.

## Status

v0.2.0. Typed edges and mode scoping shipped. 96 tests passing. Awaiting Phase B live usage before the v0.3 brainstorm.
