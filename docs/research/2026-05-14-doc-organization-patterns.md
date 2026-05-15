# Doc Organization Patterns Research

**Date:** 2026-05-14
**Source:** general-purpose research agent (WebSearch + WebFetch), ~50K tokens, 13 tool uses.
**Prompted from:** ContextDrift Phase B pilot session, after the user clarified that the prior research (`2026-05-14-context-loading-landscape.md`) targeted the tool landscape but missed the doc-organization question they were actually asking: where do projects put always-load content vs per-task content, and what patterns have emerged.

This is the verbatim agent output. Sources at the bottom.

---

## Content patterns in AGENTS.md / CLAUDE.md

Across observed repos and influential guides, the dominant pattern is a thin "operational entrypoint" — not a knowledge dump. Anthropic's official memory doc says explicitly: keep CLAUDE.md to "build commands, conventions, project layout, 'always do X' rules" and move multi-step procedures or subsystem-specific content into skills or path-scoped `.claude/rules/` files.

The [agents.md](https://agents.md/) spec lists the canonical sections: **project overview, build/test commands, code style, testing instructions, security considerations, commit/PR guidelines**. Augment's research-backed guide adds two patterns that empirically improve agent behavior: **decision tables** for ambiguous choices and **paired don't/do statements** with concrete alternatives, plus 3–10 line snippets from *actual production code* (not invented examples).

What's notably *absent* from observed files: architecture overviews (ETH Zurich research found they don't help agents locate files) and long taxonomies. Concrete example: [duyet/monorepo CLAUDE.md](https://github.com/duyet/monorepo/blob/master/CLAUDE.md) is ~25 lines total; the rest lives in `docs/ai/internal-knowledge.md` referenced via a plain markdown link.

## How shared concepts are handled

The clearly winning pattern is **separate doc, pointer from root** — not inline, not @import. HumanLayer's influential guide recommends "Progressive Disclosure": split into `code_conventions.md`, `service_architecture.md`, `database_schema.md`, etc., with brief descriptions in CLAUDE.md pointing the agent at them. Anthropic's `.claude/rules/` mechanism is the structured version of this — topic files load with the same priority as CLAUDE.md, optionally scoped by glob path so they only fire when matching files are touched.

`@import` exists but is explicitly **not** a context-saver: Anthropic docs state "imported files still load and enter the context window at launch." The Bijit Ghosh guide reinforces this: "Imports do not reduce context usage — imported content is expanded inline." So `@import` is for *organization*, not loading economy. For genuine load-economy on shared concepts, path-scoped rules or skills are the only real lever.

Inline glossaries in CLAUDE.md are rare in observed repos. Augment specifically warns against this, noting orphan reference docs hit <10% discovery rates but inline taxonomies eat the same context every session.

## Typical file sizes / scope

Anthropic's official target: **under 200 lines**. HumanLayer cites their own root file as "less than sixty lines" and recommends under 300. Augment's research found "100–150 line AGENTS.md files with a handful of focused reference documents were the top performers" with 10–15% improvements; gains *reversed* beyond that length. [agents.md](https://agents.md/) itself offers no size guidance.

The instruction-budget framing (Medium guide by Bijit Ghosh): frontier models reliably follow ~150–200 distinct instructions; Claude Code's own system prompt consumes ~50, leaving ~100–150 effective slots before drop-off begins.

## "Always-load vs subsystem" split — documented conventions

The cleanest published heuristic is Anthropic's own: belongs in CLAUDE.md only if it's "facts Claude should hold in every session." Multi-step procedures → **skills** (load on invocation). Subsystem rules → **`.claude/rules/*.md` with `paths:` frontmatter** (load only when matching files are read). Augment phrases it as: "non-inferable details, counterintuitive patterns, and custom tooling constraints deliver the highest signal" — anything an agent will discover from one session of reading the code should *not* be in the always-on file. ETH Zurich's research backs this: instructions that just describe what's already visible in code don't improve task success and increase costs 19–20%.

## Hierarchical / nested patterns

Two distinct mechanisms, often conflated:

1. **Ancestor walk** (CLAUDE.md). At launch, Claude Code reads every CLAUDE.md from filesystem root down to CWD, concatenating them in root-to-CWD order — nothing is "overridden," it's just appended later. Files in *subdirectories below* CWD load lazily when Claude reads files in those dirs.
2. **Nested package files**. The OpenAI repo reportedly ships 88 AGENTS.md files across subprojects. The monorepo example pattern: root holds global TS/lint/git conventions; per-package files hold package-specific commands and validation libraries (Prisma, Zod). Packages without their own file simply inherit the root.

Important caveat from Augment's research: nested READMEs in subdirectories had only 40% discovery rates. The mechanism works in Claude Code because it's automatic-on-file-read, not because agents browse for nested docs.

## Patterns worth adopting

1. **The 200-line ceiling is a real constraint, not a soft suggestion** — Augment's data shows performance *reversing* past ~150 lines. If your always-on doc is >300 lines, you're paying context for material agents follow less reliably.
2. **Path-scoped `.claude/rules/*.md` is the right home for subsystem terminology/taxonomies** — it's the only mechanism that actually reduces session load (skills aside). `@import` does not. Inline does not.
3. **Shared concepts (glossaries, banned vocab, taxonomies) belong in topic files referenced from CLAUDE.md, not inline** — inline pays the cost every session for content used in some sessions. The HumanLayer pattern (`code_conventions.md` etc.) with a one-line pointer in CLAUDE.md is the converged community answer.
4. **"What would a new teammate need that they can't infer from the code?" is the operational filter** — Anthropic's docs, ETH Zurich's research, and Augment's empirical data converge on this. Anything inferable from one session of reading the codebase is net-negative in an always-on file.

## Sources

- [Anthropic Claude Code memory docs](https://code.claude.com/docs/en/memory)
- [agents.md spec](https://agents.md/)
- [HumanLayer — Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Augment — How to write good AGENTS.md](https://www.augmentcode.com/blog/how-to-write-good-agents-dot-md-files)
- [InfoQ — ETH Zurich research on AGENTS.md value](https://www.infoq.com/news/2026/03/agents-context-file-value-review/)
- [Bijit Ghosh — Complete Guide to CLAUDE.md](https://medium.com/@bijit211987/the-complete-guide-to-claude-md-memory-rules-loading-and-cross-tool-compression-97cc12ed037b)
- [Builder.io — Improve AI code output with AGENTS.md](https://www.builder.io/blog/agents-md)
- [Monorepo example — claude-md-monorepo.md](https://github.com/MuhammadUsmanGM/claude-code-best-practices/blob/main/examples/claude-md-monorepo.md)
- [duyet/monorepo CLAUDE.md (real-world example)](https://github.com/duyet/monorepo/blob/master/CLAUDE.md)
