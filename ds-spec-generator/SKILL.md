---
name: ds-spec-generator
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

Read `references/component-spec-template.md` or `references/pattern-spec-template.md` before generating output. The spec must follow that structure exactly.

---

## Process

Run these phases in order. Each phase informs the next.

---

### Phase 1 — Classify the input

Determine:

- **Component or pattern?** A component is a single encapsulated UI element (button, input, tooltip). A pattern is a multi-component composition solving a repeating UX problem (form layout, empty state, search). When genuinely ambiguous, ask.
- **Known library?** If the component is from a well-known library (shadcn, MUI, Radix, Headless UI, etc.), skip Phase 2 extraction and reference the library's own API docs directly. Focus effort on token mapping and team-specific usage rules instead.
- **Conformance target:** Default to Level 2 (Complete) unless the user asks for more. Skip sections that don't fit the component — a simple badge doesn't need §9 Loading or §14 Instrumentation.
- **What inputs are present?** Code only / code + token file / code + Figma link / some combination.
- **What is the component called?** Extract the canonical name from the source. Note any aliases.

If no source code is present, ask the user to provide it before continuing.

---

### Phase 2 — Analyse the source code

Extract facts from the code. Don't infer implementation decisions or make framework-specific recommendations.

**Extract:**
- Component name and any aliases
- Props / API surface: name, type, default value, required flag, what it controls in behavioral terms
- Events emitted: name, when they fire, payload shape
- Slots, children, or render props: name and what they accept
- Internal states the component manages autonomously (toggle, selection, animation)
- States exposed for consumer control via props
- Sub-components used in the composition (anatomy)
- Any hardcoded visual values (colors, spacing, radius, shadows) — flag each one

**Don't carry forward:** framework-specific patterns (hooks, lifecycle methods, directives), internal wiring, build system assumptions.

**Rules:**
- If the code is a prototype (rough, vibe-coded), extract intent — not the exact implementation
- Omit props that are clearly internal implementation artifacts (e.g. `__internalRef`)
- Treat co-located test files and Storybook argTypes as additional signal — argTypes are often more accurate than the component source for documenting the intended API
- If prop purpose is ambiguous, mark it `[needs clarification]`
- If the component targets multiple platforms (React + Web Components + iOS), extract each platform's API separately; the spec's §6 API will have one block per platform

---

### Phase 3 — Resolve design tokens

Never hardcode raw values into the spec. Every visual property must map to a token or be flagged.

**Steps:**
1. Search the codebase for token source files: `tokens.json`, `variables.css`, `theme.ts`, `*.tokens.ts`, `designTokens.*`, or any file exporting a named token object
2. For each hardcoded value found in Phase 2, check if it exists in the token file
3. Map it: `[css-property] → [token.identifier]`
4. If no match: flag as `[no token found — value: X]` and suggest a name following the system's existing convention

**If no token system exists at all:** document raw values as `[no token system — raw value: X]` for every visual property, and add a Phase 6 question recommending token creation before the spec is finalized.

**Token rules:**
- Prefer semantic identifiers (`color.text.primary`) over primitive aliases (`color.gray.900`); if only primitives exist, use those and add a Phase 6 question about creating semantic tokens
- If the user provides a Figma file or token JSON separately, treat it as authoritative over values found in code

---

### Phase 4 — Research industry standards

Search for how established design systems implement the same or equivalent component. **Run all searches in parallel.**

**Research targets:**
1. W3C WAI-ARIA Authoring Practices Guide (APG) — keyboard and ARIA pattern (authoritative)
2. Radix UI primitives — anatomy and API conventions
3. Adobe Spectrum — state and accessibility depth
4. IBM Carbon — anatomy and interaction documentation
5. Shopify Polaris — usage guidelines and content conventions
6. GitHub Primer — API and composability conventions
7. Material Design 3 — state and motion specs

See `references/research-targets.md` for component-class-specific URLs and notes.

**Extract:**
- Keyboard interaction table (APG — treat as authoritative)
- ARIA role and required attributes
- Standard anatomy part names
- Common prop names and types for this component class
- Typical states documented across systems
- Any usage rules that appear in 3+ systems (treat as a de facto standard)

**Convergence rule:** Where multiple systems agree, adopt that as the spec position — don't document alternatives. Where systems diverge significantly, flag it in Phase 6.

**Factual integrity rule:** Only include what was found in research. If a state, behavior, or ARIA attribute wasn't found in the source code or in at least one reputable system's docs, don't include it. Mark gaps as `[TBD]`.

---

### Phase 5 — Write the spec

Load the appropriate template. Fill every section using only what was found in Phases 2–4. Skip sections that genuinely don't apply (note skipped sections with a one-line reason).

**Writing rules:**
- Bullet points for prose. Tables for structured data (API, states, token map, keyboard interactions).
- Short declarative sentences. Subject → verb → object. No qualifiers.
- Present tense: "Emits `onChange`." not "Will emit `onChange`."
- Active voice: "Accepts a `label` prop." not "A `label` prop is accepted."
- No explanatory preamble. Assume the reader knows what design systems are.

**Rationale rule:** Include a "why" only when a `must`/`must-not` guideline has a non-obvious constraint, the spec diverges from an industry standard, or an API decision has an accessibility consequence.

**Token rule:** Never write a raw value. Always use the token identifier. No token yet → `[no token — suggest: token.name]`.

**Gap rule:** Can't fill a section from code or research → write `[TBD]` and generate a question in Phase 6. Never fabricate.

**Section-specific guidance:**
- **Anatomy:** Name every part. Mark required vs. optional. Map tokens per part.
- **Variants:** Only document dimensions that exist in the code or are standard for this component class. Don't invent variants.
- **States:** Cross-reference code states with APG. Use the superset — but only include states with a known trigger and visual change.
- **API:** Describe what each prop controls, not how to implement it. Tighten loose prototype types (e.g. `string` for something that should be an enum) based on research. One block per platform for multi-platform components.
- **Accessibility:** Keyboard table from APG. ARIA attributes from code + research. If contrast pairs can't be computed (tokens unresolved), write `[verify against token values]`.
- **Usage guidelines:** `must`/`must-not` rules only if backed by an accessibility standard or observed failure mode. `should` rules from convergent industry practice.
- **Content:** Only document strings the component itself renders. Don't document strings the consumer provides.

---

### Phase 6 — Generate questions

After the spec, output a clearly separated `## Questions` section.

**Rules:**
- Only ask where the answer would change the spec
- One question per bullet. No multi-part questions.
- Direct and specific: "Does this component support X?" not "Have you considered X?"
- Group by section. Prioritise: accessibility gaps > API ambiguity > missing states > token gaps > content > edge cases
- Maximum 12 questions. Prioritise ruthlessly.

**Always include questions for:**
- Any prop marked `[needs clarification]`
- Any value marked `[no token found]` or `[no token system]`
- Any divergence between source code and the industry standard
- Any APG-required state not found in the source
- Any APG-required ARIA attribute not present in the source

**Format:**
```
## Questions

### Anatomy
- [question]

### API
- [question]

### States
- [question]

### Accessibility
- [question]

### Tokens
- [question]
```

---

## Output

Save the spec to `[component-name]-spec.md` in the working directory (or a path the user specifies), then print the file path. If no filesystem access is available, output inline.

Output order:
1. Completed spec, following the template structure exactly
2. `## Questions` section immediately after

No preamble, no process summary. Spec and questions only.

---

## Reference files

- `references/component-spec-template.md` — Load before generating a component spec
- `references/pattern-spec-template.md` — Load before generating a pattern spec
- `references/research-targets.md` — Load for component-class-specific research URLs and notes
