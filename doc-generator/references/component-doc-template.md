# Component Usage Doc — Template

> **Purpose**
> Designer-facing usage documentation. Audience: product designers making decisions in Figma or design reviews.
>
> **Not a spec.** Exclude: API props, token identifiers, anatomy tables, ARIA code, engineering terminology, auto-managed states.
>
> **Minimum bar:** A designer one year into their career should read this, understand it, and know what to do next.

---

## [Component Name]

**What it is:** _(one sentence describing what this component communicates or enables for the user)_

**Status:** draft | experimental | stable | deprecated  
**Figma:** [link]

---

## When to use it

> **Prompts**
> - What specific situations call for this component?
> - When should a designer reach for something else instead — and what is that alternative?
> - What is the clearest deciding factor between this and its most commonly confused alternative?

**Use when:**
- _(specific scenario)_

**Don't use when:**
- _(scenario → use [AlternativeComponent] instead, because [one-sentence rationale])_

---

## Variants

> **Prompts**
> - What variants are available to designers in Figma?
> - What does each variant *communicate* to the user — not what it looks like, but what job it does?
> - When should a designer reach for each one?
> - What are the most common mistakes when choosing between variants?
>
> Explain the semantic meaning, not just the visual difference. Designers need to understand *why* the variants exist.

### [Variant dimension name]

_What this dimension controls and why it matters._

| Variant | What it communicates | When to use |
|---|---|---|
| [name] | [The signal this variant sends to the user] | [The condition that calls for it] |

**Common mistakes:**
- _(Choosing [variant A] when [scenario] calls for [variant B], because [rationale])_

---

## States designers control

> **Prompts**
> - Which states require a design decision — where the designer chooses when or whether the state appears?
> - What does the user see in each state and what does it communicate?
> - What must the designer ensure when specifying or handing off each state?
>
> **Exclude:** hover, press, focus ring rendering, transition animations — these are automatic and require no design decision.
> **Include:** disabled, loading, error, inactive, empty — only when the designer controls or must design for them.

| State | What the user sees | When to use it | Designer's responsibility |
|---|---|---|---|
| Disabled | Muted, non-interactive | When the action is unavailable in context | Only disable when the reason is obvious or explained nearby — don't use disabled as a shortcut for "not yet" |
| [state] | | | |

---

## Usage guidelines

> **Prompts**
> - What are the absolute rules — violations that produce a broken, inaccessible, or misleading experience?
> - What are the most common real mistakes designers make with this component?
> - For each guideline: why does it exist? What breaks if it's ignored?
>
> **Do/Don't rule:** Every example must describe something a designer could actually do wrong when composing and making usage decisions. Nothing impossible within the design system. Focus on: wrong component choice, bad composition, semantic mismatch, misleading hierarchy.

### Do

| Guideline | Why |
|---|---|
| [Specific, actionable instruction] | [The consequence of not following this] |

### Don't

| Guideline | Why |
|---|---|
| [Specific description of a real antipattern] | [What the user experiences or misunderstands] |

---

## Content guidelines

> **Prompts**
> - What text does this component display that the product team authors?
> - What are the rules for that text — length, casing, verb form, tone?
> - What copy mistakes are most common for this component?
>
> _Skip this section if the component renders no consumer-authored text. Note why._

| Element | Rule | Example |
|---|---|---|
| [label type] | [Convention: sentence case, imperative, max N chars, etc.] | "[Good example]" |

**Common copy mistakes:**
- **Don't:** "[Bad example]" — [why]
- **Do:** "[Good example]" — [why]

---

## Accessibility responsibilities

> **Prompts**
> - What must the designer ensure in their layouts for this component to be accessible?
> - What should the designer communicate to engineering in handoff annotations?
> - Are there minimum size or contrast decisions the designer controls?
>
> Plain language only. No ARIA code. Every item should be actionable in Figma or a handoff annotation.

| What to ensure | Why it matters |
|---|---|
| [Designer action or annotation] | [Accessible outcome it enables] |

---

## Related components

> **Prompts**
> - Which components are most commonly confused with this one, and what is the deciding factor?
> - Which components often appear alongside this one in compositions?

| | Component | When to choose it |
|---|---|---|
| Instead of this | `[ComponentName]` | [The specific condition that makes the alternative the right choice] |
| Often used with | `[ComponentName]` | [In what composition context] |
