---
name: token-foundation
description: Set up the foundational rules for a 3-tier design token system (primitive → semantic → component). Use this skill whenever someone wants to start a new design token system, establish naming conventions, define what tokens to create, decide on modes/themes, or document the structure of their token architecture. Also use when someone asks what tokens they need, how to name tokens, or how to structure a design system's variables in Figma.
---

# Token Foundation

This skill captures all the decisions that need to be made **once** before any tokens are created. It produces a `foundation.md` document for the project that all other token skills reference.

Run this skill first. Every other skill in this set assumes a foundation document exists.

---

## Step 1 — Interview the designer

Ask these questions before writing anything. Collect all answers before proceeding.

**Scope**
- What product(s) or brands will share this token system?
- Are you starting from scratch, or migrating an existing system? (If migrating → use `token-migrate` after this skill)

**Platform scope**
- Web only, or also native (iOS, Android)?
- This affects typography tokens (system fonts, platform units), spacing conventions, and which output formats are needed. Ask this before generating any structure — retrofitting platform differences later is expensive.

**Tiers needed**
- Do you need component-level tokens (e.g. `button/background/primary/default`)? These add precision but cost maintenance. Recommend: start with primitive + semantic; add component tokens only for your most complex, state-heavy components.

**Token categories** — confirm which are needed:
- Color (almost always yes)
- Spacing / sizing
- Typography (font family, size, weight, line height)
- Border radius
- Elevation / shadow
- Motion / duration
- Opacity

**Modes**
- Light + dark? (most common)
- Any brand themes (e.g. a white-label product)?
- High-contrast accessibility mode?
- Density variants (compact / comfortable / spacious)?

**Output targets**
- Figma only, or also synced to code (CSS custom properties, Style Dictionary, etc.)?
- If code: what format? CSS, SCSS, JS/TS, iOS Swift, Android XML?

---

## Step 2 — Write the foundation document

Output a `foundation.md` file to the working directory with these sections:

### 2a. System overview
One paragraph: what this token system covers, how many tiers, what modes.

### 2b. Naming convention

The canonical naming formula is:

```
[category]/[subcategory]/[property]/[variant]/[state]
```

- Use **kebab-case** within each segment: `font-size`, not `fontSize` or `FontSize`
- Use **forward slash** as the segment separator (maps to Figma variable groups)
- Go from **general → specific**, left to right
- Use **full words**, not abbreviations: `background` not `bg`, `primary` not `pri`
- Names must describe **intent**, not appearance: `color/surface/brand` not `color/pink`

**Segment definitions:**

| Segment | What it describes | Examples |
|---|---|---|
| category | Token type | `color`, `spacing`, `font-size`, `border-radius`, `motion` |
| subcategory | Usage area or group | `surface`, `text`, `border`, `icon`, `feedback` |
| property | What it affects | `background`, `foreground`, `stroke`, `fill` |
| variant | Primary/secondary/brand etc. | `primary`, `secondary`, `brand`, `neutral`, `danger` |
| state | Interactive state | `default`, `hover`, `active`, `disabled`, `focus` |

**Rules:**
- Primitives use appearance names: `color/blue/500`, `spacing/4`, `font-size/14`
- Semantic tokens use intent names: `color/surface/brand`, `color/text/primary`
- Component tokens use component-first naming: `button/background/primary/hover`
- Never include hex values, px values, or color names in semantic or component token names
- Omit segments that aren't meaningful: not every token needs all five levels

**Forbidden patterns:**
- `color/blue` as a semantic token (describes appearance, not intent)
- `btnBgPrimary` (camelCase, abbreviations)
- `primary-button-background-color-default` (wrong order — should be component-first)
- `color/brand-primary-background-default` (flattened — use slashes not hyphens as separators)

### 2c. Namespace consolidation and alias safety

When merging or consolidating namespaces (e.g. combining `checkbox/`, `radio/`, and `toggle/` into a single `control/` namespace), removing the old variables will break any existing aliases in other collections that point to those variable IDs.

**Before removing any variables during a namespace consolidation:**
1. List all tokens in other collections that alias the variables being removed
2. Plan the remapping — for each broken alias, identify the replacement variable in the new namespace
3. Apply the remapping before (or at the same time as) deleting the old variables

Never delete variables without first accounting for their dependents.

### 2d. Stub variable requirements

When creating new namespaces or placeholder variables, every stub must resolve to either a real value or a valid alias before the session ends. Do not leave stubs as raw placeholder values (e.g. `#FFFFFF` / `#000000`) — these require a separate repair pass later and are easy to forget.

If the final value isn't known yet, alias the stub to the closest existing primitive and leave a description note: `STUB: replace with final value`.

### 2e. Tier definitions

Document which tiers this project uses and what each one means:

**Primitive tokens** (`Primitives` collection in Figma)
- Define every raw value in the system
- Named after what they *are*, not how they're used
- Never applied directly to design elements (hidden from publishing)
- Examples: `color/blue/500 → #3B82F6`, `spacing/4 → 16px`

**Semantic tokens** (`Tokens` collection in Figma)
- Reference primitives via aliases
- Named after what they *mean*
- Applied directly to design elements
- Support multiple modes (light/dark) by switching which primitive they point to
- Examples: `color/surface/default → color/neutral/50` (light) / `color/neutral/900` (dark)

**Component tokens** (part of `Tokens` collection, or separate `Components` collection)
- Reference semantic tokens via aliases
- Named after the component and its specific usage
- Optional — only create these for components with many states or overridable properties
- Examples: `button/background/primary/default → color/surface/brand`

### 2f. Modes

List every mode and what it represents:

```
Collection: Tokens
Modes:
  - light (default)
  - dark
```

If additional modes (brand themes, density), list them and which collection they live in.

### 2g. Categories and subcategories

For each category the team confirmed, list the subcategories and properties that will be tokenised. Example:

```
color/
  surface/      → background fills on containers, cards, pages
  text/         → foreground on text elements
  border/       → strokes, dividers, outlines
  icon/         → icon fills
  feedback/     → success, warning, danger, info states
  brand/        → primary brand accent colors
```

### 2h. Visibility and publishing rules

- Primitive collection: mark all tokens as **hidden from publishing**; uncheck "Show in all supported properties"
- Semantic + component tokens: publish normally
- Scope each token where appropriate (e.g. color tokens scoped to fills only, not strokes)

### 2i. Decisions log

A table of any non-obvious decisions made and why. This prevents re-debating the same questions.

| Decision | Choice | Rationale |
|---|---|---|
| Component tokens | Buttons and inputs only | Small team, limited bandwidth |
| Spacing scale | 4pt base (4, 8, 12, 16, 24, 32, 48, 64) | Existing codebase uses 4pt |
| Typography tokens | Figma styles (not variables) | Variables don't support composite text styles yet |

---

## Step 3 — Confirm before proceeding

Present `foundation.md` to the designer. Ask:
1. Does the naming convention look right? Walk through one example token name per category.
2. Are the tiers correct — do you need component tokens, or start with just primitive + semantic?
3. Any modes or categories missing?

Get explicit confirmation before this document is used by other skills.

---

## Expected handoff files

This skill produces `foundation.md`. The table below shows all artifacts in the pipeline and which skill produces or consumes each one:

| File | Produced by | Consumed by | Purpose |
|---|---|---|---|
| `foundation.md` | **token-foundation** | all skills | Naming conventions, tiers, modes, categories |
| `scaffold-state.json` | token-figma-scaffold | token-push, token-apply, token-generate, token-bridge | Collection IDs, mode IDs, variable ID index |
| `token-proposal-[category].json` | token-generate | token-push, token-audit, token-apply | Token definitions per category (draft → approved → pushed) |
| `bridge-mapping.json` | token-bridge (Stage 4) | token-bridge (Stage 7) | Old → new token mapping |
| `bridge-state.json` | token-bridge (Stage 5–6) | token-bridge (graduation) | Bridge variable metadata and status |

For the canonical format of `scaffold-state.json`, see `references/scaffold-state-schema.json`.

---

## Reference

For detailed guidance on Figma implementation of collections and modes, see `references/figma-variables.md`.
For naming examples by category, see `references/naming-examples.md`.
