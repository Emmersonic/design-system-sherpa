# Component Spec — Template

> **Purpose**
> This template defines what a complete engineering spec for a design system component should contain. Fill out each section by answering the prompts for your specific component. Not every section applies to every component — skip sections that genuinely don't fit, but treat states, token mapping, and accessibility as required.
>
> **Conformance tiers**
> - **Level 1 — Core:** Metadata + Overview + Anatomy
> - **Level 2 — Complete:** + Variants + States + Design Specifications + API + Accessibility
> - **Level 3 — Gold:** All sections, with evidence-backed guidelines and per-platform coverage

---

## 0. Metadata

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

## 1. Overview

_DSDS: `useCases` — purpose statement, recommended and discouraged scenarios with alternatives_

The key distinction DSDS draws: `useCases` answers **whether** to use something. Guidelines (§11) answer **how** to use it well.

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

## 2. Anatomy

_DSDS: `anatomy` — named parts, required flag, description, token map per part_

This is the structural source of truth. Every other section (states, variants, tokens, accessibility) references anatomy part names. Define these first.

> **Prompts**
> - Starting from the most complex variant of this component, what are all the named sub-elements? Every discrete visual or structural part gets an identifier.
> - Which parts are always rendered, and which are conditional — appearing only when a certain prop is set or content is provided?
> - For each part: what design tokens control its visual properties? Map token-purpose names (what the token does) to token identifiers (the token's name in your system). Only include the tokens that are actually governed by the design system — not browser defaults.
> - Are any parts themselves instances of other design system components? Which, and in what configuration?
> - Are there meaningful constraints on what a part can contain — length limits, allowed child types, structural rules?

_Annotate a diagram showing the most complex variant with all optional parts visible, each labeled by its identifier._

| Part identifier | Name | Always present? | Description | Tokens (purpose → token id) |
|---|---|---|---|---|
| `[part-identifier]` | [Human name] | ✅ / ☐ | What this part is and what it does. | `[visual-property] → [token.name]` |

---

## 3. Variants

_DSDS: `variants` — dimensions, values with token overrides, invalid combinations (exclusions)_

Variants are independent dimensions of variation — separate axes that can combine. Don't merge unrelated dimensions into one enum.

> **Prompts**
> - What are the independent axes of visual or behavioral variation on this component? Each axis becomes a separate variant dimension.
> - For each dimension: what values are valid, what is the default, and what does each value communicate to the user or signal in the interface?
> - For each variant value: which anatomy part tokens change compared to the baseline, and to what tokens? List only the overrides — not every token.
> - Are there combinations of values across dimensions that are invalid or visually broken? Why — is it a technical constraint, a visual failure, or an accessibility issue?
> - If an invalid combination is passed, what should happen? (Warn in console, fall back silently, throw?)

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

## 4. States

_DSDS: `states` — identifier, trigger, human name, token overrides from default, rationale_

States are conditions the component can enter based on user interaction or props. Variants configure the component; states change it at runtime.

> **Prompts**
> - What are all the conditions this component can be in? Go through the full list and confirm which apply: default, hover, focus, active/pressed, filled/selected, disabled, read-only, loading, error, success, warning, indeterminate, dragging, expanded, collapsed.
> - For each state: what triggers it — a user action, a prop, a system event, or an internal condition?
> - For each state: which anatomy part tokens change from the default, and to what? List only the delta.
> - Which state combinations are valid and must be explicitly handled? (e.g. focus + error, hover + disabled)
> - Which states does the component manage internally, and which must the consumer control via props?
> - What does the user perceive in each state — visual change, cursor change, animation, or an assistive technology announcement?

| State identifier | Human name | Trigger | Token overrides (delta from default) | Notes |
|---|---|---|---|---|
| `default` | Default | Initial render | — | Baseline. All design-spec values apply. |
| `[state]` | [Name] | [What triggers it] | `[part].[property] → [token.name]` | |

---

## 5. Design Specifications

_DSDS: `design-specifications` — baseline token values, spacing, sizing, typography, responsive_

This section documents the **baseline** — the default variant at the default state. Per-variant and per-state token overrides live in §3 and §4, not here.

> **Prompts**
> - What are the baseline visual property values for this component's default configuration? Express each as a token name — not a raw value.
> - What are the internal spacing relationships (padding, gap, inset)? Document with token names. What changes across size variants?
> - What are the sizing constraints: minimum width, maximum width, fixed or flexible height? Do these change per variant?
> - Which anatomy parts contain text? What typography tokens apply to each?
> - How does this component behave across breakpoints — does it change layout, scale, or visual treatment at any screen size?
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

## 6. API

_DSDS: `api` — properties, events, slots, CSS custom properties, CSS parts, methods_

For multi-platform components, create a separate API block per platform and note what differs across them.

> **Prompts**
> - What properties can consumers pass to configure this component? For each: name, type, default value, whether it's required, and what it controls.
> - What events does this component emit, and when does each fire? What is the payload shape?
> - What named slots, render props, or children positions does the component accept? What constraints apply to each slot?
> - Does the component expose CSS custom properties for lightweight theming overrides outside the token system?
> - Does the component expose CSS shadow parts (`::part()`) for external structural style targeting?
> - Does the component expose any imperative methods on its ref or instance?
> - Which props are purely semantic or accessibility-related with no visual design equivalent?
> - What behaviors does the consumer control vs. what does the component manage internally?

**Platform:** [Web / iOS / Android]

### Properties

| Name | Type | Default | Required | Description |
|---|---|---|---|---|
| `[prop]` | `[type]` | `[default]` | Yes / No | What this prop controls. |

### Events

| Name | Fires when | Payload |
|---|---|---|
| `[event]` | [Condition] | `[type signature]` |

### Slots / Children

| Name | Description | Constraints |
|---|---|---|
| `[slot]` | What goes here | What is and isn't allowed |

### Methods (ref / instance)

| Method | Description |
|---|---|
| `[method()]` | What it does and when to use it. |

---

## 7. Imports

_DSDS: `imports` — install command, import statement, platform, package, setup notes_

> **Prompts**
> - What is the exact install command and import statement for each supported platform?
> - Are there any required setup steps before this component can be used — provider wrappers, peer dependencies, polyfills, registered web components?
> - Does importing this component produce any global side effects (global CSS, registered custom elements)?
> - Has the import path changed across major versions? If so, document the old and new paths and link to the migration guide.

**[Platform]**
```bash
# install
```
```[language]
# import
```

---

## 8. Interactions & Behaviour

_DSDS: `guidelines` with `category: "interaction"` — RFC 2119 conformance levels (must / should / should-not / must-not)_

This section covers **how the component behaves** — not how to use it in a product (that's §11). Focus on what the component itself does: event handling, internal logic, animation, and timing.

> **Prompts**
> - What happens when the user interacts with this component via keyboard? Via pointer? Are there differences?
> - What keyboard events does the component handle internally, and what action does each trigger? What events pass through to the consumer?
> - Does this component have any internal logic it manages on its own (e.g. toggling, selection, collapsing, debouncing)? How does the consumer configure or disable that logic?
> - Are there any transitions or animations on state changes? What property changes, over what duration and easing?
> - What happens at the boundary cases of interaction — rapid repeated clicks, interaction while loading, interaction in an unsupported state?

| Level | Guideline | Rationale |
|---|---|---|
| **must** | | |
| **must-not** | | |
| **should** | | |
| **should-not** | | |

---

## 9. Accessibility

_DSDS: `accessibility` — keyboard interactions, ARIA attributes, announcements, focus behavior, contrast pairs, reduced-motion_

> **Prompts**
> - What ARIA role does the root element carry? What ARIA attributes are always required, and which are conditional on state or props?
> - What is the complete keyboard interaction model? List every key or key combination that this component responds to, and what action it triggers. Use the W3C APG pattern for this component type as a baseline, then note any deviations.
> - What does a screen reader announce when focus lands on this component? What does it announce when the component's value or state changes? Are announcements synchronous or via a live region?
> - How does focus enter, move within, and leave this component? Is focus ever trapped, and if so, how is it released?
> - List every foreground/background color pair used across all states and variants. Confirm each passes WCAG AA (4.5:1 for text, 3:1 for UI elements and focus indicators).
> - Does this component include animations or transitions? What does it do under `prefers-reduced-motion: reduce`?
> - What is the minimum touch/pointer target size? Is the hit area ever larger than the visible component?

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
| `[foreground]` / `[background]` | [Where this pair appears] | 4.5:1 / 3:1 | ✅ / ❌ |

### Reduced motion

_(For each animation or transition in this component: what it does by default, and what replaces it under `prefers-reduced-motion: reduce`.)_

---

## 10. Content

_DSDS: `content` — labels terminology, localization_

The distinction DSDS draws: the `content` block is a **reference dictionary** of exact wording and localization rules. Writing conventions (sentence case, imperative voice) go in §11 as guidelines.

> **Prompts**
> - What system-owned strings does this component render? For each: what is the canonical wording, what does it communicate, and when does it appear?
> - What constraints apply to consumer-provided text content — character limits, truncation rules, required minimum length?
> - Does this component include any directional elements (icons, arrows, carets) that need to mirror in RTL layouts?
> - How much text expansion should the layout accommodate for translated strings? What breaks first if strings are longer than expected?
> - Are there locale-specific formatting concerns for values rendered inside this component?

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

## 11. Usage Guidelines

_DSDS: `guidelines` — must / should / should-not / must-not, with rationale, evidence, and testable criteria_

Guidelines answer **how to use this component well** — the rules that apply once someone has decided to use it. `useCases` (§1) answers whether to use it at all.

> **Prompts**
> - What are the absolute requirements — rules where non-compliance produces a broken, inaccessible, or misleading UI?
> - What are the strong recommendations — things most implementations should do, where exceptions are possible but need justification?
> - What are the most common misuses or antipatterns you've seen in practice with this component?
> - Are any of these rules mechanically testable — by a linter, visual regression, or accessibility audit? If so, define the success criterion.
> - Is any rule backed by evidence — an audit finding, user research, bug report, or test data? If so, record it in the evidence field.

| Level | Guideline | Rationale | Evidence / Testable criterion |
|---|---|---|---|
| **must** | | | |
| **must-not** | | | |
| **should** | | | |
| **should-not** | | | |

---

## 12. Related Components

_DSDS: `useCases` (discouraged + alternatives) + `links` with kind: `alternative`, `parent`, `child`, `related`_

> **Prompts**
> - Which other components in the system are most commonly confused with this one, and what is the deciding factor between them?
> - Which components does this one frequently get composed with or nested inside?
> - Does this component extend or derive from another component in the system? What does it add or constrain?
> - Are there components that should replace this one in specific contexts?

| Relationship | Component | Decision rule |
|---|---|---|
| `alternative` | `[ComponentName]` | Use `[ComponentName]` when ... |
| `parent` | `[ComponentName]` | This component is typically used inside `[ComponentName]`. |
| `child` | `[ComponentName]` | `[ComponentName]` is a specialization of this component. |
| `related` | `[ComponentName]` | Often composed alongside this component. |
