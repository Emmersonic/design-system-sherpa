# Pattern Usage Doc — Template

> **Purpose**
> Designer-facing usage documentation for a multi-component pattern. Audience: product designers composing screens.
>
> **Not a spec.** Exclude: API props, code, token identifiers, ARIA code, engineering terminology.
>
> **Minimum bar:** A designer one year into their career should read this, understand it, and know what to do next.

---

## [Pattern Name]

**What it is:** _(one sentence from the user's perspective — what problem this pattern solves)_

**Status:** draft | experimental | stable | deprecated  
**Figma:** [link]

---

## When to use it

> **Prompts**
> - What recurring user or product problem does this pattern solve?
> - In what product contexts is this the right pattern?
> - When should a designer use something else — and what is that alternative?
> - What is the clearest decision rule separating this from its closest alternative?

**Use when:**
- _(specific product context or condition)_

**Don't use when:**
- _(context → use [AlternativePattern] instead, because [rationale])_

---

## Structure

> **Prompts**
> - What regions or sections make up this pattern? What role does each play?
> - Which regions are required and which are optional? What happens if an optional region is omitted?
> - Are there hierarchy or ordering rules between regions?
>
> Describe the layout at a high level — what goes where and why. No component-level anatomy.

| Region | Role | Required? | Notes |
|---|---|---|---|
| [region name] | [What this region communicates or enables] | Yes / No | [Constraints or configuration notes] |

---

## Variants

> **Prompts**
> - Does this pattern have meaningfully different sub-types that change composition or behavior, not just appearance?
> - For each variant: what structural or behavioral difference distinguishes it? What use case does it serve?
>
> _Skip this section if the pattern has no meaningful structural variants._

| Variant | What makes it different | When to use it |
|---|---|---|
| [name] | [Structural or behavioral distinction] | [The specific condition or context] |

---

## What to design for

> **Prompts**
> - What states does a designer need to explicitly account for in their layouts?
> - What does the user see in each state — what feedback do they get?
> - What are the edge cases a designer must design for, not leave to chance?
>
> Frame as "the user does X, then sees Y." Only include states the designer must explicitly design — not auto-managed system transitions.

| Scenario | What the user sees | Design consideration |
|---|---|---|
| Loading / async | | |
| Error | | |
| Empty / zero-state | | |
| Success | | |
| [pattern-specific edge case] | | |

---

## Usage guidelines

> **Prompts**
> - What are the absolute rules — violations that create broken, inaccessible, or confusing experiences?
> - What are the most common real mistakes designers make with this pattern?
> - For each guideline: why does the rule exist? What breaks or degrades if it's ignored?
>
> **Do/Don't rule:** Every example must describe something a designer could actually do wrong when composing this pattern. Nothing constrained by the component system itself. Focus on: composition mistakes, wrong pattern choice, missing states, hierarchy errors, misleading flows.

### Do

| Guideline | Why |
|---|---|
| [Specific, actionable instruction] | [The rationale — what the user gains from this] |

### Don't

| Guideline | Why |
|---|---|
| [Specific description of a real antipattern] | [What the user experiences or misunderstands] |

---

## Content guidelines

> **Prompts**
> - What copy appears in this pattern that the product team authors?
> - What are the rules for headings, CTAs, error messages, empty state copy?
> - What copy mistakes are most common for this pattern?
>
> _Skip only if the pattern has no meaningful copy decisions._

| Copy element | Rule | Example |
|---|---|---|
| Heading / title | | |
| Primary CTA | [Verb + noun, sentence case, max N chars] | |
| Error message | | |
| Empty state | | |

**Copy mistakes to avoid:**
- **Don't:** [Bad pattern] — [why it fails]
- **Do:** [Better pattern] — [why it works]

---

## Accessibility responsibilities

> **Prompts**
> - What must the designer ensure in their layouts for this pattern to be accessible?
> - Are there reading order or focus decisions the designer needs to annotate for engineering?
> - Are there heading level or landmark decisions the designer controls?
>
> Plain language only. No ARIA code. Everything here should be actionable in Figma or a handoff annotation.

| What to ensure | Why it matters |
|---|---|
| [Designer action or annotation] | [Accessible outcome it enables] |

---

## Related patterns

> **Prompts**
> - Which patterns are most commonly confused with this one? What is the deciding factor?
> - Are there narrower, more specific patterns to use in certain conditions?

| | Pattern | When to choose it |
|---|---|---|
| Instead of this | `[PatternName]` | [Condition that makes the alternative the better choice] |
| Often paired with | `[PatternName]` | [In what product context] |
