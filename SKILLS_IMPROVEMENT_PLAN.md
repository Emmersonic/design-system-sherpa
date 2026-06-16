# Skills Improvement Plan

Plan to address the 15 open issues against `spec-generator` and `doc-generator`.
Derived from reading every open issue plus both `SKILL.md` files and
`spec-generator/references/component-spec-template.md`.

## Issue landscape

| Cluster | Issues | Skill(s) |
|---|---|---|
| A — Storybook / MDX awareness | #37, #38, #39, #48 | spec + doc |
| B — API & composition modeling | #40, #42, #45, #46 | spec |
| C — New sections & correctness | #41, #43, #44, #49 | spec |
| D — Prose & structure quality pass | #47, #50, #51 | spec |

13 of 15 issues touch `spec-generator`. #37 and #39 touch `doc-generator`.

## Two cross-cutting decisions to make first

These block clean execution of the clusters. Resolve them before writing any
skill changes, because nearly every issue depends on them.

### 1. Lock the canonical section numbering

The issues reference conflicting section numbers, and two of them add new
sections. Today the template is:

`§0 Metadata · §1 Overview · §2 Anatomy · §3 Variants · §4 States · §5 Design
Specs · §6 API · §7 Imports · §8 Interactions · §9 Accessibility · §10 Content ·
§11 Usage Guidelines · §12 Related`

Proposed canonical order after all issues land:

`§0 What's new (migration delta, conditional — #41) · §1 Metadata · §2 Overview
· §3 Anatomy · §4 Variants · §5 States · §6 Design Specs · §7 API · §8 Imports ·
§9 Interactions · §10 Accessibility · §11 Content · §12 Acceptance checklist
(#44/#49) · §13 Usage Guidelines · §14 Related`

Open question for the user: keep "What's new" as a renumbering-causing `§0`, or
make it an un-numbered lead block so the rest of the template keeps its current
numbers? Recommendation: un-numbered lead block titled **"What's new"** so we do
not renumber the whole template (and break every cross-reference in existing
specs) just to satisfy one conditional section. Same for Acceptance checklist —
place it by name, not by fighting over a number.

### 2. Add a "Plan & confirm" phase to spec-generator

#40, #42, and #50 all require the skill to "surface a decision to the user in
the Phase 3 plan for confirmation." `spec-generator` has no such phase — it goes
straight from Research (Phase 4) to Write (Phase 5). 

Proposal: insert **Phase 4.5 — Plan & confirm** (between Research and Write) that
emits a short plan: component class, detected composition slots, proposed section
consolidation, and any derived-vs-consumer prop classifications — then waits for
confirmation or proceeds with defaults if the user says "just go." This single
addition unblocks the "surface for confirmation" acceptance criteria across the
whole B cluster.

Also add a **`componentClass` output (`leaf` | `composite`) to Phase 1** (#40).
This signal is consumed by #40, #42, #45, and #46, so it belongs in Phase 1 once.

## Workstreams, in recommended execution order

### Workstream 1 — Storybook detection foundation (#37)

Prerequisite for #38, #39, #48. Smallest, highest-leverage change.

- Add a **Storybook detection step** to both skills: scan the component dir for
  `[Name].stories.{tsx,ts,js,jsx}`, regex out named exports, produce a
  `storybookContext { detected, storiesFile, exports[] }` object.
- Non-blocking: parse failure or no file ⇒ `{ detected: false }` ⇒ `.md` fallback.
- Land this alone first; it has no user-visible output change on its own.

### Workstream 2 — MDX output (#38, #39, #48)

Depends on WS1. Do spec and doc in parallel after detection exists.

- **#38 (spec):** when `detected`, emit `.mdx` with `Meta name="Design Spec"`
  preamble; inject `<Canvas of={Stories.X}>` after variant/state sections whose
  normalized heading substring-matches an export. Never emit a Canvas for an
  unknown export. Fallback to `.md`.
- **#39 (doc):** same idea, `name="Usage"`, but **selective** canvases (lead
  canvas + per-variant only; none in when-to-use / copy / a11y prose). Output
  `.mdx`.
- **#48 (spec, advanced):** after #38, add `<ArgTypes>` for §7.1 consumer props,
  `<details>` collapsible appendices, JSX token-comparison blocks (tokens only,
  no raw values), `<Source>` usage snippets. Must degrade gracefully in `.md`.
  Note: #48 depends on the API split (#42) for the "consumer props only" filter,
  so sequence #42 before #48's ArgTypes piece.

### Workstream 3 — API & composition modeling (#40, #42, #45, #46)

Tightly coupled; shares detection logic and the `componentClass` signal. Build
the detection once, then the three consumers.

1. **Detection (Phase 2 + Phase 1):** classify `componentClass`; detect
   composition boundaries (co-located `Child.tsx`, `Parent.Child = X` statics,
   "compose with `<X>`" doc hints); flag derived props (computed from ≥2 props,
   set by context, absent from argTypes). Surface all of this in the new Phase 4.5.
2. **#42 — split §API** into `7.1 Consumer props`, `7.2 Derived & internal`,
   `7.3 Composition slots` (omit empty subsections; no prop in two places).
3. **#45 — reference child specs** instead of inlining: each composition slot
   emits a reference/stub line, never the child's prop table.
4. **#46 — parent documents child *impact* only**: coupling summary
   (down/up/structural) + grep-able `*(stub — spec not yet written)*` marker.
5. **#40 — anatomy depth by class**: leaf ⇒ full part table (unchanged);
   composite ⇒ selective anatomy + omission note; slots reference child spec.

These four should land as one sequenced PR series since they edit the same
template sections and Phase 2 detection block. #42 → #45 → #46 → #40 order.

### Workstream 4 — New sections & correctness (#41, #43, #44, #49)

Mostly independent of WS3; can run in parallel.

- **#43 (bug, do early):** resolve contrast pairs from the token file in Phase 3
  — walk the `var()` chain to hex, compute WCAG ratio, fill ✅/❌. Replace the
  blanket `[verify against token values]` with `[unresolved — chain ends at X]`
  + a Phase 6 blocker question. Highest correctness value; ship first in this WS.
- **#44:** add the Acceptance checklist section, items *derived* from spec
  content (variants/states/motion/ARIA/deprecated props), binary pass/fail,
  design-correctness scope only.
- **#49:** group that checklist by functional area (Layout / Header / Motion /
  Accessibility / Composition / Content / Other); omit empty groups. Depends on
  #44 — same PR or immediately after.
- **#41:** conditional "What's new" lead block when a predecessor is detected
  (deprecated re-exports, predecessor import path, or user states it). Add the
  "what does this replace?" question to the new Phase 4.5 plan/interview.

### Workstream 5 — Prose & structure quality pass (#47, #50, #51)

All three rewrite Phase 5 writing rules and add a Phase 5 self-review. Do them
together to avoid three conflicting edits to the same phase.

- **#47:** lead with tables, no prose that restates a table; ≤1 sentence
  pre-table prose.
- **#50:** consolidate thin (≤15-line) adjacent sections under `##` parent +
  `###` subsections; never consolidate API or a full Accessibility section.
- **#51:** terse sentence style — active voice, ≤20 words, ban "in order to",
  "the following table", "it is important", "this means"; one-sentence questions.
- Implement as a single **Phase 5 self-review checklist** the skill runs before
  emitting, since #47/#50/#51 are all "scan output, then fix" passes.

## Recommended sequencing

```
Milestone 0 (decisions):  section numbering + Phase 4.5 + componentClass signal
Milestone 1:              #37 (detection)              → #43 (contrast bug)
Milestone 2:              #38, #39 (MDX)               #42→#45→#46→#40 (composition)
Milestone 3:              #48 (MDX interactive)        #44→#49 (checklist), #41 (what's new)
Milestone 4:              #47+#50+#51 (Phase 5 quality pass) — last, touches final output
```

Rationale: detection and the contrast bug are foundational/standalone. The
composition series and the new-sections series are independent and parallelizable.
The prose/structure pass goes last because it operates on the *finished* output
of everything else — doing it first would mean re-tuning it after each later
change.

## Risks & notes

- **Renumbering blast radius.** Any spec already generated by the skill encodes
  section numbers. Prefer named/un-numbered sections for the two additions to
  avoid breaking existing cross-references. Confirm with the user.
- **#44 references a `ds-impl-spec` skill** "that already produces this section."
  That skill is not in this repo — only `spec-generator`/`doc-generator` exist.
  Treat #44 as porting the pattern into `spec-generator`, not reusing code.
- **Phase-number drift.** Issues cite phase numbers (`Phase 2 interview`,
  `Phase 3 plan`) that don't match the current spec-generator phases. The new
  Phase 4.5 reconciles most of these; each issue's "Phase N" references should be
  re-mapped to the actual phases during implementation, not copied literally.
- **MDX graceful degradation** is an acceptance criterion in #38/#39/#48 — every
  interactive element needs a tested `.md` fallback path.
```
