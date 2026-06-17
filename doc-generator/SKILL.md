---
name: doc-generator
description: >
  Generate designer-facing usage documentation for a design system component or pattern. Use this skill
  whenever a user wants documentation aimed at product designers — not engineers. Triggers include:
  "write usage docs for this component", "document how designers should use this", "create the design
  guidelines for X", "what should the usage page say", "generate the do and don't section", "write
  the designer docs", "create docs for the design system", "what are the usage guidelines for X",
  "generate designer documentation", "write the Figma / product documentation for this component",
  "create usage guidance", or any request for documentation where the output audience is designers
  rather than developers. This is the sister skill to ds-spec-generator — where the spec answers
  "how do I build this?", this skill answers "how do I use this well in my designs?".
---

# Design System Usage Doc Generator

Produces designer-facing usage documentation for a design system component or pattern. The audience is product designers — people composing screens in Figma or making decisions about which component to use and when.

**This is not a spec.** Do not include:
- API props, events, or code
- Token identifiers or raw values
- ARIA attributes or keyboard interaction tables
- Anatomy details unless they directly explain a behavior or best-practice rationale
- Auto-managed interaction states that require no design decision (hover animation, press feedback, etc.)
- Engineering terminology (intrinsic sizing, leading edge, polymorphic, DOM order, etc.)

Read `references/component-doc-template.md` or `references/pattern-doc-template.md` before generating output. The doc must follow that structure.

---

## Inputs

Accept any combination of:
- Component or pattern name
- A companion spec (from ds-spec-generator) — extract behavioral context only, ignore engineering sections
- Figma component URL or screenshot
- Existing design system documentation to improve or extend
- Research sources or user research the team has run

If no input is provided at all, ask for the component or pattern name and any context about the design system.

---

## Process

Run these phases in order.

---

### Phase 1 — Classify and scope

Determine:

- **Component or pattern?** A component is a single encapsulated element (button, badge, tooltip). A pattern is a multi-component composition solving a recurring UX problem (empty state, form layout, onboarding flow). When ambiguous, ask.
- **Known component class?** If the component maps to a well-known class (button, input, modal, tab, etc.), research directly against established design systems rather than inferring from scratch.
- **What context exists?** Is there a companion spec? A Figma file? Prior docs to improve?
- **Audience nuance:** Is this for a broad product design team, or a specific product vertical (e.g. mobile-only, data-heavy)? Default to broad unless told otherwise.
- **Environment.** If a component path is available, detect co-located stories with `${CLAUDE_SKILL_DIR}/../_shared/scripts/detect_stories.py <component-path>`. It returns `{ detected, storiesFile, exports[] }`. When stories exist, the doc renders as `.mdx` with selective live canvases (see Phase 4); otherwise it stays `.md`. Detection is non-blocking — a failure or absence simply means `.md`.

---

### Phase 2 — Research industry documentation

Search how established design systems document the same component or pattern *for designers*. Focus on the "Usage" or "Guidelines" tab, not the "Code" or "API" tab. **Run all searches in parallel.**

**Research targets (priority order):**
1. **Shopify Polaris** — `polaris.shopify.com/components/[name]` — best content guidelines, real do/don'ts
2. **IBM Carbon** — `carbondesignsystem.com/components/[name]/usage` — thorough usage guidance, rationale depth
3. **Atlassian Design System** — `atlassian.design/components/[name]/usage` — clear decision frameworks
4. **Material Design 3** — `m3.material.io/components/[name]/guidelines` — strong rationale, semantic distinctions
5. **Apple HIG** — `developer.apple.com/design/human-interface-guidelines/[name]` — strong behavioral principles
6. **Adobe Spectrum** — `spectrum.adobe.com/page/[name]` — accessibility guidance for designers
7. **GitHub Primer** — `primer.style/components/[name]` — composability and contextual guidance

See `references/doc-research-targets.md` for component-class-specific URLs and notes.

**Extract from research:**
- When to use and when not to use (with alternatives named)
- Semantic distinctions between variants (what each variant *communicates*, not just what it looks like)
- Common designer mistakes or antipatterns documented across systems
- Rationale behind key guidelines
- Content and copy rules
- Accessibility guidance framed for designers (outcomes, not ARIA code)
- Any guidelines that appear in 3+ systems — treat as de facto standard

**Convergence rule:** Where multiple systems agree, adopt that as the doc position. Where systems diverge significantly, note both and explain the distinction.

**Citation rule:** If a guideline comes directly from a named research source, an accessibility standard, or a specific system, note the source in parentheses. Don't cite for common knowledge.

---

### Phase 3 — Extract from companion spec (if provided)

If a companion spec exists, extract only:
- Behavioral description of each variant (what it *does*, not what tokens it uses)
- States that require a design decision — disabled, error, loading, empty, inactive. Plain language only.
- Component relationships (what this component is used inside, what it contains)
- Any noted misuse patterns or usage constraints from the spec's guidelines section

Do not carry forward: API props, token identifiers, ARIA attributes, code, anatomy tables, or auto-managed interaction states (hover, press, focus ring rendering).

---

### Phase 4 — Write the documentation

Load the appropriate template. Fill every section using what was found in Phases 2–3. Skip sections that genuinely don't apply — note skipped sections with a single sentence explaining why.

**Audience rule — always active:**
A junior product designer is the minimum bar. If a sentence requires knowing how Figma component properties work, what "DOM order" means, or what an engineering prop does, rewrite it or cut it. The test: would a designer one year into their career understand this and know what to do next?

**Writing rules:**
- Use present tense: "Primary buttons signal the single most important action." not "Will signal."
- Active voice throughout. Short, declarative sentences.
- No hedging ("generally", "typically", "in most cases").
- Explain the *why* behind every guideline. A rule without rationale is one designers will ignore.
- No preamble or process summary in the output. Documentation only.
- No section numbering. Use plain heading names.

**Length rule:**
Shorter is better. A designer reading this is looking for a specific answer, not reading a textbook. If a section can be cut without losing guidance a designer would act on, cut it. Prefer one sharp sentence over three cautious ones.

**MDX rendering (only when Phase 1 detection reported `detected: true`):**
A usage doc is designer prose, not a spec — canvases anchor key decisions, they don't catalog every state. Embed *selectively*.

- *Preamble.* Begin with:
  ```mdx
  import { Meta, Canvas } from '@storybook/addon-docs/blocks';
  import * as Stories from './ComponentName.stories';

  <Meta of={Stories} name="Usage" />
  ```
  `name="Usage"` keeps this tab distinct from spec-generator's "Design Spec" tab. The import path is relative to the output file.
- *Lead canvas.* If a `Default` export exists, embed `<Canvas of={Stories.Default} />` immediately after the opening description paragraph, before the first heading — so designers get visual context without scrolling.
- *Variant canvases.* After a named variant subsection where a story export matches (lowercase both, strip spaces/punctuation, substring match), embed one canvas.
- *Never* embed a canvas in when-to-use / don't-use, copy, or accessibility sections — those explain rules, they don't demonstrate a visual state. When in doubt, fewer canvases.
- *Never* emit a canvas for an export not in the detected list. No match → omit.
- Output `.mdx` instead of `.md`. The prose content is unchanged — MDX adds the preamble and canvases only.

**States rule:**
Only document states that require a design decision. Ask: does the designer choose when this state appears, or does it happen automatically? If automatic and invisible to design choices — omit it. Include: disabled, loading, error, empty, inactive. Exclude: hover animation, press feedback, focus ring rendering, transition timing.

**Rationale rule:** Every usage guideline must include a "why" — even if brief. Prefer causal explanations ("because...") over authority-based ones ("per guidelines...").

**Do/Don't rule — CRITICAL:**
- Do/don't examples document **bad patterns a designer could actually produce** when making composition and usage decisions.
- Never write a don't that describes something impossible within the design system constraints.
- A good "don't" describes a real mistake: wrong component choice, bad composition, semantic mismatch, misleading hierarchy.
- Every don't must have a brief rationale. Every do should have one too.
- Prefer specificity: "Don't use a danger button for reversible actions like 'Archive'" beats "Don't overuse danger buttons."

**Anatomy rule:**
No anatomy tables or part-by-part breakdowns. Only name component parts when necessary to explain a behavior or best practice that the designer must act on.

**Accessibility rule:**
Frame accessibility as plain designer responsibilities — layout decisions, labeling, reading order. No ARIA code, no engineering terms. Every responsibility should be actionable by a designer in Figma or in a handoff annotation.

---

### Phase 5 — Ask clarifying questions in chat

After saving the doc, ask any clarifying questions **in chat using the AskUserQuestion tool** — not in the output file. Questions belong in the conversation, not in the documentation the team will publish.

**Rules:**
- Only ask where the answer would meaningfully change the guidance
- Max 3 questions per AskUserQuestion call. Each question must have 3–4 multiple-choice options plus Other.
- Prioritise: missing context about the design system > ambiguous variant semantics > unclear audience > missing research
- If there are more than 3 questions, ask the most impactful ones first and mention there may be follow-ups

**Example question format:**
- Question: "Does your team expose the Inactive button state in Figma?"
- Options: "Yes, it's a component property", "No, designers use Disabled instead", "We handle it differently", "Other"

---

## Output

Save the doc to `[component-name]-usage.md` — or `[component-name]-usage.mdx` when stories were detected in Phase 1 — in the working directory (or a path the user specifies), then print the file path.

The file contains: completed usage doc only. No questions, no process notes, no TBD placeholders. If a section can't be filled without more information, skip it and ask about it in chat.

---

## Reference files

- `references/component-doc-template.md` — Load before generating component documentation
- `references/pattern-doc-template.md` — Load before generating pattern documentation
- `references/doc-research-targets.md` — Load for component-class-specific research URLs and documentation notes

## Scripts

- `${CLAUDE_SKILL_DIR}/../_shared/scripts/detect_stories.py <component-path>` — Phase 1: detect co-located stories and extract named exports, to decide between `.md` and `.mdx` output and which canvases to embed
