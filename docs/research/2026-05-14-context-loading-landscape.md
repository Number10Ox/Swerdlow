# Context-Loading Landscape Research

**Date:** 2026-05-14
**Source:** general-purpose research agent (WebSearch + WebFetch), 51K tokens, 20 tool uses.
**Prompted from:** ContextDrift Phase B pilot session, after user asked "what have other systems done to solve this problem? Swerdlow seems like something that should already exist as part of a larger harness."

This is the verbatim agent output. Sources are linked inline at the bottom.

---

## Is there a standalone Swerdlow-equivalent?

**No exact match found.** Closest neighbors, none of which are a true match:

- **ai-context-builder** (dawichi) — CLI that bundles files into one markdown blob, but uses glob patterns, no `depends_on`, no graph resolution.
- **promptpack** (3rd) — interactive TUI file picker that concatenates selected files; flat, no deps.
- **Cognotik DocProcessor** — does topological sort, but on implicit relations (`specifies`, `documents`, `transforms`), not user-declared `depends_on`, and is bundled with an IntelliJ plugin rather than standalone.
- **Obsidian Dataview** — queries frontmatter across a vault, but it is a query layer (read this metadata into a table), not a doc-to-ordered-context-bundle resolver.
- **LlamaIndex DocumentSummaryIndex** — hierarchical doc index, but auto-derived from summarization, not user-declared deps.

The Swerdlow shape (user-authored `depends_on:` in frontmatter, typed/mode-filtered edges, topological resolution into an ordered file list, standalone CLI) does not appear to exist as a published primitive.

## How major harnesses handle context loading

- **Cursor** — Merkle-tree-indexed embeddings of code chunks; semantic vector search against the query; auto-attaches current file, recent files, linter errors. Hardcoded conventions (`.cursorrules`, `.cursorignore`); explicit `@file` / `@codebase` mentions.
- **Cline** — Hardcoded conventions (`.clinerules/` directory of markdown, every char loaded every request). v3.7+ supports YAML frontmatter with `paths:` conditional — activates rule only when active file matches. No cross-doc dep graph.
- **Continue.dev** — Embeddings + keyword hybrid retrieval over a local index; configurable `nRetrieve` / `nFinal`; `@codebase` provider (now deprecated in favor of agent-mode file exploration tools). Pluggable context providers, including custom RAG via MCP.
- **Aider** — Tree-sitter symbol extraction, personalized PageRank over a symbol-reference graph, dynamic token-budgeted "repo map." Code-graph-driven, not user-declared.
- **Cody (Sourcegraph)** — Hybrid dense+sparse vector retrieval, plus precise code-intelligence "Find References/Definitions" hard links from Sourcegraph's code graph; cross-repo.
- **Plandex** — Tree-sitter "project map" auto-loaded, LLM selects relevant files from the map per step ("smart context window"). Manual `plandex load` for overrides.
- **Goose** — MCP-driven; relies on the agent calling file-read tools rather than a baked-in indexer. Context controlled by `GOOSE_CONTEXT_LIMIT` and auto-compaction.
- **Gemini CLI / Codex / Copilot** — Hardcoded conventions: `GEMINI.md`, `AGENTS.md`, prompt-file slash commands. Gemini supports `@file.md` imports inside `GEMINI.md`.

## Approaches in the field

- **RAG / embeddings** — Cursor, Cody, Continue (classic), custom-RAG-via-MCP. Strength: scales to large unfamiliar codebases. Weakness: opaque, miss-prone, requires indexing infra; recall on small curated doc sets is mediocre.
- **Code-graph / symbol-resolution** — Aider (PageRank over tree-sitter symbols), Cody (LSIF/SCIP refs), Plandex (tree-sitter map). Strength: precise on code. Weakness: language-aware only; doesn't help with prose/design docs.
- **Hardcoded convention files** — `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.clinerules/`, `GEMINI.md`. Always-loaded global instructions. Strength: zero-config, predictable. Weakness: every char eats context every turn; doesn't scale to many systems.
- **Conditional / path-scoped rules** — Cline `paths:` frontmatter, Cursor `.mdc` glob-scoped rules, nested `CLAUDE.md` via directory walking. Strength: scopes load to active file. Weakness: trigger is file-path-based, not task/topic-based.
- **Manual `@` references** — Cursor, Continue, Aider `/add`, Plandex `load`. Strength: surgical. Weakness: user must already know what to load — exactly the problem Swerdlow solves.
- **Declarative user-authored deps in markdown** — Effectively absent as a first-class primitive. Cognotik DocProcessor uses implicit relation types; nobody surfaced does user-authored `depends_on` + typed edges + mode filters.

## Patterns worth knowing

- **`AGENTS.md`** — Open, tool-agnostic standard (agents.md); ~2,500+ repos surveyed by GitHub. Build steps, test commands, conventions, "do/don't" boundaries. Read by Cursor, Aider, Codex, Jules, Zed, RooCode, Kilo, Windsurf, Factory.
- **`CLAUDE.md`** — Claude Code's native file; supports `@import`, hierarchical directory-walking discovery, path-scoped rules. Recommended layering: `AGENTS.md` for shared/cross-tool, `CLAUDE.md` minimal on top.
- **`.cursorrules` / `.cursor/rules/*.mdc`** — Plain-text or MDC files with YAML frontmatter and glob globs; loaded every interaction.
- **`.clinerules/`** — Directory of markdown files, concatenated; YAML `paths:` for path-conditional activation.
- **`GEMINI.md`** — Gemini CLI equivalent; supports `@file.md` imports.
- **Prompt files / slash commands** — VS Code Copilot, Claude Code, Cursor all converging on standalone `.md` (or `.prompt.md`) files with YAML frontmatter declaring `description`, `tools`, `agent`.

## Where the field is moving

Convention files (`AGENTS.md` + tool-specific overlays) are consolidating as the universal "always-on" layer, while in-context retrieval is splitting between (a) embedding/RAG for large unfamiliar codebases and (b) agent-driven tool-call exploration (the path Continue, Goose, and Cline are taking — let the LLM `read_file` what it needs rather than pre-bundling). The declarative-graph slice that Swerdlow occupies — user-authored doc deps with typed/mode-filtered edges, resolved into an ordered list — appears genuinely unoccupied; the closest adjacent work (Cline `paths:` conditionals, Cognotik implicit topological sort, `CLAUDE.md` `@import`) shows the field is groping toward it but hasn't landed a standalone primitive.

## Sources

- [Cursor codebase indexing](https://docs.cursor.com/context/codebase-indexing)
- [Securely indexing large codebases - Cursor](https://cursor.com/blog/secure-codebase-indexing)
- [Cline Rules docs](https://docs.cline.bot/customization/cline-rules)
- [.clinerules folder announcement](https://cline.bot/blog/clinerules-version-controlled-shareable-and-ai-editable-instructions)
- [Aider repo map](https://aider.chat/docs/repomap.html)
- [Building a better repository map with tree sitter - Aider](https://aider.chat/2023/10/22/repomap.html)
- [Continue @Codebase](https://docs.continue.dev/customize/context/codebase)
- [Continue custom code RAG](https://docs.continue.dev/guides/custom-code-rag)
- [How Cody understands your codebase](https://sourcegraph.com/blog/how-cody-understands-your-codebase)
- [Anatomy of an AI coding assistant - Sourcegraph](https://sourcegraph.com/blog/anatomy-of-a-coding-assistant)
- [Plandex context management](https://docs.plandex.ai/core-concepts/context-management/)
- [Goose docs](https://goose-docs.ai/)
- [AGENTS.md spec](https://agents.md/)
- [How to write a great agents.md - GitHub Blog](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [AGENTS.md vs CLAUDE.md - The Prompt Shelf](https://thepromptshelf.dev/blog/agents-md-vs-claude-md/)
- [.cursorrules vs CLAUDE.md vs AGENTS.md](https://thepromptshelf.dev/blog/cursorrules-vs-claude-md/)
- [Gemini CLI GEMINI.md](https://geminicli.com/docs/cli/gemini-md/)
- [ai-context-builder CLI](https://github.com/dawichi/ai-context-builder)
- [promptpack CLI](https://github.com/3rd/promptpack)
- [Cognotik DocProcessor frontmatter schema](https://www.cognotik.com/frontmatter.html)
- [Obsidian Dataview](https://github.com/blacksmithgu/obsidian-dataview)
- [LlamaIndex DocumentSummaryIndex](https://developers.llamaindex.ai/python/examples/index_structs/doc_summary/docsummary/)
