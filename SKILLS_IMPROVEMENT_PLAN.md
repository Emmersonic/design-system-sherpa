# Skills Improvement Plan

A comprehensive redesign of `spec-generator` and `doc-generator`, derived from
the 15 open issues — but organized around the problems they reveal, not the
solutions they prescribe. The issues are treated as evidence of what's broken,
not as a spec to implement literally.

## The reframe

The 15 issues collapse into 5 root problems:

| # | Root problem | Evidenced by |
|---|---|---|
| 1 | No model of composition/hierarchy — every component treated as a flat standalone leaf | #40, #42, #45, #46 |
| 2 | Blind to output environment — emits dead static markdown wherever it lands | #37, #38, #39, #48 |
| 3 | Asserts unverified facts — placeholders that look complete but aren't | #43 |
| 4 | Serves authoring, not the reader's job — no support for review sign-off or migration | #41, #44, #49 |
| 5 | Optimizes for coverage, not signal — restated tables, thin sections, verbose prose | #47, #50, #51 |

They share one cause: **the skill renders a document directly from raw
extraction, through a fixed pipeline, into a uniform exhaustive format —
regardless of what the component is, where the doc will live, or who reads it.**

## The architecture: model, then render

Introduce an explicit intermediate **component model**, then render it adaptively.
Today extraction flows straight into prose. Instead, Phases 1–4 build a model;
Phases 5–6 render and edit it.

The model captures, for each component:
- **Parts** with token bindings and a significance flag (carries tokens? manages
  state? conditional? structurally load-bearing?) — drives anatomy depth.
- **Props, classified**: consumer-settable / derived-internal / composition slot.
- **Composition edges**: which props/statics resolve to other named components,
  and whether those have their own spec.
- **Resolved values**: token chains walked to concrete values; contrast computed;
  unresolved chains recorded with *where* they stopped.
- **Lineage**: predecessor component, if this replaces/extends one.
- **Environment**: co-located stories + their exports; token file present?; output
  target (`.md` vs `.mdx`).

Everything renders from this model. That's what makes the result one coherent
system instead of fifteen patches.

### Three axes of adaptivity

The renderer adapts along three axes, which is precisely what the issues are
groping toward:

1. **Adapt to the component's nature** (leaf vs composite/layout; standalone vs
   member of a family). Leaf components get full part-by-part anatomy and a flat
   API. Composite components get selective anatomy (significant parts only),
   split API, and *references* to the components they compose — never inlined
   child tables. → resolves problem 1; absorbs #40, #42, #45, #46.

2. **Adapt to the output environment.** If stories are co-located, render `.mdx`
   with a live preamble, embed canvases against matched exports, prefer
   `<ArgTypes>` over a hand-authored consumer-prop table, and collapse reference
   material into `<details>`. No stories → plain `.md`, identical content. If a
   token file is present, resolve from it. → resolves problem 2; absorbs #37, #38,
   #39, #48.

3. **Adapt to the reader's job.** A spec is a build guide *and* a handoff
   artifact. Render a migration delta when lineage exists, and a derived,
   testable acceptance checklist for sign-off. → resolves problem 4; absorbs #41,
   #44, #49.

### Two disciplines applied across every section

4. **Grounding/verification.** Never assert what wasn't verified, never fake
   completeness. Resolve what the inputs allow (token chains, contrast ratios);
   for what genuinely can't resolve, emit a *specific, actionable* marker naming
   where resolution stopped, and raise it as a question. A blanket
   `[verify against token values]` — a placeholder masquerading as done work —
   is banned whenever the means to verify exist. → resolves problem 3; absorbs
   #43, and generalizes it to every resolvable value, not just contrast.

5. **Editorial restraint.** The model is rendered for a reader who scans. Lead
   with the densest format (table over prose), never restate across formats,
   scale depth to the component, and push reference material below the primary
   read. This is a first-class render phase, not a set of inline rules. →
   resolves problem 5; absorbs #47, #50, #51, and reinforces #40/#48.

## Redesigned pipeline

The current flat pipeline (Classify → Analyse → Tokens → Research → Write →
Questions) has no place to decide the document's shape, no verification gate, and
fuses writing with editing. Replace it with a model-building front half and a
rendering back half:

1. **Frame.** Classify the component's nature, detect the environment (stories,
   token file, predecessor), and from those decide the document's shape and depth.
   This is the old "Classify," widened to set every adaptivity axis up front.
2. **Model.** Extract source into the structured model: parts + significance,
   props classified by kind, composition edges, states. Detect composition
   boundaries here (co-located child files, `Parent.Child` statics, "compose
   with" hints).
3. **Ground.** Resolve token chains to values; compute contrast; record
   unresolved chains with their stopping point. Verification is its own gate, not
   a side effect of token mapping.
4. **Research.** Industry standards, in parallel — unchanged in spirit.
5. **Render.** Fill the template from the model, adapting format to environment
   and depth to component class.
6. **Edit.** A dedicated self-review pass: collapse restatement, consolidate thin
   sections, tighten prose, demote reference material. The renderer writes;
   this phase cuts.
7. **Question.** Surface only what changes the doc, with verification gaps
   (problem 3) prioritized.

Naming the phases by what they *do* — rather than numbering them and bolting on
"Phase 4.5" — keeps the issues' "surface this for confirmation" intent (it lands
in Frame's output and the Question phase) without importing their phase numbers.

## Redesigned template

The current template is a flat list of ~13 equally-weighted numbered sections,
which is the structural cause of problems 1 and 5. Reorganize around **progressive
disclosure** and **the reader's path**, in three tiers:

- **Orient** (always a tight read): what changed since the predecessor (only when
  lineage exists), what it is and when to use it, anatomy at a depth matched to
  the component class.
- **Specify** (the contract): variants, states, design baseline, API split into
  consumer / derived / composition-slots, interactions, accessibility, content.
  Composition slots reference child specs; they never inline them.
- **Verify & relate** (the handoff): acceptance checklist (derived, grouped,
  testable), usage guidelines, related components. Bulky reference material
  (full subcomponent tables, exhaustive token chains) lives here, collapsed when
  the environment supports it.

Section *numbers* become an implementation detail of the template, not a contract
the issues negotiate over. New material (migration delta, acceptance checklist)
is placed where it serves the reader and is omitted entirely when not applicable
— not slotted at a contested integer. Same restructuring principle applies to
`doc-generator`, scoped to its designer audience (it already has a length rule
and a no-anatomy rule; it gains environment adaptivity and the editorial pass).

## Issue coverage check

Every issue is resolved by a principle above, not a dedicated patch:

| Issue | Resolved by |
|---|---|
| #37 stories detection | Frame phase — environment detection (axis 2) |
| #38 spec MDX/Canvas | Render adapts to environment (axis 2) |
| #39 doc MDX/Canvas | Render adapts to environment, doc-scoped (axis 2) |
| #48 ArgTypes/details/token-compare | Render adapts to environment + progressive disclosure (axis 2, tier 3) |
| #40 anatomy depth | Model significance flag + adapt to nature (axis 1) |
| #42 API split | Model prop classification (axis 1) |
| #45 reference child specs | Model composition edges (axis 1) |
| #46 parent documents child impact | Composition edges carry coupling, not internals (axis 1) |
| #43 contrast resolution | Grounding discipline, generalized (discipline 4) |
| #41 migration delta | Lineage in model + adapt to reader (axis 3) |
| #44 acceptance checklist | Adapt to reader's job: handoff (axis 3) |
| #49 grouped checklist | Same, rendered grouped from the model (axis 3) |
| #47 prose/table duplication | Editorial pass (discipline 5) |
| #50 consolidate thin sections | Editorial pass + progressive disclosure (discipline 5) |
| #51 terse prose | Editorial pass (discipline 5) |

## Sequencing

Build the model spine first; the adaptive renders depend on it.

1. **Pipeline + model + template skeleton.** Reframe phases, define the model,
   restructure the template into the three tiers. Everything else renders from
   here. (Foundational; nothing ships meaningfully before it.)
2. **Grounding discipline** (#43 generalized) and **environment detection** (#37).
   Both are self-contained and unblock later work; high correctness value.
3. **Composition-aware render** (#40, #42, #45, #46) and **MDX render** (#38, #39,
   #48) — independent of each other, parallelizable, both depend on 1–2.
4. **Reader-job render** (#41, #44, #49).
5. **Editorial pass** (#47, #50, #51) — last, because it operates on the finished
   output of everything above. Done first, it would need re-tuning after each
   later change.

## Judgement calls made (flag if you disagree)

- **Section numbers are demoted to a template detail.** New sections are placed
  by reader value and omitted when N/A, not negotiated onto a specific integer.
- **Phases are renamed by function**, not extended with fractional numbers. The
  "surface for confirmation" intent lives in the Frame output and Question phase.
- **The grounding fix is generalized beyond contrast** (#43) to every resolvable
  value, since the same placeholder-as-completeness failure applies to token
  chains generally.
- **doc-generator gets the same architecture, audience-scoped** — it shares
  problems 2 and 5, not 1, 3, or 4.
