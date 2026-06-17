# Pattern Spec — Template

> **Purpose**
> This template defines what a complete engineering spec for a design system pattern should contain. A pattern is a multi-component solution to a recurring UX problem — it documents composition, logic, lifecycle, and user flow rather than the visual properties of a single element.
>
> **Component spec vs. pattern spec**
> A component spec answers: "How do I build this element correctly?"
> A pattern spec answers: "How do I compose these elements into a working, correct feature?"

> **How this spec is organized — read in three tiers**
> The spec is grouped into three tiers, in reading order. A reader rarely needs all three at once.
>
> - **Orient** — what problem this solves, when to reach for it, and what it's composed of. The quick read.
> - **Specify** — the contract: lifecycle, interaction flow, data, validation, errors, async, success, accessibility, content, edge cases. The build reference.
> - **Verify & relate** — handoff: acceptance checklist, instrumentation, a copy-ready blueprint, and neighboring patterns. The sign-off and reference material.
>
> Bulky reference material (the blueprint, exhaustive event tables) belongs in **collapsible appendices** at the end — render as `<details>` in MDX, or a labeled "Appendix" heading in plain markdown. Section numbers are deliberately omitted; sections are referenced by name and omitted entirely when they don't apply.

> **Conformance tiers**
> - **Level 1 — Core:** Metadata + Overview + Composition + Interaction flow
> - **Level 2 — Complete:** + States + Validation + Error handling + Accessibility
> - **Level 3 — Gold:** All sections, including data model, edge cases, content, and instrumentation

---
---

# Tier 1 — Orient

*What problem this pattern solves, when to use it, and what it's composed of. The quick read.*

## Metadata

_DSDS: `metadata` — status, since, lastUpdated, aliases, category, tags, links_

> **Prompts**
> - What is the lifecycle status of this pattern? Is it recommended for new work, experimental, or being phased out?
> - When was this pattern established, and when was it last meaningfully updated?
> - What other names does this pattern go by across teams, products, or historical documentation?
> - Where do the canonical artifacts live? Link to: the Figma frame, any reference implementation or code example, and the relevant Storybook story or documentation page.
> - If deprecated: what replaces it, and what's the migration path?

```
Name:
Identifier (kebab-case):
Category:
Status:      draft | experimental | stable | deprecated
Since version:
Last updated:
Aliases:
Links:
  design:
  reference implementation:
  documentation:
```

---

## What's new

_Conditional — include only when this pattern replaces or extends a predecessor. Omit the heading entirely otherwise._

> **Purpose**
> When a pattern is an explicit replacement or evolution of an existing one, lead with the delta — what changed, not a rehash of current behavior.

Compared to `[PredecessorPattern]`:

- **[Change].** [One sentence: what changed — composition, flow, data shape, or behavior.]
- **[Removed/renamed region or step].** [What replaces it.]

---

## Overview

_DSDS: `useCases` — purpose, recommended scenarios, discouraged scenarios with alternatives_

> **Prompts**
> - What recurring UX problem does this pattern solve? State it in one sentence from the user's perspective.
> - In what specific product or feature contexts is this the right pattern to reach for?
> - When should a team *not* use this pattern — and what should they use instead? What makes those alternatives better in those contexts?
> - What is the decisive difference between this pattern and the closest alternative pattern?
> - Does this pattern exist to solve a design problem, a technical problem, or both?

**Purpose:** _(one sentence from the user's perspective)_

**Use when:**
- _(specific context or condition where this is the right pattern)_

**Don't use when:**
- _(context → use `[AlternativePattern]` instead, because ...)_

---

## Composition

_DSDS: `anatomy` (structural sections) + `links` (component references with `role` and `required` flag)_

A pattern's anatomy describes its structural layout regions — not visual sub-elements. Each region references one or more design system components.

> **Prompts**
> - What are the structural regions that make up this pattern's layout? Give each a name and describe its role.
> - For each region: which design system component(s) does it contain? Is that component required for the pattern to function, or optional?
> - What is the assembly order — which regions are fixed in position and which are flexible?
> - Can any region be omitted without breaking the pattern? What degrades gracefully vs. what breaks entirely?
> - Are any components shared between patterns? If so, are there configuration differences the engineer needs to know about?

_Include a structural anatomy diagram showing all regions at their maximum composition. Label each region by name and show which component fills it._

| Region | Role | Component(s) used | Required? | Notes |
|---|---|---|---|---|
| `[region-name]` | What this region is for | `[ComponentName]` | ✅ / ☐ | Configuration notes or constraints |

---

## Variants

_DSDS: `variants` — sub-types of the pattern, with structural or behavioral differences_

Pattern variants are meaningfully different sub-types — not just visual tweaks. If the difference is only cosmetic, it probably belongs on a component variant, not a pattern variant.

> **Prompts**
> - Does this pattern have meaningfully different sub-types — variations that change composition, layout, or core behavior, not just appearance?
> - For each variant: what structural or behavioral difference distinguishes it? What use case does it serve that the base pattern doesn't cover?
> - Does a variant add or remove regions from the base composition? Does it substitute different components?
> - Can variants be combined, or is each a discrete choice?

| Variant | What distinguishes it | When to use it |
|---|---|---|
| `[variant-name]` | How it differs structurally or behaviorally | The specific condition that calls for this sub-type |

---
---

# Tier 2 — Specify

*The contract: lifecycle, interaction flow, data, validation, errors, async, success, accessibility, content, edge cases. The build reference.*

---

## State Lifecycle

_DSDS: `states` — pattern-level conditions, triggers, transitions_

Pattern states describe the lifecycle of the feature as a whole — not the states of individual components within it. A pattern state is a condition the whole composition can be in.

> **Prompts**
> - What are all the conditions this pattern can be in across its full lifecycle? (e.g. loading initial data, pristine/unmodified, dirty/modified, validating, submitting, success, error, empty, locked/read-only)
> - What triggers each state transition — a user action, a system event, an API response, a timer?
> - Draw the state machine: which transitions are possible from which states? Are any transitions one-way?
> - Which states can overlap? (e.g. can a pattern be in both "dirty" and "loading" simultaneously?)
> - What does the user see and experience in each state? What feedback confirms the transition?
> - Which states are controlled by the consumer vs. managed internally by the pattern's logic?

_Include a state machine diagram. Each node is a state; each edge is a transition with its trigger._

| State | Trigger | User-facing feedback | Notes |
|---|---|---|---|
| `[state]` | [What causes this state] | [What the user sees or hears] | |

---

## Interaction Flow

_DSDS: `interactions` — ordered steps with triggers, component involvement, and examples_

The interaction flow is the time-ordered sequence of what happens as the user moves through this pattern. It is the most important section for communicating expected behavior to an engineer.

> **Prompts**
> - Walk through the primary user journey through this pattern step by step, in time order. What happens at each step?
> - For each step: what triggers it — a user action or a system response? What does the system do in response?
> - For each step: which components are involved, and what role do they play in that moment?
> - Where does the flow branch? What conditions determine which branch the user takes?
> - Walk through the full error path: at what steps can errors occur, what triggers them, and what does each error look like?
> - Walk through the success path to completion: what signals the end of the interaction to the user?

| Step | Trigger | System response | Components involved |
|---|---|---|---|
| 1 | [What the user does or what occurs] | [What the system shows or does] | `[ComponentName]` — [its role in this step] |
| 2 | | | |
| … | | | |

_For patterns with significant branching, use a flowchart diagram rather than a linear table._

---

## Data Model

_DSDS: `sections` (free-form) — structured data that the pattern reads, writes, or manages_

> **Prompts**
> - What data does this pattern manage — what are the inputs it collects or displays, and what is the output it produces?
> - What is the shape of the data object the pattern works with? What are the field names, types, and constraints?
> - Which fields are required vs. optional? Which have defaults?
> - Where does initial data come from — props passed in, an API fetch, local state, or a combination?
> - What does the pattern emit or write on completion — what does the output payload look like?
> - Are there fields the pattern manages internally that are not surfaced to the consumer?

```
Input shape:
{
  [fieldName]: [type]  // [required | optional] — [description]
}

Output shape:
{
  [fieldName]: [type]  // [description]
}
```

---

## Validation

_DSDS: `guidelines` with `category: "interaction"`, `criteria` array — testable rules with RFC 2119 levels_

> **Prompts**
> - Which fields or inputs in this pattern have validation rules? For each: what is valid, what is invalid, and what is the rule?
> - When does validation run — on change (per keystroke or interaction), on blur (when focus leaves), on submit, or triggered programmatically?
> - Are there any cross-field validation rules — cases where the validity of one field depends on the value of another?
> - Are any validation checks asynchronous (requiring a network call)? If so, how is the loading/pending state handled?
> - What is the validation priority order when multiple rules fail on the same field simultaneously?
> - Can the consumer override or extend the built-in validation rules?

| Field / Input | Rule | When validated | Error message pattern |
|---|---|---|---|
| `[field]` | [What constitutes valid/invalid] | on change / on blur / on submit | [Format or example of the error string] |

**Cross-field rules:**
- _(If field A has a certain value, field B becomes required / must satisfy ...)_

---

## Error Handling

_DSDS: `states` (error conditions) + `guidelines` + `sections`_

Errors at the pattern level are distinct from component-level validation errors. This section covers what happens when things fail: field validation, API responses, network failures, and partial successes.

> **Prompts**
> - What kinds of errors can occur in this pattern — field validation errors, API errors, network failures, permission errors, timeout?
> - For each error type: what triggers it, what does the user see, and what actions can the user take to recover?
> - How are field-level errors (a single input is invalid) distinguished from pattern-level errors (the whole submission failed)?
> - When an API returns an error, how does the error message reach the user — inline near the relevant field, in a summary, or as a global notification?
> - What happens in a partial success — some inputs were accepted, some were rejected?
> - Are any errors unrecoverable from within this pattern? What happens then — redirect, disable, require refresh?

| Error type | Trigger | User-facing feedback | Recovery action |
|---|---|---|---|
| Field validation | [Condition] | Inline message adjacent to the field | User corrects the value and resubmits |
| API error (server) | [HTTP status or error code] | [How it surfaces] | [What the user can do] |
| Network failure | [Condition] | [How it surfaces] | [What the user can do] |
| `[other]` | | | |

---

## Loading & Async States

_DSDS: `states` + `guidelines` with `category: "interaction"`_

> **Prompts**
> - Does this pattern require any data to be fetched before it can render? How is the loading state shown — skeleton, spinner, placeholder?
> - When the user takes an action that triggers an async operation (submit, search, load more), how does the pattern communicate that work is in progress?
> - Are any controls disabled or locked while async operations are in flight? Which ones, and why?
> - Does the pattern use optimistic updates — showing a success state before the operation completes? If so, how is a failure rolled back?
> - Are there any debounce or throttle requirements on user-triggered async operations?
> - What is the timeout behavior — if an operation takes too long, when and how does the pattern give up and show an error?

| Async condition | Loading indicator | Controls disabled? | Timeout behavior |
|---|---|---|---|
| Initial data load | [e.g. skeleton, spinner] | [Which controls, if any] | [What happens if it fails] |
| User-triggered action | [e.g. button spinner, overlay] | [Which controls] | |

---

## Success Behaviour

_DSDS: `interactions` (final steps) + `guidelines`_

> **Prompts**
> - What signals to the user that the pattern has completed successfully?
> - After success, does the user stay on the same view, navigate elsewhere, or see a different state of the same pattern?
> - If staying on the same view: what resets, what retains its value, and what updates?
> - Is any success state transient — shown briefly and then dismissed automatically? If so, for how long?
> - If navigation occurs, who controls the destination — the pattern, the consumer, or a router?
> - What should happen if the user attempts to interact with the pattern again immediately after a success state?

**Success outcome:**

| Condition | Behaviour | Duration (if transient) |
|---|---|---|
| [When success occurs] | [Stay / navigate / reset / show confirmation] | |

---

## Accessibility

_DSDS: `accessibility` — pattern-level focus management, live regions, landmark structure, keyboard model_

Pattern-level accessibility is distinct from component-level accessibility. This section covers focus management across the whole composition, landmark and heading structure, and how state transitions are communicated across the full user journey.

> **Prompts**
> - When the pattern first renders, where should focus be placed? Should focus be auto-moved, or does the user navigate to it?
> - When the pattern transitions between states (e.g. loading → error, submitting → success), where does focus go, and how is the transition announced?
> - How are error messages announced to screen reader users — via `aria-live`, `aria-describedby`, or focus movement to an error summary?
> - What landmark roles and heading levels does this pattern's layout establish? How do they fit into the page's existing landmark and heading structure?
> - What is the full keyboard path through this pattern — from entry to completion? Can every action be performed without a pointer?
> - Does the pattern ever block or restrict interaction with content outside it (e.g. a modal or drawer)? If so, how is focus trapped and released?

**Focus management**

| State transition | Focus destination | Announcement |
|---|---|---|
| Pattern enters view | [Where focus goes, if anywhere] | [What is announced] |
| Error state entered | [Focus moves to ...] | [What is announced] |
| Success state | [Focus moves to ...] | [What is announced] |

**Landmark and heading structure**

| Element | Role / Heading level | Notes |
|---|---|---|
| Pattern container | `[landmark role]` | |
| `[heading text]` | `h[N]` | Must be consistent with surrounding page heading hierarchy |

**Keyboard navigation path**

1. _(Entry point)_
2. _(Tab sequence through the pattern)_
3. _(Completion or exit)_

---

## Content

_DSDS: `content` — pattern-level labels, copy conventions, localization_

> **Prompts**
> - What system-owned or pattern-owned strings appear in this pattern — headings, CTA labels, confirmation copy, error summaries?
> - What are the copy conventions for each string type — what tone, tense, and length are expected?
> - Are there strings that must remain consistent across all instances of this pattern (e.g. a standard "Save" label vs. context-specific CTAs)?
> - How does the layout handle text expansion in localized versions? What breaks first if strings are longer?
> - Are there directional elements (arrows, progress indicators) that must mirror in RTL?

### Pattern strings

| String role | Canonical wording | Notes |
|---|---|---|
| Primary CTA | "[Exact string, or pattern: verb + noun]" | |
| Cancel / secondary action | | |
| Success message | | |
| Error summary heading | | |
| Empty state heading | | |

### Copy conventions

| String type | Convention |
|---|---|
| CTA labels | |
| Error messages | |
| Confirmation copy | |

### Localization

| Concern | Handling |
|---|---|
| RTL | |
| Text expansion | |

---

## Edge Cases

_DSDS: `guidelines` + `sections`_

> **Prompts**
> - What happens if the user navigates away before completing the pattern — is there unsaved data? How is the user warned?
> - How does the pattern detect that data has changed from its initial state (dirty state)? What triggers the dirty flag?
> - What does the pattern show when there is no data to display — a first-time empty state, a cleared empty state, or a zero-results empty state? Are these different?
> - What happens if the user has insufficient permissions to complete one or more actions in the pattern?
> - What if the user's session expires mid-interaction?
> - Are there race conditions to guard against — e.g. rapid repeated submissions, concurrent edits from another session?

| Edge case | Trigger | Expected behaviour |
|---|---|---|
| Unsaved changes + navigation | User navigates away with unsaved changes | |
| Empty / first-time state | Pattern has no data to show | |
| Permission restriction | User lacks permission for an action | |
| Session expiry | Session expires during interaction | |
| Rapid repeated submission | User submits multiple times quickly | |
| `[other]` | | |

---
---

# Tier 3 — Verify & relate

*Handoff: acceptance checklist, instrumentation, a copy-ready blueprint, and neighboring patterns. Sign-off and reference material.*

---

## Acceptance checklist

_Testable pass/fail criteria for handoff. Derived from this spec's content — not generic boilerplate._

> **Purpose**
> Usage answers "how do I use this going forward?" This checklist answers "is this pattern spec complete and correct enough to hand off?" Each item is a binary pass/fail criterion derived from the spec: each lifecycle state, interaction branch, validation rule, error path, and focus transition generates a corresponding check. Group by functional area; omit empty groups.

**Flow & lifecycle**
- [ ] _(every lifecycle state has a defined trigger and user-facing feedback)_
- [ ] _(every interaction-flow branch reaches a defined success or error terminus)_

**Validation & errors**
- [ ] _(each validation rule has a defined trigger time and error message)_
- [ ] _(each error type has a defined recovery action)_

**Accessibility**
- [ ] _(focus destination defined for each state transition)_
- [ ] _(landmark and heading structure fits the host page hierarchy)_

_(Add Data, Content, or Other groups as the pattern requires. A criterion that can't be written as binary pass/fail belongs in Validation or Usage, not here.)_

---

## Instrumentation

_DSDS: `sections` (free-form)_

> **Prompts**
> - What analytics events should fire as the user moves through this pattern? For each: event name, when it fires, and what properties it carries.
> - Which fields or values in this pattern contain personally identifiable information (PII) and must not be logged?
> - Are there any performance metrics this pattern should track — time to interactive, time to first data, submission latency?
> - What constitutes a "funnel drop-off" for this pattern — at what point does failing to complete indicate abandonment?

| Event name | Fires when | Properties | PII fields (do not log) |
|---|---|---|---|
| `[pattern]_viewed` | Pattern enters the viewport | `[prop]: [type]` | |
| `[pattern]_started` | User begins interaction | | |
| `[pattern]_completed` | User reaches success state | | |
| `[pattern]_errored` | Error state entered | `error_type`, `error_code` | |
| `[pattern]_abandoned` | [Condition defining abandonment] | | |

---

## Blueprint

_DSDS: `blueprint` — pre-composed, copy-ready code starting point_

A blueprint is a code-level composition of components that implements this pattern. It is a starting point for engineers — not a locked implementation.

> **Prompts**
> - What is the minimal viable code composition that correctly implements this pattern?
> - What are the 2–3 most important adaptation guidelines for engineers using this blueprint as a starting point?
> - Which components in the blueprint are fixed (should not be swapped) and which are flexible (can be substituted)?
> - Are there common mistakes engineers make when hand-rolling this pattern that the blueprint is meant to prevent?

```[language]
// Blueprint: [PatternName]
// Composes: [ComponentA], [ComponentB], [ComponentC]
```

**Adaptation guidelines**

| Level | Guideline |
|---|---|
| **must** | |
| **should** | |

---

## Related Patterns

_DSDS: `links` with kind: `alternative`, `parent`, `child`, `related`_

> **Prompts**
> - What patterns are most commonly confused with this one? What is the clearest deciding factor between them?
> - Does this pattern depend on or extend another pattern?
> - Are there narrower, more specific patterns that should be used when a specific condition is met?

| Relationship | Pattern | Decision rule or connection |
|---|---|---|
| `alternative` | `[PatternName]` | Use `[PatternName]` when ... |
| `parent` | `[PatternName]` | This pattern is a specialization of `[PatternName]`. |
| `related` | `[PatternName]` | Often appears in the same product context. |

---

## Appendices

_Collapsible reference material. Render as `<details>` in MDX, or a labeled "Appendix" heading in plain markdown. Include the full blueprint, exhaustive event/instrumentation tables, or any material that would otherwise bloat the linear read. Omit the heading if there are none._
