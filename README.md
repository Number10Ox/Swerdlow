# Swerdlow

A markdown-to-markdown dependency layer for AI-assisted codebases. Indexes a corpus of markdown documents, builds a dependency graph from declared frontmatter, and answers: **"what files should I load to work on document X?"**

Named after Swerdlow, the journalist/chronicler from Mike Baron and Steve Rude's *Nexus* — the figure who records and tracks events across a system. Apt for a tool that indexes a corpus.

---

## Why this exists

When you have a project with many markdown documents (specs, ADRs, runbooks, glossaries, design notes), three problems compound:

1. **Implicit dependencies.** Every doc assumes context: a glossary, an architecture overview, upstream module specs. Without a declared dependency graph, every reader — human or LLM — has to guess what else to load. The fallback patterns are bad: copy-paste (each doc re-encodes its context) or silent assumption (docs become incomprehensible to outsiders).
2. **Lifecycle blur.** Drafts, accepted specs, superseded specs, frozen audits, and stale plans all share one directory. Nobody knows what's authoritative. LLMs load contradictions and act on them.
3. **No agent-callable graph.** When an AI session is working on feature X, it should be able to ask "which docs govern this work?" and get a minimal correct answer. Today it greps and guesses.

Existing spec-driven dev tools (Spec Kit, BMAD, Kiro, OpenSpec, Tessl, GSD) solve the *workflow* problem — proposal → spec → design → tasks → code. None of them treat the **spec corpus itself** as a first-class graph with declared dependencies. Swerdlow fills that gap.

The origin: a working session on the Project B redacted project surfaced that 100+ docs were cross-referencing each other implicitly. Loading the right context for any given task required tribal knowledge. The bet was that a small generic tool would beat a project-specific workflow hack.

---

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

- **AGENTS.md / CLAUDE.md** for universal always-on context (vision, terminology, conventions). Anthropic and Augment's empirical data converges on a ~150–200 line ceiling for these files — past that, models stop reliably following the content. Progressive disclosure into linked docs is structurally required, and `@import` doesn't help (imports inline at launch, not on demand).
- **Agent-driven exploration** for filling gaps the graph didn't anticipate. The structured prelude + LLM exploration combination is more cost-effective than either alone.

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
$ swerdlow init                       # writes .swerdlow/config.yaml — edit to set globs
$ swerdlow bootstrap                  # scans corpus, writes .swerdlow/bootstrap.plan.yaml
$ ${EDITOR:-vi} .swerdlow/bootstrap.plan.yaml   # review / adjust / enrich
$ swerdlow bootstrap --apply          # writes depends_on: into your markdown files
$ swerdlow context Combat             # prints ordered context bundle for Combat.md
$ swerdlow modes                      # discover modes used in this corpus
$ swerdlow context Combat --for narration  # filter the bundle to narration-mode edges
```

---

## Concepts

- **Indexed doc** — a markdown file matching the `include` glob with a frontmatter block (even empty `---\n---`).
- **`depends_on:`** — frontmatter list of ids the doc needs as context. Each id defaults to filename stem.
- **Bundle / context** — the target doc plus all transitive `depends_on` deps, deepest first.
- **Bootstrap** — scan for existing markdown links, propose `depends_on:` entries, write to a plan file you review before applying.
- **Typed edges** — `depends_on` entries can be bare strings (always relevant) or `{id, when: [mode1, mode2]}` dicts (only relevant for the listed modes). `when: []` is a parse error; use bare string or omit `when:` for "always."
- **Mode filtering** — `swerdlow context X --for narration,plan` walks only the edges whose `when:` includes `narration` or `plan`, plus all always-edges. Filter applies at every traversal hop, so non-matching branches cut their descendants too.
- **Mode discovery** — `swerdlow modes` lists the mode tags present in the corpus with edge and doc counts. Use it to spot typos before they bite.

---

## What belongs where (designing your doc corpus)

A practical division for projects already using AGENTS.md or CLAUDE.md:

| Content kind | Lives in | Why |
|---|---|---|
| Vision, pillars, terminology, banned vocabulary | `CLAUDE.md` / `AGENTS.md` | Universal — every session needs it. Keep under ~200 lines. |
| Authoring rules ("when writing scenes, do X") | Skills or path-scoped rules | Triggered by the work itself, not loaded blindly. |
| Subsystem prerequisites ("to understand X, read Y first") | Swerdlow `depends_on:` | What your `swerdlow context` calls resolve. |
| How the code works | (nowhere) | Code is the source of truth. Doc-redundancy rots. |

The operational test (per published research from Anthropic, ETH Zurich, and Augment): **"What would a new teammate need that they can't infer from the code?"** Content that fails this test doesn't belong in a doc at all.

**Roots-as-leaves heuristic:** in a dep graph, "I need this for context" inverts the editorial hierarchy. Vision docs (e.g., GDD, TDD) sit at the top editorially, but in the dep graph subsystems depend on them — not the other way around. So vision docs should either have `depends_on: []` (be graph leaves) or move to the always-on layer entirely.

**Annotation discipline:** when you have a "Related docs (load when touching that area)" prose table in a design doc, translate the "Load when..." column directly into `when:` tags. The table you already wrote is the design source for your mode taxonomy.

---

## Design decisions (and why)

The load-bearing choices, with rationale. Full design specs in `docs/superpowers/specs/`.

### Declared (frontmatter) over inferred (RAG / NLP)

Author intent is more reliable than inference from prose. The writer of "to work on the combat system, you need the game pillars" knows what the doc needs; an embedding model guesses. Declared deps are deterministic, inspectable in git diffs, cost zero LLM round-trips at query time, and — critically — let the *author* control what context propagates rather than leaving it to runtime heuristics.

RAG is the right answer for "find me docs about X" on a corpus the author doesn't know well. Swerdlow is the right answer for "load the prerequisites to work on Y" on a corpus the author maintains.

### Per-edge typed metadata over doc-level scope tags

The pilot evidence (ContextDrift's "Related docs (load when touching that area)" prose tables) showed that mode-scoping is per-edge in practice. The same doc references doc Y in mode A and doc Z in mode B; doc-level scope would force a single mode tag on all of doc Y's outbound edges. Per-edge `{id, when: [...]}` mirrors the convention the author already writes by hand.

### Filter at every traversal hop, not just root

If we only filtered at the root (the queried doc), a chain like `A --[narration]--> B --[design]--> C` would still pull C into a `--for narration` bundle, because the A→B edge survived. That defeats the purpose. Filtering at every hop is what actually shrinks bundles in heavily-cross-linked corpora — the ContextDrift pilot saw 23-file bundles drop to 12, then to 3 once roots were repaired.

### `when: []` is a parse error

`when: []` has two natural readings: "no modes match, never load" (taking `when:` as a constraint) and "empty constraint = always" (taking absence as the unconstrained case). Picking one and letting the other silently mean the same thing is a foot-gun. Forbidden — use a bare string or omit `when:` entirely for "always."

### Free-form mode tags, no enum

Modes are project-defined strings. Swerdlow ships no known-modes list. Cost: typos and case-sensitivity errors (mitigated by `swerdlow modes` discovery and the unknown-mode warning listing corpus modes). Benefit: no "schema bureaucracy" failure mode where the tool dictates a vocabulary that doesn't fit the project.

### Backward compatibility (bare strings still work)

v0.1's bare-string `depends_on: [foo]` syntax is preserved verbatim in v0.2. A v0.1 corpus loads identically. No flag day, no migration script. Typed and untyped entries coexist in the same `depends_on:` list.

### Glob-based include/exclude, no `roots:` concept

Real corpora are messy. Project B has 194 markdown files scattered across root-level `*.md`, `docs/`, and inline `core/.../README.md`. A `roots:` config concept assumes a directory; glob `include` / `exclude` doesn't. Same config shape works for narrow (`Docs/**/*.md`) and broad (`**/*.md` plus aggressive exclude) corpora.

### Two-phase bootstrap (scan → user edits → apply)

`swerdlow bootstrap` writes a plan file; you review/edit; `bootstrap --apply` writes frontmatter to source files. The plan file is the bridge: bootstrap's heuristic catches markdown links (limited recall), and the user (or an LLM-with-project-context) enriches the plan with the prose-only dependencies the heuristic missed. Both steps refuse to overwrite without `--force` — destructive operations require explicit consent.

### Byte-preserving frontmatter writes (`ruamel.yaml` round-trip)

`apply` uses `ruamel.yaml` in round-trip mode to preserve comments, key order, quoting style, and flow-vs-block style on existing frontmatter. The first-pass review explicitly elevated this from "nice to have" to "v0.1 requirement" — if a retrofit tool silently reformats user YAML on every edit, trust evaporates the first time the user sees a noisy git diff.

### Author intent over data-format ceremony

The kickoff principle: "Not a doc generator. It indexes existing docs; it doesn't write them." Swerdlow does the minimum mutation needed (writing `depends_on:` to opt-in frontmatter blocks); everything else is the author's territory.

---

## Why declared deps vs. just letting the LLM explore?

Both approaches work. Tradeoffs:

- **Declared deps (Swerdlow):** deterministic (same answer every time), free (no LLM round-trips), user-controlled (author intent, not LLM heuristic). Best for corpora the author knows well — design docs, system specs, runbooks.
- **Agent-driven exploration (Continue, Cline 3.7+, Goose):** adaptive, no annotation cost, finds things the author didn't anticipate. Costs many tool-call round-trips per session and depends on LLM heuristics.

The "structured prelude + exploration from there" combination is usually better than either alone: Swerdlow gives the LLM a deterministic starting bundle, and the LLM explores from there if the bundle is incomplete. Future Swerdlow may expose itself as an MCP tool so exploring agents call it as step 1.

---

## Roadmap

**Shipped:**

- **v0.1** — parse frontmatter, build graph, `swerdlow bundle <id>` (later renamed `context`), `swerdlow init`, bootstrap scan + apply, plain-text path output.
- **v0.1.1** — byte-preservation across line endings (CRLF/LF); bootstrap proposes empty-deps frontmatter for true orphans in the include set.
- **v0.2** — typed edges (per-edge `when:` metadata), `--for` mode filter on `context`, filter-at-every-hop, `swerdlow modes` discovery, unknown-mode warning lists corpus modes.

**Planned for v0.3** (evidence-driven; will brainstorm after Phase B live-usage):

- **`note:` field on edges.** Captures the editorial rationale ("why is this doc in the bundle?") that's currently lost at the schema layer. Forward-compatible — Swerdlow already ignores unrecognized fields.
- **F2 indirection mechanism.** A primitive for "active-deliverable" routing — `Now.md`'s deps change weekly as the in-flight work shifts. Mode-tags-as-deliverable-IDs is a workaround that doesn't scale. Likely shape: a `follow:` primitive that resolves a state pointer at query time.
- **Doc-org guidance refinement.** This README's "What belongs where" section will sharpen as more pilots happen.

**Speculative for v0.4+:**

- **MCP server.** Expose Swerdlow's `context`/`modes` operations as MCP tools so agent-driven exploration tools (Continue, Cline, Goose, etc.) can call Swerdlow as their first step. The "structured prelude + LLM-driven exploration" integration.
- **Graph visualization** (`swerdlow graph` → Graphviz / Mermaid output). Useful for inspecting the corpus structure.
- **Reverse lookup** (`swerdlow reverse <code-path>` → which docs govern this code file?). Requires `touches:` frontmatter convention.
- **`swerdlow check`** — cycle / orphan / dead-ref report walking the unfiltered graph for canonical reporting. Distinct from query-time issues.
- **Status-aware bundling** — skip drafts unless explicitly requested; respect a project-defined status vocabulary.

**Explicitly not planned:**

- **Inline RAG / embedding layer.** Different problem; different tool. Swerdlow stays declarative.
- **A workflow framework** (proposal → spec → impl → ship). Swerdlow sits underneath whatever convention a project uses. GSD / Spec Kit / BMAD live in that layer.
- **Per-section dependency declarations.** Big architectural change; doc-granularity is sufficient for the use cases on the table.
- **Wikilink resolution (`[[brackets]]`).** Out of scope for v0.x — declared frontmatter is the primary mechanism. Bootstrap may eventually detect them as candidates, but they won't be the schema.
- **Sidecar metadata files** (Unity-style `.meta`). Frontmatter lives in the markdown file. Sidecars are too painful to maintain alongside the content.

---

## References

- `docs/kickoff.md` — original project brief.
- `docs/superpowers/specs/2026-05-14-swerdlow-v0.1-design.md` — v0.1 design (Draft v2, post-review).
- `docs/superpowers/specs/2026-05-14-swerdlow-v0.2-design.md` — v0.2 design (Draft v2).
- `docs/superpowers/plans/` — implementation plans for v0.1 and v0.2.
- `docs/pilots/2026-05-14-contextdrift-phase-a.md` — first pilot's findings.
- `docs/research/` — ecosystem research informing positioning.

## Status

v0.2.0 — typed edges + mode scoping in production. 96 tests passing. Awaiting ContextDrift Phase B (live consumer wiring) before v0.3 brainstorm.
