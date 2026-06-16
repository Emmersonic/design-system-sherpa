# Component Spec — Template

> **Purpose**
> This template defines what a complete engineering spec for a design system component should contain. It is the render target for the `spec-generator` skill: the skill builds a component *model* (see `SKILL.md`), then fills this structure from it. Fill each section by answering the prompts for your specific component. Not every section applies to every component — omit sections that genuinely don't fit, but treat states, token mapping, and accessibility as required.

> **How this spec is organized — read in three tiers**
> The spec is grouped into three tiers, in reading order. A reader rarely needs all three at once.
>
> - **Orient** — what this is, when to reach for it, what it's made of. The quick read.
> - **Specify** — the contract: variants, states, design values, API, behavior, accessibility, content. The build reference.
> - **Verify & relate** — handoff: acceptance checklist, usage guidelines, neighbors. The sign-off and migration material.
>
> Bulky reference material (full subcomponent tables, exhaustive token chains, story galleries) belongs in **collapsible appendices** at the end — it should not add weight to the linear read. In a Storybook MDX render these use native `<details>`; in plain markdown they use a clearly labeled "Appendix" heading.

> **Section depth scales to the component.** A *leaf* component (button, input, chip — a single encapsulated element with its own interaction model) gets a full part-by-part anatomy and a flat API. A *composite/layout* component (page, card, drawer — a molecule that seats children or derives state) gets a selective anatomy (only structurally significant parts) and an API split by who controls each value. The skill sets this class in its Frame phase; this template adapts accordingly where noted.

> **Conformance tiers**
> - **Level 1 — Core:** Metadata + Overview + Anatomy
> - **Level 2 — Complete:** + Variants + States + Design Specifications + API + Accessibility
> - **Level 3 — Gold:** All sections, with evidence-backed guidelines and per-platform coverage

---
---

# Tier 1 — Orient

*What this component is, when to use it, and what it's made of. The quick read.*

---

## Metadata

_DSDS: `metadata` — status, since, lastUpdated, aliases, category, tags, links_

> **Prompts**
> - What is this component's lifecycle status on each platform it targets? Is any platform ahead or behind the others?
> - When was this component introduced, and when was its documentation last meaningfully changed?
> - What other names does this component go by — across teams, legacy codebases, other platforms, or external conventions?
> - How is this component categorized within the system's taxonomy?
> - Where do the canonical artifacts live? Link to: source code, Storybook, Figma component, and the token definition file.
> - If deprecated: what should consumers use instead, and what's the migration path?

```
Name:
Identifier (kebab-case):
Category:
Status:
  overall:      draft | experimental | stable | deprecated
  web:
  ios:
  android:
  figma:
Since version:
Last updated:
Aliases:
Links:
  source:
  design:
  storybook:
  documentation:
```

---

## What's new

_Conditional — include only when this component replaces or extends a predecessor. Omit the heading entirely otherwise._

_DSDS: `useCases` + `links` (kind: `alternative`) — the migration delta_

> **Purpose**
> When a component is an explicit replacement or evolution of an existing one, the highest-value content for an engineer is *what changed*. This section is the delta — not a rehash of current behavior.

> **Prompts**
> - What does this component replace or extend?
> - For each difference: is it a new, removed, renamed, or changed feature? One sentence each.
> - For renamed props, what are both the old and new names?
> - For removed features, what is the deprecation note?

Compared to `[PredecessorComponent]`:

- **[Feature name].** [One sentence: what changed.]
- **[Renamed prop].** `[oldName]` → `[newName]`.
- **[Removed feature].** [What to use instead.]

---

## Overview

_DSDS: `useCases` — purpose statement, recommended and discouraged scenarios with alternatives_

The key distinction DSDS draws: `useCases` answers **whether** to use something. Guidelines (Usage Guidelines) answer **how** to use it well.

> **Prompts**
> - What is this component, and what single user or system need does it address? Write one sentence.
> - In what specific situations is this the right component to reach for? What conditions make it the correct choice?
> - In what situations should someone *not* use this component — and what should they use instead? What is the rationale for each alternative?
> - What is the clearest decision rule that separates this component from its most commonly confused alternative?

**Purpose:** _(one sentence)_

**Use when:**
- _(specific scenario where this is the right choice)_

**Don't use when:**
- _(scenario → use `[AlternativeComponent]` instead, because ...)_

---

## Anatomy

_DSDS: `anatomy` — named parts, required flag, description, token map per part_

This is the structural source of truth. Every other section (states, variants, tokens, accessibility) references anatomy part names. Define these first.

> **Depth rule**
> - **Leaf components:** document every part — each wrapper matters to tokens and accessibility.
> - **Composite/layout components:** document a part only when it carries component-scoped tokens, manages internal state (scroll container, context provider, observer target), is conditional on a non-obvious prop, or its absence breaks a consumer assumption (e.g. a `:has()` selector targets it). Omit pure structural wrappers (`flex: 1`, `display: contents`) and add the note below.
> - **Composition slots:** when a part is a slot filled by a named subcomponent, name the slot and reference the child's spec — do not expand the subcomponent's internal parts here.

> **Prompts**
> - Starting from the most complex variant, what are the named sub-elements? Every discrete visual or structural part gets an identifier.
> - Which parts are always rendered, and which are conditional?
> - For each part: what design tokens control its visual properties? Map token-purpose names to token identifiers. Only tokens governed by the design system — not browser defaults.
> - Are any parts themselves instances of other design system components? Which, and in what configuration?
> - Are there meaningful constraints on what a part can contain?

_Annotate a diagram showing the most complex variant with all optional parts visible, each labeled by its identifier._

| Part identifier | Name | Always present? | Description | Tokens (purpose → token id) |
|---|---|---|---|---|
| `[part-identifier]` | [Human name] | ✅ / ☐ | What this part is and what it does. | `[visual-property] → [token.name]` |
| `[slot-identifier]` | [Slot name] | ☐ | Accepts `<ChildComponent>`. [Effect of presence.] See [ChildComponent spec](#). | — |

_When parts are omitted (composite components):_ "Intermediate structural wrappers are omitted — they carry no tokens and have no behavioral constraints."

---
---

# Tier 2 — Specify

*The contract: variants, states, design values, API, behavior, accessibility, content. The build reference.*

---

## Variants

_DSDS: `variants` — dimensions, values with token overrides, invalid combinations (exclusions)_

Variants are independent dimensions of variation — separate axes that can combine. Don't merge unrelated dimensions into one enum.

> **Prompts**
> - What are the independent axes of visual or behavioral variation? Each axis becomes a separate dimension.
> - For each dimension: what values are valid, what is the default, and what does each value communicate?
> - For each variant value: which anatomy part tokens change from the baseline, and to what? List only the overrides.
> - Are there combinations across dimensions that are invalid or visually broken? Why?
> - If an invalid combination is passed, what should happen?

### Dimension: `[dimension-name]`

_What this dimension controls. What the values represent._

| Value | Name | Default? | What it communicates | Token overrides from baseline |
|---|---|---|---|---|
| `[value]` | [Name] | | | `[purpose] → [token.name]` |

### Invalid combinations

| Dimensions | Condition | Reason |
|---|---|---|
| `[dim-a]` + `[dim-b]` | `[value-a]` + `[value-b]` | Why this combination doesn't work. |

---

## States

_DSDS: `states` — identifier, trigger, human name, token overrides from default, rationale_

States are conditions the component can enter based on user interaction or props. Variants configure the component; states change it at runtime.

> **Prompts**
> - What conditions can this component be in? Confirm which apply: default, hover, focus, active/pressed, filled/selected, disabled, read-only, loading, error, success, warning, indeterminate, dragging, expanded, collapsed.
> - For each state: what triggers it — a user action, a prop, a system event, or an internal condition?
> - For each state: which anatomy part tokens change from the default? List only the delta.
> - Which state combinations are valid and must be handled? (focus + error, hover + disabled)
> - Which states does the component manage internally, and which must the consumer control?
> - What does the user perceive in each state — visual change, cursor, animation, or an AT announcement?

| State identifier | Human name | Trigger | Token overrides (delta from default) | Notes |
|---|---|---|---|---|
| `default` | Default | Initial render | — | Baseline. All design-spec values apply. |
| `[state]` | [Name] | [What triggers it] | `[part].[property] → [token.name]` | |

---

## Design Specifications

_DSDS: `design-specifications` — baseline token values, spacing, sizing, typography, responsive_

This section documents the **baseline** — the default variant at the default state. Per-variant and per-state token overrides live in Variants and States, not here.

> **Prompts**
> - What are the baseline visual property values for the default configuration? Express each as a token name.
> - What are the internal spacing relationships (padding, gap, inset)? What changes across size variants?
> - What are the sizing constraints: min width, max width, fixed or flexible height? Do these change per variant?
> - Which anatomy parts contain text? What typography tokens apply to each?
> - How does this component behave across breakpoints?
> - Is the component intrinsically sized or does it stretch to fill available space by default?

### Baseline design properties (default variant, default state)

| Property | Token |
|---|---|
| `[property-name]` | `[token.identifier]` |

### Spacing

| Property | [Size A] | [Size B] | [Size C] |
|---|---|---|---|
| `[spacing-property]` | `[token]` | `[token]` | `[token]` |

### Sizing

| Constraint | [Size A] | [Size B] | [Size C] |
|---|---|---|---|
| Height | | | |
| Min width | | | |
| Max width | | | |

### Typography (per anatomy part)

| Part | Font family | Size | Weight | Line height |
|---|---|---|---|---|
| `[part]` | `[token]` | `[token]` | `[token]` | `[token]` |

### Responsive

| Breakpoint | What changes |
|---|---|
| `[breakpoint]` | _(visual or layout change at this breakpoint)_ |

---

## API

_DSDS: `api` — properties, events, slots, CSS custom properties, CSS parts, methods_

For multi-platform components, create a separate API block per platform and note what differs.

> **Why this is split.** A flat prop table implies every value is consumer-settable. It isn't: some values are derived internally, and some props are slots filled by named subcomponents. The skill classifies each prop in its Model phase and renders it into the right subsection. Omit any subsection with no rows. No prop appears in more than one subsection.

> **Prompts**
> - What can consumers pass to configure this component? For each: name, type, default, required, what it controls.
> - Which values does the component compute or manage itself, never set by the consumer? What are they derived from?
> - Which props accept a specific named subcomponent? What is the slot contract (required?, absence behavior, interaction effect)?
> - What events does it emit, and when? Payload shape?
> - CSS custom properties? CSS shadow parts? Imperative ref methods?
> - Which props are purely semantic/accessibility-related with no visual equivalent?

**Platform:** [Web / iOS / Android]

### Consumer props

_What a page or feature engineer passes in — the externally settable surface._

| Name | Type | Default | Required | Description |
|---|---|---|---|---|
| `[prop]` | `[type]` | `[default]` | Yes / No | What this prop controls. |

### Derived & internal

_Values the component computes or manages on its own. Never passed by the consumer. Omit if none._

| Internal value | Derived from | Notes |
|---|---|---|
| `[value]` | `[props or conditions]` | Why it's derived rather than consumer-controlled. |

### Composition slots

_Props that accept a named subcomponent. Document the slot contract only — never inline the subcomponent's prop table. Omit if none._

| Prop | Compose with | Required | Slot contract |
|---|---|---|---|
| `[slot prop]` | `<ChildComponent>` | Yes / No | Absence behavior, interaction effect, and [link to child spec](#) or *(stub — spec not yet written)*. |

### Events

| Name | Fires when | Payload |
|---|---|---|
| `[event]` | [Condition] | `[type signature]` |

### Methods (ref / instance)

| Method | Description |
|---|---|
| `[method()]` | What it does and when to use it. |

---

## Imports

_DSDS: `imports` — install command, import statement, platform, package, setup notes_

> **Prompts**
> - What is the exact install command and import statement for each supported platform?
> - Any required setup before use — provider wrappers, peer dependencies, polyfills, registered web components?
> - Does importing produce global side effects (global CSS, registered custom elements)?
> - Has the import path changed across major versions? Document old and new paths and link the migration guide.

**[Platform]**
```bash
# install
```
```[language]
# import
```

---

## Interactions & Behaviour

_DSDS: `guidelines` with `category: "interaction"` — RFC 2119 conformance levels (must / should / should-not / must-not)_

Covers **how the component behaves** — not how to use it in a product (that's Usage Guidelines). Focus on what the component itself does: event handling, internal logic, animation, timing.

> **Prompts**
> - What happens on keyboard interaction? On pointer? Differences?
> - What keyboard events does it handle internally, and what does each trigger? What passes through to the consumer?
> - Does it manage internal logic on its own (toggling, selection, collapsing, debouncing)? How does the consumer configure or disable it?
> - Any transitions or animations on state changes? What property, duration, easing?
> - What happens at interaction boundaries — rapid clicks, interaction while loading, interaction in an unsupported state?

| Level | Guideline | Rationale |
|---|---|---|
| **must** | | |
| **must-not** | | |
| **should** | | |
| **should-not** | | |

---

## Accessibility

_DSDS: `accessibility` — keyboard interactions, ARIA attributes, announcements, focus behavior, contrast pairs, reduced-motion_

> **Grounding rule.** Contrast pairs are resolved, not deferred. When the token file is present, the skill walks each pair's token chain to concrete values and fills the actual ratio and ✅/❌. A pair it genuinely cannot resolve shows `[unresolved — chain ends at --token]` (naming where it stopped) and raises a question — never a blanket "verify against token values."

> **Prompts**
> - What ARIA role does the root carry? Which attributes are always required, and which are conditional on state/props?
> - What is the complete keyboard model? List every key/combination and its action. Use the W3C APG pattern as baseline; note deviations.
> - What does a screen reader announce on focus, and on value/state change? Synchronous or via live region?
> - How does focus enter, move within, and leave? Is it ever trapped, and how released?
> - List every foreground/background pair across all states and variants. Confirm each passes WCAG AA (4.5:1 text, 3:1 UI and focus indicators).
> - Animations/transitions? What happens under `prefers-reduced-motion: reduce`?
> - Minimum touch/pointer target size? Hit area larger than visible component?

**WCAG conformance target:** AA / AAA

### ARIA

| Attribute | Applied to | Value / Condition |
|---|---|---|
| `[aria-attribute]` | `[element or part]` | [When and what value] |

### Keyboard interactions

| Key / Combination | Action |
|---|---|
| `[key]` | [What it does] |

### Screen reader announcements

| Context | What is announced |
|---|---|
| Focus enters | |
| State changes to `[state]` | |

### Focus behavior

- _(How focus enters)_
- _(How focus moves within the component, if it has internal focus points)_
- _(How focus exits or is released)_

### Color contrast

| Pairing | Use case | Min ratio | Passes? |
|---|---|---|---|
| `[foreground]` / `[background]` | [Where this pair appears] | 4.5:1 / 3:1 | `[resolved ratio]` ✅ / ❌ |

### Reduced motion

_(For each animation or transition: what it does by default, and what replaces it under `prefers-reduced-motion: reduce`.)_

---

## Content

_DSDS: `content` — labels terminology, localization_

The `content` block is a **reference dictionary** of exact wording and localization rules. Writing conventions (sentence case, imperative voice) go in Usage Guidelines.

> **Prompts**
> - What system-owned strings does this component render? For each: canonical wording, what it communicates, when it appears.
> - What constraints apply to consumer-provided text — character limits, truncation, minimum length?
> - Any directional elements (icons, arrows, carets) that mirror in RTL?
> - How much text expansion should the layout accommodate? What breaks first?
> - Locale-specific formatting concerns for values rendered inside?

### Labels dictionary

| Label | Canonical wording | Meaning | When it appears |
|---|---|---|---|
| `[label-id]` | "[Exact string]" | What it communicates | [Condition] |

### Localization

| Concern | Handling |
|---|---|
| RTL | |
| Text expansion | |
| `[other locale concern]` | |

---
---

# Tier 3 — Verify & relate

*Handoff: acceptance checklist, usage guidelines, neighbors. Sign-off and migration material.*

---

## Acceptance checklist

_Testable pass/fail criteria for design handoff. Derived from this spec's content — not generic boilerplate._

> **Purpose**
> Usage Guidelines answer "how do I use this going forward?" This checklist answers "is this spec complete and correct enough to hand off?" Each item is a binary pass/fail criterion of **design correctness** — not engineering implementation. Items are derived from the spec: each variant, state, motion, ARIA attribute, and deprecated prop generates a corresponding check. Group by functional area; omit empty groups.

**Layout**
- [ ] _(derived from Variants / Design Specifications)_

**Accessibility**
- [ ] Focus ring visible on keyboard interaction (`:focus-visible`), correct token and offset
- [ ] WCAG 2.1 AA: contrast ≥ 4.5:1 on all state × mode combinations
- [ ] _(per-ARIA-attribute announcement check)_

**Motion**
- [ ] `prefers-reduced-motion: reduce` collapses [motion name] to instant

**Content**
- [ ] _(truncation / empty-state / RTL check, if applicable)_

_(Add Header/Chrome, Composition, or Other groups as the component requires. A criterion that can't be written as binary pass/fail belongs in Usage Guidelines, not here.)_

---

## Usage Guidelines

_DSDS: `guidelines` — must / should / should-not / must-not, with rationale, evidence, and testable criteria_

Guidelines answer **how to use this component well** — the rules that apply once someone has decided to use it. Overview answers whether to use it at all.

> **Prompts**
> - What are the absolute requirements — rules where non-compliance produces a broken, inaccessible, or misleading UI?
> - What are the strong recommendations — things most implementations should do, where exceptions need justification?
> - What are the most common misuses or antipatterns seen in practice?
> - Are any rules mechanically testable — by a linter, visual regression, or a11y audit? Define the success criterion.
> - Is any rule backed by evidence — an audit finding, user research, bug report? Record it.

| Level | Guideline | Rationale | Evidence / Testable criterion |
|---|---|---|---|
| **must** | | | |
| **must-not** | | | |
| **should** | | | |
| **should-not** | | | |

---

## Related Components

_DSDS: `useCases` (discouraged + alternatives) + `links` with kind: `alternative`, `parent`, `child`, `related`_

> **Prompts**
> - Which other components are most commonly confused with this one, and what is the deciding factor?
> - Which components does this one frequently get composed with or nested inside?
> - Does this component extend or derive from another? What does it add or constrain?
> - Are there components that should replace this one in specific contexts?

| Relationship | Component | Decision rule |
|---|---|---|
| `alternative` | `[ComponentName]` | Use `[ComponentName]` when ... |
| `parent` | `[ComponentName]` | This component is typically used inside `[ComponentName]`. |
| `child` | `[ComponentName]` | `[ComponentName]` is a specialization of this component. |
| `related` | `[ComponentName]` | Often composed alongside this component. |

---

## Appendices

_Collapsible reference material. Render as `<details>` in MDX, or a labeled "Appendix" heading in plain markdown. Include only what would otherwise bloat the linear read — full subcomponent prop tables (linked from Composition slots), exhaustive token chains, story galleries. Omit the heading if there are none._
