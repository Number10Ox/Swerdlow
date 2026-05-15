# Swerdlow Pilot Findings (ContextDrift, Phase A)

**Date:** 2026-05-14
**Pilot host:** `~/workspace/ContextDrift`
**Swerdlow version:** v0.1.0 (installed via `uv tool install --from ~/workspace/Swerdlow`)
**Scope:** narrowed Phase A config — `Docs/*.md` + `Docs/Design/*.md` + `Docs/Workflow/*.md`. 31 files indexed after apply. `process/` excluded for round one.

---

## Bugs (for v0.1.x patch)

### B1 [high]: CRLF→LF normalization breaks byte-preservation

**Behavior:** `swerdlow bootstrap --apply` rewrote files that originally used `\r\n` line endings as `\n`, producing whole-file `git diff` output even though the only intended change was prepending a `---\ndepends_on:\n  - foo\n---\n` block. Hits 6 of the 29 files apply touched in this pilot: `Docs/GDD.md`, `Docs/TDD.md`, `Docs/GamePillars.md`, `Docs/Workflow/workflow-design.md`, `Docs/Workflow/workflow-engineering.md`, `Docs/Workflow/testing.md`. Files that were already LF (most of `Docs/Design/`) show clean minimal diffs — confirms the rest of the byte-preserving discipline works.

**Repro:**
```bash
printf '# Test\r\n\r\nBody line.\r\n' > test.md
mkdir -p .swerdlow
cat > .swerdlow/config.yaml <<'EOF'
include: ["test.md"]
exclude: []
EOF
cat > .swerdlow/bootstrap.plan.yaml <<'EOF'
proposals:
- file: test.md
  add_depends_on: [Foo]
issues: []
EOF
swerdlow bootstrap --apply
od -c test.md | head -3
# Expected: \r\n preserved on body lines
# Actual:   \n everywhere
```

**Byte-level evidence on ContextDrift GDD.md before vs after apply (body line 1):**
```
before: ... D o c u m e n t \r \n \r \n
after:  ... D o c u m e n t    \n   \n
```

**Likely fix locus:** `bootstrap/apply.py` `_apply_existing` / `_apply_greenfield` — detect file's line-ending convention on read (first `\n` preceded by `\r` or not), preserve on write. `ruamel.yaml` round-trip alone doesn't enforce this because the prepend / splice is in the calling code, not in the YAML serializer.

**Severity rationale:** the spec §6.3 promises *"`git diff` after `--apply` shows only the lines that actually changed."* This bug breaks that contract — the trust principle the spec was explicitly built on. ContextDrift reverted these 6 files post-pilot and is waiting on a v0.1.1 fix before re-applying.

---

### B2 [medium]: Bootstrap skips files with zero outbound links

**Behavior:** `swerdlow bootstrap` emits a `Proposal` only for files with at least one outbound markdown link. Files with zero outbound links get no plan entry, get no frontmatter from `--apply`, and therefore are NOT in the indexed corpus. When enrichment lists such a file as a dep target, the loader reports `missing_ref: depends_on '<id>' has no indexed target` and drops the edge.

**Hit on this pilot:** `Docs/Design/AgentVoiceContract-Psalm.md` and `Docs/Design/ShowcaseScript.md` — both authority docs that other docs depend on, neither has any outbound `[label](X.md)` links of its own. Bootstrap silently omitted them. The pilot's enrichment naively listed them as deps; first `context` run produced `missing_ref` issues.

**Repro:**
```bash
# In any test corpus:
mkdir leaf-test && cd leaf-test
echo "# Leaf — has no outbound links" > leaf.md
echo "# Hub" > hub.md
echo "See [leaf](leaf.md)." >> hub.md  # leaf gets a proposal via hub's link
# But:
echo "# Orphan-but-authoritative — no outbound, no inbound either" > orphan.md
swerdlow init
swerdlow bootstrap
cat .swerdlow/bootstrap.plan.yaml
# orphan.md NOT in proposals. leaf.md IS (because hub linked to it).
```

**Workaround used in pilot:** manually `Edit` an empty `---\ndepends_on: []\n---\n` block into the two leaf files before re-running `context`. Two files, ~30 seconds. Real fix should be in bootstrap.

**Suggested fix:** in `bootstrap/scan.py`, emit a `Proposal { file, add_depends_on: [] }` for *every* file matching the include globs (even ones with no outbound links). Idempotency still holds — re-running against an applied corpus produces zero new proposals for files that already have frontmatter. Cost is a longer plan file; benefit is the indexed corpus matches the configured corpus after `--apply`.

---

### B3 [medium, possibly intentional]: Link-as-index treated as link-as-dependency

**Behavior:** bootstrap proposes every outbound markdown link as a `depends_on:` candidate, with no signal about whether the link is an index entry or a true dependency.

**Hit on this pilot:** `Docs/GDD.md` contains a "System Design Docs" table:

> *"Detailed specs for each system area. Load the relevant doc when working on that system. **Note:** These docs are being replaced by per-system living docs..."*

…linking to 8 design docs (CoreMechanic, MissionMechanics, CampaignMechanics, CityMap, NarrativeDesign, CampaignNarrative, PlayerExperience, SceneAuthoring). Bootstrap proposed all 8 as `add_depends_on` for GDD. But those docs are *downstream* of GDD — they depend on GDD, not the other way around. Treating them as GDD's deps inverts the graph and causes upstream nodes to fan into the entire downstream subtree on any traversal.

**Enrichment had to strip 8 of 10 bootstrap-proposed deps from GDD** to get a sensible graph.

**Probably "by design" for v0.1.** Bootstrap can't tell index from dep without semantics, and explicit user review of the plan file is the spec's named mechanism. But the friction is real: GDD's plan section is mostly noise that enrichment deletes. Some heuristic options if v0.2 wants to reduce the review burden:
- Links inside a markdown table cell or under a heading like "Index" / "Related docs" / "System docs" are usually index-style.
- Links in the first 10% of a doc are more likely to be index entries than deps.
- A doc that introduces 5+ links in a single table is almost certainly an index.

None of these are bulletproof; the right answer might just be "document the gotcha so reviewers know to look for it."

---

## Design findings (for v0.2 brainstorm)

### F1 [load-bearing]: Bundle ballooning

**Empirical bundle sizes from `swerdlow context <doc>` on the pilot corpus (31 indexed files):**

| Target | Bundle size | "Sensible" size (judged after the fact) | Bloat |
|---|---:|---:|---:|
| `GamePillars` (leaf) | 1 | 1 | — |
| `NarrativeDesign` | 23 | ~7-8 | 3x |
| `MissionGameplay` | 23 | ~10 | 2.3x |
| `Now` (session entry) | 24 | ~5-8 | 3-4x |

**The 23-file bundle for NarrativeDesign includes:** FinalRoomClimax, InteriorAssets, CCTVSignalGame, MissionScriptSystem, MiniActions, AgentLayer, MissionGeneration, CityMap, CampaignMechanics, and more. None of those are needed for a narration-quality session. They arrive via chains like `NarrativeDesign → MissionGameplay → CCTVSignalGame → InteriorAssets`.

**Root cause:** every edge is `depends_on: <id>` with no qualifier. In a graph where most non-leaf nodes have 5-10 outbound edges (and ContextDrift's design docs are heavily cross-linked because every system touches every other system), two-hop transitive closure covers nearly every node.

**Evidence for "sensible size" target:** NarrativeDesign.md's own "Related docs (load when touching that area)" table — written by the human author, before Swerdlow existed — lists exactly 3 related docs (MissionGameplay, MissionIntelModel, SceneAuthoring). Adding the per-agent voice exemplar (AgentVoiceContract-Psalm), the writing-standards origin (GamePillars), and one cross-reference partner (CampaignNarrative) gets you to ~7. The bundle returns 23.

**Candidate v0.2 mechanisms (each has tradeoffs):**

- **Typed edges:** `depends_on: [{id: X, kind: "always"}, {id: Y, kind: "load-for-narration"}]`. Direct expression of mode-specific loading.
- **Scope tags at the doc level:** `loads_for: [narration, plan]`. Edges inherit the doc's scope. `context` query takes a mode argument and filters.
- **Bundle depth limit:** `swerdlow context X --depth=1`. Crude; loses transitive benefits.
- **Per-section deps:** GDD § 2 needs CityMap; § 7 needs MissionGameplay. Big architectural change but matches how big design docs actually work.
- **Reverse-aware bundling:** distinguish "depends_on" (this doc needs X to be readable) from "informs" (X benefits from being read alongside this doc). The fan-out problem is mostly "informs" being collapsed into "depends_on."

**My (pilot's) read:** typed edges + mode tags is the closest fit. ContextDrift's design docs already encode this in prose ("Load when..." columns — see F6). Schema is just making the existing convention machine-readable.

---

### F2 [load-bearing]: Now.md is the highest-value entry but its deps rot weekly

**The setup:** ContextDrift's `SessionStart` hook auto-injects `Now.md` into every Claude Code session. Now.md is *the* doc whose `depends_on:` would do the most work — it's the doc the user sees first, and the user's stated pain ("when I start sessions, critical context is missing") is exactly an under-loading problem at session start.

**The problem:** Now.md's *actual* dependencies are "whatever the active deliverable references." On 2026-05-14, that's DEL-046 (mission template surgery) → MissionGameplay + MissionGeneration. Last week it was DEL-045 (writer-agent) → NarrativeDesign + the writer-agent spec. Next week it'll be DEL-047 (first golden instance) → MissionScriptSystem + Clinique Weir kernel docs.

Static frontmatter on Now.md means weekly hand-editing of `depends_on:` to track the active deliverable. That's exactly the bookkeeping ContextDrift wants Swerdlow to remove.

**Bundle data:** `swerdlow context Now` returns 24 / 31 indexed files — basically the whole corpus. Surfacing all 24 via SessionStart would *inflate* context usage, not reduce it. The current SessionStart auto-load (CLAUDE.md + MEMORY.md + Now.md + mode workflow doc) is ~4 files. Swerdlow's bundle is 6x.

**Candidate v0.2 mechanisms:**

- **Indirection:** Let Now.md `depends_on: [<active-deliverable-spec>]` where the spec lives in `process/` (the spec carries the real deps). Requires `process/` to be in scope (see F5).
- **A `--follow-active` mode** that reads Now.md's body for a marker (e.g., "Active deliverable: DEL-046") and routes through the named target.
- **Accept that "what to load for the current session" is a different question** than "what's the static dep graph." Maybe v0.2's `context` command grows a `--for <task-or-mode>` flag, and "session start" is one such mode.

This finding connects to F3 (mode-specific bundles) — they're the same underlying issue, surfaced from different angles.

---

### F3: Same target, two work types, different right answer

**Concrete case from this pilot:**

- A `/narration` session on `NarrativeDesign.md` wants: MissionGameplay (where narration fits in beat cycle), MissionIntelModel (wrongness vs intel), SceneAuthoring (pre-authored data), AgentVoiceContract-Psalm (voice exemplar), GamePillars (writing standards), CampaignNarrative (REQ-NR-002 cross-ref). ~7 files.
- A `/plan` session on the same doc wants: heavier on plan template, acceptance criteria, the deliverable spec in `process/`; lighter on per-agent voice contracts. Different ~7 files.

v0.1's `context NarrativeDesign` produces *one* answer for both. There's no way for the consumer to ask "for narration work" vs "for planning work."

**Strongest argument for typed edges / mode tags.** Without a mode-aware primitive, the bundle is the same regardless of task, which means the bundle has to be a union (loading more for every task) or has to be wrong for at least one task.

---

### F5: Excluding `process/` missed real value

**Pilot config excluded `process/**`.** Reasoning at scoping time: 81 files in `process/`, many archival or in-flight, would create noise. Right call for round one.

**But ContextDrift's `CLAUDE.md` and `MEMORY.md` explicitly name `process/` as a context-loading target:**
> "Per-deliverable specs: `process/spec-*.md` — read when working on the in-flight deliverable named in Now.md."

Active design happens in `process/spec-*.md` (canonical specs), `process/plan-*.md` (implementation plans), `process/instance-*.md` (per-content design docs). Excluding them means the dependency graph stops at the design layer and never reaches the work-actually-being-done layer.

**The bootstrap output already showed this:** 4 of the 12 `issues:` entries were `target outside indexed corpus` errors for `process/spec-*.md` references in `Docs/Design/MissionGameplay.md`, `MissionIntelModel.md`, and `NarrativeSystemArchitecture.md`. The design docs *want* to depend on the specs; the config wouldn't let them.

**Suggested round two:** include `process/spec-*.md` and `process/plan-*.md` with careful exclusion of drafts (`process/draft-*.md`, `process/del-*-task-*-*.md`) and run logs (`process/m6-phase3/**`, `process/content-expansion/**`). Glob config will get awkward — the right answer might be a config primitive like `include_subset:` that takes named subsets ("active-specs", "all-plans") rather than just globs.

**This also reinforces F1:** including `process/` will *increase* graph density, which makes bundle ballooning worse, which makes a scoping primitive even more necessary.

---

### F6: The "Load when..." prose columns are already typed-edge data

**Evidence — copied from `Docs/Design/NarrativeDesign.md` directly:**

```markdown
### Related docs (load when touching that area)

| Doc | What it defines | Load when... |
|---|---|---|
| [MissionGameplay.md](MissionGameplay.md) | Beat reactions (A/B choice → agent reaction messages), narrator tiers | Checking how narration fits in the beat cycle |
| [MissionIntelModel.md](MissionIntelModel.md) | Wrongness field (narrator input) vs intel (handler input) | Ensuring narrator uses wrongness, not intel |
| [SceneAuthoring.md](SceneAuthoring.md) | What gets pre-authored for narrator | What data the narrator receives per room |
```

**Four pilot docs have a "Related docs (load when touching that area)" table:** `NarrativeDesign.md`, `MissionGameplay.md` (9-row version), `CoreMechanic.md`, `CampaignNarrative.md`. Each row encodes:

1. **Which doc** (the edge target — same as `depends_on:`)
2. **What it defines** (semantic role — possibly a clue to edge type)
3. **Load when...** (the trigger condition — exactly mode/task scoping)

**This is the user's own answer to typed-edge design**, written in prose form before Swerdlow existed. The v0.2 brainstorm should treat these tables as the requirements document for the schema. If the schema can be derived directly from "Load when..." column conventions, the schema is right.

---

## What worked

- **Install:** `uv tool install --from ~/workspace/Swerdlow swerdlow` — zero friction. Tool resolved, built, installed in ~1s.
- **`swerdlow init`:** clean, refused-to-overwrite behavior worked as spec'd.
- **`swerdlow bootstrap` scan:** found 27 of 29 indexable files. Heuristic caught explicit markdown links via `mistune` parser. No false positives from code-block content. Issues block was useful — surfaced 12 real broken / out-of-corpus references in the existing docs, which is value beyond what the pilot scope asked for.
- **`swerdlow bootstrap --apply`:** for files that were already LF, byte-preserving worked perfectly. The frontmatter prepend is clean, minimal, idempotent.
- **`swerdlow context`:** loud-but-nonfatal issue reporting on stderr worked as designed. 42 `cycle_detected` events on `context NarrativeDesign` — all handled gracefully, paths still shipped. Cycle handling is correct for this corpus.
- **Plan-file enrichment as bridge for prose-style refs:** the workflow design is right. Bootstrap caught ~10% of true deps (the explicit links); enrichment caught the other 90%. Without the plan file as a hand-edit step, this couldn't have worked on ContextDrift.

---

## Hard data

### File counts

- **Total `.md` in ContextDrift repo:** 1,473 (most are `output/report-mock-*.md` run artifacts).
- **Matched by pilot include glob:** 45 (before exclusion).
- **Indexed after exclusion + apply:** 31.
- **Bootstrap proposed:** 22 files with at least one dep + 7 files with empty deps = 29 plan entries. **2 leaf files (Psalm, Showcase) were silently omitted** — see B2.

### Bundle sizes (full output)

```bash
$ swerdlow context GamePillars 2>/dev/null | wc -l
1

$ swerdlow context NarrativeDesign 2>/dev/null | wc -l
23

$ swerdlow context MissionGameplay 2>/dev/null | wc -l
23

$ swerdlow context Now 2>/dev/null | wc -l
24
```

### Stderr issue counts

- `swerdlow context NarrativeDesign`: 0 missing_ref (after manual B2 workaround), 42 cycle_detected, 0 parse_error, 0 duplicate_id.
- All cycles were expected (GDD↔TDD, MissionGameplay↔NarrativeDesign↔CampaignNarrative triangle, etc.).

### Commits / diffs to inspect

- **ContextDrift pilot artifact:** `~/workspace/ContextDrift/.swerdlow/bootstrap.plan.yaml` (the applied plan).
- **ContextDrift pilot notes (full version, more discursive):** `~/workspace/ContextDrift/process/swerdlow-pilot-notes.md`.
- **CRLF damage evidence (now reverted in ContextDrift):** see B1 byte-level od output above. Reverted via `git checkout HEAD -- <6 files>` post-pilot per Swerdlow session direction.
- **Currently-applied frontmatter** in ContextDrift: 25 files in `Docs/{,Design/,Workflow/}*.md` have `depends_on:` frontmatter from this pilot. Will re-apply the 6 CRLF-reverted files after v0.1.1 ships.

---

## Phase A close

Phase A is complete. F1 (bundle ballooning) is decisive — further v0.1 testing on wider globs or more targets would confirm the same finding in more places. The v0.2 brainstorm has enough signal to start from F1, F2, F3, F6 (the typed-edges / mode-scoping cluster) and F5 (process/ inclusion + glob config primitives).

Phase B (wire one consumer path to prove value-prop) is blocked until v0.2 ships at least one bundle-scoping mechanism — surfacing v0.1's 24-file bundles via SessionStart would inflate context, not reduce it.
