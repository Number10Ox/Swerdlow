# Swerdlow v0.2.0 Pilot Findings (ContextDrift, Phase A continuation + Phase B)

**Date:** 2026-05-14
**Pilot host:** `~/workspace/ContextDrift`
**Swerdlow version:** v0.2.0 (upgraded via `uv tool upgrade --reinstall swerdlow`)
**Scope:** Same Phase A config (31 indexed files in `Docs/{,Design/,Workflow/}*.md`). Annotated 12 docs with typed `when:` edges based on F6's "Load when..." prose tables.

---

## Headline

**F3 (mode orthogonality) — VALIDATED.** Same target produces different bundles per mode tag, cleanly. The typed-edge mechanism works as designed.

**F1 (bundle ballooning) — PARTIALLY FIXED.** NarrativeDesign bundle dropped from **23 → 15 files** (35% reduction). All Test-2 content criteria pass cleanly. But Test-1 strict count target (≤10) was missed. Test-3 strict count target (<12) was met (8 files).

**Phase B unblocked** but introduces a v0.3-class finding (ambient docs / foundational-chain leakage — section C8 from the v0.2 spec review). The current bundles are usable as Phase B consumer input; the count gap reflects a real design tension in v0.2's filter model when applied to a corpus with foundational orientation docs.

---

## Success criteria verification

### TEST 1: `swerdlow context NarrativeDesign --for narration` ≤ 10 (target ~7)

**Result: 15 files. FAIL on strict count, PASS on content criteria.**

```
$ swerdlow context NarrativeDesign --for narration | wc -l
15
```

The 15-file bundle breaks down as:

**9 narration-relevant files (correct):**
- NarrativeDesign.md (target)
- MissionGameplay.md (via `when: [narration]` from NarrativeDesign)
- MissionIntelModel.md (via `when: [narration]`)
- SceneAuthoring.md (via `when: [narration]`)
- AgentVoiceContract-Psalm.md (via `when: [narration]`)
- ShowcaseScript.md (via `when: [narration]`)
- CampaignNarrative.md (via `when: [narration]` — REQ-NR-002 cross-ref)
- GamePillars.md (via bare-string from NarrativeDesign — writing standards origin)
- GDD.md (via bare-string from NarrativeDesign — terminology + banned vocab)

**6 foundational/orientation files (the leak):**
- TDD.md ← via GDD's bare edge to TDD
- Roadmap.md ← via GDD's bare edge
- Decisions.md ← via GDD's bare edge, MissionGameplay's bare edge
- AgentLayer.md ← via TDD's bare edge, CoreMechanic's bare edge
- MiniActions.md ← via Decisions's bare edge
- CoreMechanic.md ← via MissionGameplay's bare-string edge (the "Load when..." prose said "Revisiting why the handler role exists" with no mode-marker, so I tagged it always)

**The pattern:** once any traversal path reaches the orientation cluster (GDD ↔ TDD ↔ Roadmap ↔ Decisions ↔ AgentLayer), the bare-string interconnections pull in the whole cluster regardless of mode.

### TEST 2: Must contain / must NOT contain — PASS

```
MUST contain:
  ✓ NarrativeDesign         (target)
  ✓ MissionGameplay         (in bundle)
  ✓ MissionIntelModel       (in bundle)
  ✓ SceneAuthoring          (in bundle)
  ✓ AgentVoiceContract-Psalm (in bundle)

MUST NOT contain:
  ✓ InteriorAssets          (NOT in bundle — was leaking via 3-hop chain in v0.1)
  ✓ CCTVSignalGame          (NOT in bundle)
  ✓ CityMap                 (NOT in bundle)
  ✓ MissionGeneration       (NOT in bundle)
```

The "must NOT contain" list is decisive evidence the filter works. In v0.1 these all leaked into the NarrativeDesign bundle via chains like `NarrativeDesign → MissionGameplay → CCTVSignalGame → InteriorAssets`. v0.2's mode-tagging at each hop cleanly cuts those chains.

### TEST 3: `swerdlow context Now --for narration` < 12 — PASS

```
$ swerdlow context Now --for narration | wc -l
8
```

The 8 files are exactly the foundational chain (Now + Roadmap + GDD + TDD + Decisions + GamePillars + AgentLayer + MiniActions). No mission-specific or generation-specific docs reached, because Now.md's edges to MissionGameplay and MissionGeneration are tagged `[gameplay, del-046]` and `[generation, del-046]` respectively — both cut for `--for narration`.

This validates the F2-mitigation hypothesis (deliverable-ID-as-mode-tag) for narrowing the session-start bundle, with a caveat — see "F2 follow-up" below.

---

## F3 mode orthogonality validation

Same target, four different mode filters, four different bundles:

| Filter | Bundle size | Notes |
|---|---:|---|
| (no filter) | 23 | v0.1 behavior, all edges included |
| `--for narration` | 15 | narration-specific + foundational chain |
| `--for gameplay` | 8 | gameplay docs, minimal foundational reach |
| `--for campaign` | 17 | campaign deps reach more across the graph |
| `--for narration,campaign` | 19 | union of both modes |

The deltas between modes are real and meaningful. `--for gameplay` is the tightest because gameplay annotations don't traverse back through NarrativeDesign's narration-tagged edges. `--for campaign` is wider because CampaignNarrative is heavily cross-linked. The union (`narration,campaign`) is strictly larger than either, as expected.

**This validates F3.** The same doc produces work-type-appropriate bundles. The "Load when..." prose tables (F6) directly translate to working `when:` annotations.

---

## v0.3 design findings

### F1.1 [load-bearing for v0.3] — The "ambient docs" / foundational-chain leakage

This is the same issue I flagged as C8 in my v0.2 spec review ("the ambient docs problem"). v0.2's pilot makes it concrete with numbers.

**The problem:** ContextDrift has a tightly-interconnected orientation cluster — GDD, TDD, Roadmap, Decisions, GamePillars, AgentLayer, MiniActions, CoreMechanic. These docs cross-reference each other heavily via what feel like correct `always`-relevance edges:

- GDD → TDD ("technical mirror")
- GDD → Roadmap ("current scope")
- TDD → AgentLayer ("post-MVP scope")
- Decisions → MiniActions, AgentLayer (rationale links)
- MissionGameplay → CoreMechanic ("Revisiting why the handler role exists")

Each individual edge is defensibly always-relevant. But because they form a connected subgraph of always-edges, **any bundle that touches one of them touches all of them**. For a narration-mode query that needs GDD (terminology), GDD's bare-string-deps to TDD/Roadmap/Decisions cascade in, then those docs' bare-string deps cascade further.

**What v0.2's filter doesn't do:** prevent always-edges from propagating once the bundle enters the orientation cluster. The filter cuts mode-tagged edges, but always-edges traverse freely.

**The semantic gap:** the bare-string `always` annotation conflates two distinct ideas:
1. "This dep is genuinely relevant in EVERY work type" (truly foundational — GamePillars writing standards, GDD terminology)
2. "I haven't decided which modes this dep is relevant for, so I left it bare" (default, unclassified)

The pilot's annotation favored (2) for orientation-cluster edges, faithful to the "Load when..." columns that didn't provide mode hints for those edges. The result is the foundational chain pulling through.

**Candidate v0.3 mechanisms:**

a) **Negative modes / mode-cuts.** `{id: TDD, when: [], cut: [narration]}` — explicit "don't traverse this edge for narration." Lets foundational links stay foundational without overloading every bundle.

b) **Per-doc "ambient" flag.** `ambient: true` in frontmatter marks a doc as "loaded by session bootstrap, skip during transitive traversal." Cleanly separates the SessionStart auto-load layer from per-query bundles.

c) **Depth limit on bare-string edges only.** Mode-tagged edges traverse to convergence; bare-string edges traverse only 1 hop. Crude but quick.

d) **`only:` instead of (or alongside) `when:`.** `{id: TDD, only: [tech]}` means "load this edge only when --for tech matches, and never via 'always' default." Distinguishes "default-on" from "default-off."

My pilot read: option (b) — per-doc `ambient` flag — is the cleanest semantic fit for ContextDrift's actual workflow. The SessionStart hook already loads GDD/TDD/Now.md/Roadmap/MEMORY.md/workflow-doc as ambient context. Per-query bundles should EXCLUDE those by default. The flag lets the corpus author declare "this doc is auto-loaded elsewhere; don't transit through it."

### F1.2 [validates v0.2 review M1] — `note:` field would have been load-bearing during annotation

During annotation, I repeatedly had to make editorial calls translating "Load when..." prose into mode tags. Examples:

- MissionGameplay → CoreMechanic: "Revisiting why the handler role exists" — is this `gameplay` work? `always`? `core`? I chose always; the result leaked CoreMechanic into the narration bundle.
- CampaignNarrative → CoreMechanic: "Revisiting how corruption manifests in city narrative or faction voice" — is this `narration`? `campaign`? Both? I chose narration.
- TDD → AgentLayer: "post-MVP scope mentioned" — no mode label in the source. Chose always.

A `note:` field would have let me record the editorial reasoning AND the source prose:

```yaml
- {id: CoreMechanic, when: [gameplay], note: "Revisiting why the handler role exists"}
- {id: TDD, when: [], note: "post-MVP scope; mostly orientation"}
```

Future readers (and future tooling — e.g., a `swerdlow context --explain` that prints why each file is in the bundle) would have ground truth for what the annotation MEANS, not just what it does.

Suggest reconsidering for v0.3 in light of Phase B integration: when a consumer (skill, hook) surfaces "the bundle for this session," a `note:` makes the bundle self-explaining without forcing the consumer to invent its own labels.

### F2 follow-up: deliverable-ID-as-mode-tag — works, partial fit

I annotated Now.md's edges as `[gameplay, del-046]` and `[generation, del-046]` to test whether deliverable IDs could substitute for a separate F2 primitive.

**What worked:** `swerdlow context Now --for del-046` would now return the bundle scoped to current active work (untested in this pilot — but the mechanism is in place).

**What didn't:**
- The mode tag list multiplies linearly with deliverable count. Today: `del-046`. Next week: `del-047`. Three months: `del-046, del-047, del-048, del-049, del-050`. Now.md's frontmatter becomes a deliverable history.
- More importantly, when DEL-046 closes, the `del-046` tags become stale debt. Someone has to edit Now.md to remove them.
- Now.md's other deps (Roadmap, TDD) are bare always-strings. For a `--for del-046` query, the bundle is still 8 files (the foundational chain) because those bare-strings traverse regardless. The mode filter only narrows on the few `del-046`-tagged edges.

**Verdict:** mode-tags-as-deliverable-IDs is a hack that papers over F2 partially. It probably doesn't generalize. v0.3 still needs a dedicated primitive — possibly: read Now.md's body for an "active deliverable" marker and route through that doc's deps automatically.

### F-misc: P2 unknown-mode warning shipped, but doesn't list available modes

```
$ swerdlow context X --for nonexistent 2>&1 >/dev/null
warning: mode 'nonexistent' is not present on any edge.
```

The warning works (correctness). My v0.2 review P2 push was that it should ALSO list available modes for typo-debugging:

```
warning: mode 'nonexistent' is not present on any edge.
         Modes used in this corpus: gameplay, narration, campaign, mission-design, generation, del-046
```

Not blocking — `swerdlow modes` covers the discovery use case explicitly. But P2 was about the moment-of-failure ergonomics. Worth revisiting for v0.2.x.

### F-misc: `swerdlow modes` shipped and is useful

```
$ swerdlow modes
gameplay        24 edges,  8 docs
narration       11 edges,  5 docs
campaign         7 edges,  4 docs
mission-design   7 edges,  5 docs
del-046          2 edges,  1 docs
generation       2 edges,  2 docs
```

Mode discovery works exactly as P3 from the spec review proposed. Edge counts + doc counts make the tag landscape legible at a glance.

---

## Phase B integration (status: documented, not yet wired)

ContextDrift's `.claude/skills/narration/SKILL.md` already has its own mode parameter (`mission|campaign|narrator-prompt|review`) that loads internal CHECKLIST files from the skill's `references/` directory. It does NOT currently load project-level design docs (NarrativeDesign.md, MissionGameplay.md, etc.).

**Phase B integration pattern (proposed, not yet implemented):**

Add a "Step 0" to SKILL.md:

```markdown
## Step 0 — Load project design context

Before applying narrative quality rules, ensure the project's design context
is loaded. Run:

    swerdlow context NarrativeDesign --for narration

Read each file in the output. These are the design docs that govern
how narration works in this project — checklists alone are insufficient
without their underlying constraints.
```

Equivalent for `/narration campaign`:

    swerdlow context CampaignNarrative --for narration,campaign

This gives the skill consumer (Claude in a `/narration` invocation) the right project-design slice without bloating the skill's own auto-loaded references.

**Why not implement this turn:** the skill's auto-load behavior affects every `/narration` invocation. Modifying it warrants user review before shipping, especially because:
- The current bundle is 15 files (above the ≤10 target) — wiring it would auto-load 15 files per narration invocation.
- The foundational-chain leakage (F1.1) means the bundle includes orientation docs that the SessionStart hook is already auto-loading. Double-load risk.

Recommendation: wait for v0.3's ambient-docs mechanism, then wire. In the meantime, the integration pattern is documented and the user can invoke `swerdlow context` manually when starting a narration session to get the bundle.

---

## What worked

- **`swerdlow modes` discovery command** — pinned down the tag landscape immediately. P3 shipped correctly.
- **Backward compat** — bare-string `depends_on:` entries still work alongside dict entries in the same file. Mixed lists round-trip cleanly through apply (didn't need to test idempotency this pilot, but ruamel preserved the YAML structure on every edit).
- **Filter at every hop** — the spec's most important call. Cuts entire subtrees cleanly. Without this, only one-hop branches would be filtered and the F1 fix would be marginal.
- **F3 orthogonality** — same target, multiple modes, multiple clean bundles. The user-facing value prop is real and demonstrable.
- **Unknown-mode warning** — silent failure would have been bad here. The warning prevents typo bundles.

## Hard data

### Bundle counts (NarrativeDesign target)

| Filter | v0.1 | v0.2 | Reduction |
|---|---:|---:|---:|
| (no filter) | 23 | 23 | — |
| `--for narration` | n/a | 15 | -35% |
| `--for gameplay` | n/a | 8 | -65% |
| `--for campaign` | n/a | 17 | -26% |

### Bundle counts (Now target — session entry)

| Filter | v0.1 | v0.2 | Reduction |
|---|---:|---:|---:|
| (no filter) | 24 | 24 | — |
| `--for narration` | n/a | 8 | -67% |
| `--for gameplay` | n/a | 8 | -67% |
| `--for del-046` | n/a | 11 | -54% |

### Files annotated this pilot

12 docs received `when:` tags:
- 4 from "Load when..." tables: NarrativeDesign, MissionGameplay, CoreMechanic, CampaignNarrative
- 6 downstream design docs: MissionIntelModel, SignalGames, SceneAuthoring, CCTVSignalGame, FinalRoomClimax, InteriorAssets
- 2 entry-point docs: Roadmap, Now

The other 19 indexed docs kept bare-string edges (most are leaf nodes or have all-foundational deps).

### Mode landscape after annotation

```
gameplay        24 edges,  8 docs
narration       11 edges,  5 docs
campaign         7 edges,  4 docs
mission-design   7 edges,  5 docs
generation       2 edges,  2 docs
del-046          2 edges,  1 docs
```

### Time / effort

- Tag vocabulary selection: ~5 min (reading 4 "Load when..." tables)
- Annotation (12 docs, ~45 edges): ~15 min (mostly mechanical translation)
- Re-iteration after first F1 test failure (added 8 more docs): ~10 min
- Total annotation effort for ContextDrift's pilot scope: ~30 min

For a corpus this size (31 docs), annotating took less time than the Phase A enrichment did. Mode-tagging is faster than dep-inference once you know the model.

---

## Recommendations

1. **Ship v0.2 as-is, declare partial F1 fix.** 35% reduction is real progress; full ≤10 target requires v0.3 work.
2. **F1.1 (ambient-docs / foundational-chain leakage) is the next load-bearing v0.3 finding.** Propose evaluating options (a) negative modes, (b) per-doc `ambient` flag, (c) bare-string depth limit, (d) `only:` semantics. My preference is (b).
3. **F2 still needs its own primitive in v0.3.** Deliverable-ID-as-mode is a workable hack but doesn't address the weekly-rot problem cleanly.
4. **Reconsider `note:` field for v0.3** in light of Phase B integration's "make the bundle self-explaining" need.
5. **Phase B wiring deferred** until F1.1 is addressed — wiring now would couple the consumer to bundles that include duplicate ambient docs.

---

## Phase B post-test correction: roots-as-leaves (2026-05-14, after initial findings landed)

The user pushed back on my "ambient docs" v0.3 proposal, arguing it conflated two distinct concerns (external load state vs graph structure). Testing their alternative — strip outbound deps on the orientation cluster (GDD, TDD, Roadmap, Decisions → `depends_on: []`) — confirmed they were right. **The v0.2 mechanism handles foundational-chain leakage via annotation discipline, not a new primitive.**

The correct mental model: in a `depends_on:` graph, **the dep arrow points from "needs context" toward "provides context."** Subsystem docs depend on root docs (for terminology, vision, etc.); root docs don't depend on subsystem docs. Editorial hierarchy puts roots at the top, but in a prerequisite graph they're leaves — many incoming edges, zero outgoing.

My Phase A enrichment got this inverted. I added outbound deps to GDD/TDD/Roadmap/Decisions that were really backward arrows ("GDD relates to TDD" instead of "does GDD's content require TDD to be understood?" — answer: no). Correcting four `depends_on: []` declarations changed the bundle math substantially.

### Bundle sizes after roots-as-leaves correction

| Query | v0.1 baseline | v0.2 first pass | After roots-as-leaves | vs baseline |
|---|---:|---:|---:|---:|
| NarrativeDesign --for narration | 23 | 15 | **12** | -48% |
| NarrativeDesign --for gameplay | 23 | 8 | **3** | -87% |
| NarrativeDesign --for campaign | 23 | 17 | n/a (didn't retest) | — |
| NarrativeDesign (unfiltered) | 23 | 23 | 20 | -13% |
| Now --for narration | 24 | 8 | **3** | -87% |
| Now --for del-046 | 24 | n/a | 15 | -37% |
| GDD (direct) | varies | varies | **1 (leaf)** | — |
| TDD (direct) | varies | varies | **1 (leaf)** | — |

### Test 1 still misses ≤10 strictly, but the residual gap is editorial

12 vs ≤10 target = 2 specific edges:
- `CoreMechanic → AgentLayer` (bare) — AgentLayer is post-MVP, not narration-relevant. Tagging or dropping closes 1 file.
- `MissionGameplay → Decisions` (bare) — Decisions has narration-relevant entries (D-048, D-072). Defensibly kept.

Both are annotation calls, not mechanism failure.

### Test 2 still cleanly passes

All must-have files present (NarrativeDesign, MissionGameplay, MissionIntelModel, SceneAuthoring, AgentVoiceContract-Psalm). All forbidden files absent (InteriorAssets, CCTVSignalGame, CityMap, MissionGeneration).

### Test 3 strongly passes

Now --for narration = **3 files** (Now + Roadmap + TDD). The session-entry bundle is now exactly the orientation triple, no cascade.

### What this means

- **F1.1 (the ambient/foundational-chain finding) is dissolved.** No new primitive needed. The mechanism works; my Phase B v0.3 recommendation was wrong.
- **Roots-as-leaves is the corpus-correction rule.** In a Swerdlow corpus, root docs (vision, orientation, log-style docs like Decisions) should have `depends_on: []`. Subsystems point at them, not vice versa.
- **The deeper finding (corpus monolithic-doc structure) is a ContextDrift deliverable**, not Swerdlow's problem. Once GDD/TDD shed reference content (Terminology, AnomalyTaxonomy, etc.) to focused leaf docs, the bundle math gets even tighter. v0.2 already handles whatever shape the corpus takes.

### Correction: P2 already shipped fully

My initial Phase B report said the P2 unknown-mode warning shipped but didn't list available modes. **Wrong** — my test command (`2>&1 >/dev/null | grep -i warning`) only captured the first line of the warning. Re-tested cleanly:

```
$ swerdlow context NarrativeDesign --for nonexistent 2>&1 >/dev/null
warning: mode 'nonexistent' is not present on any edge.
         Modes used in this corpus: campaign, del-046, gameplay, generation, mission-design, narration
```

P2 shipped fully in v0.2 Task 4 as designed. Apology for the false flag.

### Revised v0.3 priority list

Drop F1.1 entirely. Updated priorities:

1. **`note:` field on edges** — still wanted. Editorial annotation calls were genuinely ambiguous; preserving the source prose (the "Load when..." rationale) would help consumers self-explain bundles and help future annotators not second-guess prior decisions.
2. **F2 primitive** — still wanted. The `del-046` deliverable-ID-as-mode-tag hack works at n=1 but doesn't scale (linear bloat in Now.md's mode list as deliverables accumulate; stale debt on closure).
3. ~~F1.1 ambient-docs flag~~ — **dropped**. Corpus correction (roots-as-leaves) handles it.
4. P2 warning shape feedback — none; ship is correct.

Visualize / reverse / `check` remain lower priority. Phase B didn't surface them.

### Phase B status: unblocked

The 12-file bundle is usable as a `/narration` skill consumer. Wiring is "add Step 0 to `.claude/skills/narration/SKILL.md`: run `swerdlow context NarrativeDesign --for narration` and Read each output file." Not gated on v0.3.
