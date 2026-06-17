---
name: spec-generator
description: >
  Generate a filled-out design system component or pattern spec from source code, design tokens,
  and industry research. Use this skill whenever a user provides a component implementation
  (prototype, vibe-coded, or production source) and wants a spec document — even if they don't
  use the words "spec" or "documentation". Triggers include: "document this component", "write a
  spec for this", "turn this into a spec", "generate handoff docs", "what should the spec look like
  for this", "I need to document this for handoff", "write up the design spec", "what's the
  accessibility spec for this", or any time source code or a Figma URL is provided alongside a
  request for documentation.
---

# Design System Spec Generator

Produces a filled-out component or pattern spec from:
1. Source code (prototype or production) — the primary input
2. Design token source — extracted from code or referenced files
3. Industry standard research — web-searched and synthesized

## How this skill works: model, then render

Do not write prose straight from the source. First **build a component model** —
a structured understanding of the component — then **render** that model into the
spec, adapting the output to the component, its environment, and its reader.

This two-step shape is what keeps the spec coherent. The model is built in Phases
1–4; it is rendered and edited in Phases 5–6.

### The component model

By the end of Phase 4 you hold these facts about the component. Carry them
forward explicitly; every section of the spec renders from them.

- **Nature** — `leaf` (a single encapsulated element with its own interaction
  model: button, input, chip) or `composite` (a molecule that seats children,
  frames a region, or derives state: page, card, drawer). Also: component vs.
  pattern, and whether it's from a known library.
- **Parts** — named anatomy parts, each with its token bindings and a
  **significance flag**: does it carry component-scoped tokens, manage internal
  state, appear conditionally, or have an absence a consumer depends on? Drives
  anatomy depth.
- **Props, classified** — each prop is one of: **consumer** (externally
  settable), **derived/internal** (computed or managed by the component, never
  set by the consumer), or **composition slot** (accepts a named subcomponent).
- **Composition edges** — for each slot, which named component fills it, and
  whether that component has its own spec. Edges are rendered as *references*,
  never as inlined child tables.
- **Resolved values** — token chains walked to concrete values; contrast ratios
  computed; every chain that could not resolve recorded with the token where it
  stopped.
- **Lineage** — the predecessor component this replaces or extends, if any.
- **Environment** — co-located stories and their named exports; whether a token
  file is present; the output target (`.md` or, when stories exist, `.mdx`).

### Three axes the render adapts to

- **Component nature** — leaf vs composite changes anatomy depth and how the API
  is presented.
- **Output environment** — stories present → richer render; token file present →
  resolved values; otherwise graceful plain-markdown fallback.
- **Reader's job** — a spec is a build guide *and* a handoff artifact, so it
  carries a migration delta (when lineage exists) and a testable acceptance
  checklist.

### Two disciplines applied to every section

- **Grounding** — never assert what you didn't verify, never fake completeness.
  Resolve what the inputs allow; for what you genuinely can't, emit a specific
  marker naming where you stopped and raise a question. Placeholders that look
  like finished work are banned when the means to verify exist.
- **Editorial restraint** — render for a reader who scans. Lead with the densest
  format, never restate the same fact across formats, scale depth to the
  component, and push reference material into appendices.

Read `references/component-spec-template.md` or `references/pattern-spec-template.md`
before rendering. The spec must follow that structure.

---

## Process

Run these phases in order. Phases 1–4 build the model; Phases 5–7 render it.

---

### Phase 1 — Frame

Decide the *shape* of the document before extracting detail. Set the three
adaptivity axes and record them as the start of the model.

- **Component or pattern?** A component is a single encapsulated UI element. A
  pattern is a multi-component composition solving a repeating UX problem. When
  genuinely ambiguous, ask.
- **Component nature: `leaf` or `composite`?** Decide this now — it changes
  anatomy depth and API presentation downstream. When unsure, lean on whether
  the component's primary job is its own interaction (leaf) or seating/​framing
  other content (composite).
- **Known library?** If from a well-known library (shadcn, MUI, Radix, Headless
  UI), skip source extraction and reference the library's own API docs. Focus
  effort on token mapping and team-specific usage rules.
- **Environment.** Detect co-located stories with
  `scripts/detect_stories.py <component-path>` — it returns
  `{ detected, storiesFile, exports[] }`, the story export list the render phase
  needs (falls back to `detected: false` when there are none). Also check for a
  token file. Note a predecessor if the user names one or the source hints at one
  (deprecated re-exports, a predecessor import path). These set lineage and
  output target.
- **Conformance target.** Default to Level 2 (Complete) unless asked for more.
  Omit sections that don't fit the component.
- **Name.** Extract the canonical name and any aliases.

If no source code is present, ask for it before continuing.

**Output a short frame summary** — nature, environment findings, predecessor,
and any classification you're unsure of — so the user can correct it before you
invest in extraction. Proceed with your best call if they say to continue.

---

### Phase 2 — Model the source

Build the structured model from the code. Extract facts; don't infer
implementation decisions or make framework-specific recommendations.

**Extract into the model:**
- Component name and aliases.
- **Props, each classified** as consumer / derived-internal / composition slot:
  - *Derived/internal:* computed via conditional logic from two or more other
    props, set by context, described as "internal" in comments, or absent from
    Storybook argTypes.
  - *Composition slot:* typed as a named component, a static attachment
    (`Parent.Child = ChildComponent`), or documented "compose with `<X>`".
  - *Consumer:* everything else the consumer passes.
- **Composition edges:** for each slot, the named child component, and whether a
  co-located spec file exists for it.
- Events: name, when they fire, payload shape.
- Internal vs consumer-controlled states.
- **Parts with significance flags** (see the model definition above).
- Any hardcoded visual values — flag each for grounding in Phase 3.

**Rules:**
- Prototype code → extract intent, not exact implementation.
- Omit internal artifacts (`__internalRef`).
- argTypes and tests are signal — argTypes often describe the intended API better
  than the source.
- Ambiguous prop purpose → mark `[needs clarification]`.
- Multi-platform → extract each platform's API separately.
- **Don't carry forward** framework specifics (hooks, lifecycle, directives),
  internal wiring, build assumptions.

---

### Phase 3 — Ground the values

Resolve everything the inputs allow into concrete, verified values. This is a
gate, not a side effect: the spec must not assert what it hasn't grounded.

**Token resolution:**
1. Find token source files: `tokens.json`, `variables.css`, `theme.ts`,
   `*.tokens.ts`, `designTokens.*`, or any file exporting a named token object.
2. For each hardcoded value from Phase 2, map it to a token:
   `[css-property] → [token.identifier]`.
3. Prefer semantic identifiers over primitive aliases; if only primitives exist,
   use them and queue a Phase 7 question about semantic tokens.
4. No match → flag `[no token found — value: X]` and suggest a name following the
   system's convention. No token system at all → `[no token system — raw value: X]`
   and queue a Phase 7 question.

**Contrast resolution:** for every foreground/background pair, resolve it with
`scripts/resolve_contrast.py --tokens <file> --pair <fg-token> <bg-token>`. The
script walks the `var()` chain (semantic → primitive → value), computes the WCAG
2.1 ratio, and returns pass/fail at each threshold (AA text, AA large, AA UI,
AAA). Record the ratio and ✅/❌ from its output. When it returns
`resolved: false`, it names the token where the chain stopped — render that as
its `[unresolved — chain ends at --token]` marker and queue a Phase 7 blocker
question. Never emit a blanket `[verify against token values]` when a token file
is present. If no token file exists, queue a blocker question per pair.

> The script accepts CSS custom-property files and flat/DTCG JSON token maps,
> and bare token names (`content-primary`, not `--content-primary`). Pass several
> pairs at once by repeating `--pair`.

If the user provides a Figma file or token JSON separately, treat it as
authoritative over values found in code.

---

### Phase 4 — Research industry standards

Search how established design systems implement the same component. **Run all
searches in parallel.**

**Research targets:**
1. W3C WAI-ARIA Authoring Practices Guide (APG) — keyboard and ARIA (authoritative)
2. Radix UI primitives — anatomy and API conventions
3. Adobe Spectrum — state and accessibility depth
4. IBM Carbon — anatomy and interaction documentation
5. Shopify Polaris — usage guidelines and content conventions
6. GitHub Primer — API and composability conventions
7. Material Design 3 — state and motion specs

See `references/research-targets.md` for component-class-specific URLs.

**Extract:** keyboard table (APG, authoritative), ARIA roles/attributes, standard
anatomy part names, common prop names/types, typical states, and any usage rule
appearing in 3+ systems (de facto standard).

**Convergence rule:** where systems agree, adopt that position — don't document
alternatives. Where they diverge significantly, flag it in Phase 7.

**Factual integrity:** only include what was found in the source or in at least
one reputable system's docs. Mark gaps `[TBD]`.

---

### Phase 5 — Render the spec

Load the template. Fill every section from the model, adapting to the three axes.
Omit sections that genuinely don't apply (note them with a one-line reason).

**Adapt to component nature:**
- *Anatomy depth* — leaf: every part. composite: only significant parts; add the
  omission note from the template for the wrappers you drop.
- *API* — render props into the Consumer / Derived & internal / Composition slots
  subsections by their model classification. Omit empty subsections; no prop in
  two subsections.

**Adapt to environment:**
- *Output target* — if stories were detected, render `.mdx`; otherwise `.md`.
  The facts are identical across targets — the environment changes format only.
  See "MDX rendering" below for what `.mdx` adds.
- *Resolved values* — fill contrast and token cells from Phase 3's resolved
  values, including the specific unresolved markers.

**MDX rendering** (only when `detect_stories.py` reported `detected: true`):

- *Preamble.* Begin the file with the addon-docs imports and a Meta tab:
  ```mdx
  import { Meta, Canvas, ArgTypes, Source } from '@storybook/addon-docs/blocks';
  import * as Stories from './ComponentName.stories';

  <Meta of={Stories} name="Design Spec" />
  ```
  `name="Design Spec"` is the convention — it distinguishes this tab from
  doc-generator's "Usage" tab. The import path is relative to the output file.
- *Canvas embeds.* After a variant or state section, embed
  `<Canvas of={Stories.Export} />` when a story export matches. **Matching rule:**
  lowercase both the section heading and each export name, strip spaces and
  punctuation, then test for a substring match (e.g. "With toolbar" → `WithToolbar`,
  "Disabled state" → `Disabled`). Never emit a Canvas for an export not in the
  detected list. No match → omit it.
- *Live prop table.* In the API's Consumer props subsection, prefer
  `<ArgTypes of={Stories.Default} include={[...consumer prop names...]} />` over
  the hand-authored table — it stays in sync with the component. The `include`
  filter keeps it to consumer props only; derived/internal and slots keep their
  hand-authored tables. If argTypes are sparse or absent, emit the hand-authored
  table plus `{/* TODO: add argTypes for a live prop table */}`.
- *Usage snippet.* When a `Default` (or primary) export exists, emit
  `<Source of={Stories.Default} />` in the Imports section as a copy-paste start.
- *Collapsible appendices.* Wrap each appendix in native
  `<details><summary><strong>Appendix — …</strong></summary> … </details>` so
  reference material collapses by default.
- *Token comparison (optional).* When a component has ≥2 layout modes whose token
  values meaningfully differ, emit an inline side-by-side JSX block immediately
  after the table that introduces the modes. All styles use `var(--*)` tokens —
  never raw hex or px.

Every MDX element must degrade: the same content renders as a plain table or
appendix heading in `.md` mode. MDX adds scaffolding, never facts.

**Adapt to reader's job:**
- *What's new* — render the migration-delta block only when lineage exists; omit
  the heading otherwise. Delta items only, never a rehash.
- *Acceptance checklist* — derive binary pass/fail items from the rendered
  content (each variant, state, motion, ARIA attribute, deprecated prop), grouped
  by functional area, design-correctness scope only.

**Render composition edges as references:** each composition slot names the child
and links its spec, or marks `*(stub — spec not yet written)*` — never the
child's prop table, states, or token chain. The parent documents only the
**coupling**, along whichever of these dimensions apply:
- *Downward* — what the parent passes into the slot (layout context, CSS
  variables, container queries) and the constraints it imposes.
- *Upward* — events the child fires that the parent responds to, or state the
  child publishes that drives a structural change in the parent.
- *Structural* — what changes in the parent when the child is present vs. absent
  (e.g. "presence activates the surface frame").

The `*(stub — spec not yet written)*` marker is identical everywhere it appears
so a later audit can grep for undocumented children across all specs. When a
composition boundary has no existing spec, optionally offer to generate a minimal
stub spec for the child (`status: stub`, one-line overview, API marked
`[TBD — spec needed before handoff]`) so the gap doesn't propagate silently.

**Writing mechanics:**
- Tables for structured data; bullets for prose.
- Present tense, active voice, subject → verb → object.
- Token identifiers only — never a raw value. No token yet → `[no token —
  suggest: token.name]`.
- Can't fill from model or research → `[TBD]` + a Phase 7 question. Never
  fabricate.
- Include a "why" only when a `must`/`must-not` has a non-obvious constraint, the
  spec diverges from an industry standard, or an API decision has an
  accessibility consequence.

---

### Phase 6 — Edit

A dedicated pass over the rendered spec. The render writes; this phase cuts. Read
the whole document as a reader who scans, and tighten:

- **No restatement across formats.** If a table carries the fact, delete the
  prose that repeats it. Pre-table prose is at most one sentence, and only when it
  changes how every row is read. Delete summary sentences that describe the table
  above them.
- **Consolidate thin sections.** A short section thematically adjacent to its
  neighbor becomes a subsection under a shared heading rather than its own
  top-level section. Never consolidate the API, and never consolidate a full
  Accessibility section (ARIA + keyboard + focus).
- **Tighten prose.** Active voice, one clause per sentence, cut filler ("in order
  to", "the following table shows", "it is important to note", "this means").
  Questions are single sentences ending in `?`.
- **Demote reference material.** Bulky tables and exhaustive chains move to the
  appendices, linked from where they're referenced.

These are editorial judgements, not arithmetic — apply them where they make the
document faster to read, not mechanically.

---

### Phase 7 — Generate questions

After the spec, output a clearly separated `## Questions` section.

**Rules:**
- Only ask where the answer would change the spec.
- One question per bullet, no multi-part questions, single sentence ending in `?`.
- Group by section. Prioritise: **verification gaps** (unresolved contrast/token
  chains) > accessibility gaps > API ambiguity > missing states > token gaps >
  content > edge cases.
- Maximum 12 questions. Prioritise ruthlessly.

**Always include questions for:**
- Any prop `[needs clarification]`.
- Any `[no token found]`, `[no token system]`, or `[unresolved — chain ends at …]`.
- Any divergence between source and industry standard.
- Any APG-required state or ARIA attribute not found in the source.

**Format:**
```
## Questions

### Accessibility
- [question]

### API
- [question]

### Tokens
- [question]
```

---

## Output

Save the spec to `[component-name]-spec.md` (or `.mdx` when stories were
detected, or a path the user specifies), then print the file path. If no
filesystem access is available, output inline.

Output order:
1. Completed spec, following the template structure exactly
2. `## Questions` section immediately after

No preamble, no process summary. Spec and questions only.

---

## Reference files

- `references/component-spec-template.md` — Load before rendering a component spec
- `references/pattern-spec-template.md` — Load before rendering a pattern spec
- `references/research-targets.md` — Component-class-specific research URLs and notes

## Scripts

- `scripts/detect_stories.py <component-path>` — Frame phase: find co-located
  stories and extract named exports (the `storybookContext`)
- `scripts/resolve_contrast.py --tokens <file> --pair <fg> <bg>` — Ground phase:
  resolve a contrast pair's token chain and compute its WCAG ratio
