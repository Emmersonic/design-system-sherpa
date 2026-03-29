---
name: token-apply
description: Rules and lookup process for correctly applying design tokens when building or modifying designs in Figma via MCP. Use this skill any time an AI agent is creating frames, components, or layouts in Figma and needs to assign colors, spacing, typography, radius, or other visual properties — whether building from scratch, implementing a spec, generating a screen, or modifying existing elements. Also use when asked to "use the design system", "apply tokens", "make this match our system", "implement this design correctly", or any task that involves writing visual properties to a Figma layer. This skill ensures token usage is consistent, semantic-layer-first, and follows the same rules regardless of whether the context is new design or migration.
---

# Token Apply

This skill governs how an AI agent uses the design token system when creating or modifying designs in Figma. It is a constraint layer — loaded mid-task, not run as a standalone workflow.

**Core rule:** Every visual property assigned to a Figma layer must come from a token. No raw values. No primitives on design elements. Always the semantic (or component) tier.

---

## Before touching any layer

### Step 1 — Load the token system

Before assigning any property, check the working directory for local context files first — they're faster and more reliable than live Figma reads:

**Check for local context (preferred):**
- `scaffold-state.json` — collection IDs and mode IDs written by `token-figma-scaffold`. Use to skip the `figma_get_variables` call entirely.
- `token-proposal-*.json` (status `"pushed"`) — contains the full token set with `figma_ids.variable_ids` mapped. Look up variable IDs by token name directly instead of searching live variables.
- `foundation.md` — naming convention, tier structure, and category meanings.

**If local context is absent or incomplete, fall back to live reads:**
```
figma_get_variables(fileUrl: <current file>, format: "filtered", collection: "<collection name>", verbosity: "standard")
figma_browse_tokens(fileUrl: <current file>)
```

Use `format: "filtered"` with the specific collection name to avoid pulling all variables at once. If the collection name isn't known, run `format: "summary"` first to list available collections.

Do not proceed from memory or assume token names. Token systems change, and a token you expect to exist might not, or might have a different name.

### Step 2 — Identify the relevant collection

- Design properties go to tokens in the **`Tokens`** collection (semantic + component tier)
- Never apply tokens from the **`Primitives`** collection directly to layers
- If a `Components` collection exists and you're building a named component, check there first

---

## The tier rule

```
Primitive tokens  →  semantic tokens  →  design layers
                                    ↑
                              apply here only
```

| Layer property | Correct source | Wrong source |
|---|---|---|
| Fill color | `color/surface/brand` | `color/blue/500` or `#3B82F6` |
| Text color | `color/text/primary` | `color/neutral/900` or `#111827` |
| Stroke color | `color/border/default` | `color/neutral/200` or `#E5E7EB` |
| Gap / padding | `spacing/4` (semantic if exists, primitive if not) | `16` (raw number) |
| Corner radius | `border-radius/md` | `8` (raw number) |

**Spacing exception:** If the system uses only primitive spacing tokens (no semantic aliases), applying primitives directly to spacing properties is acceptable — they are still tokens, just not aliased. Never use raw numbers.

---

## Picking the right token

When assigning a visual property, work through this decision sequence:

### For color

**1. What is this element's role?**

| Role | Token category to use |
|---|---|
| Container, card, page background | `color/surface/` |
| Text, label | `color/text/` |
| Icon fill | `color/icon/` (or `color/text/` if no icon category) |
| Border, divider, outline | `color/border/` |
| Focus ring | `color/border/focus` |

**2. What is its intent?**

| Intent | Variant to look for |
|---|---|
| Default/neutral state | `default`, `primary` |
| Brand emphasis | `brand`, `brand-subtle` |
| Positive / success | `success` |
| Destructive / error | `danger` |
| Warning / caution | `warning` |
| Informational | `info` |
| Muted / secondary | `secondary`, `muted`, `subtle` |
| On a colored background | `on-brand`, `on-danger`, etc. |
| Disabled state | `disabled` |

**3. Is there a component token?**

If you're building a named component (button, input, card, badge) and a component token exists for this exact property and state, use it:

```
button/background/primary/default   ← prefer this
color/surface/brand                 ← over this, when building a button
```

Component tokens exist precisely so the component can be updated independently from the semantic layer.

**4. If no match found:**

Do not hardcode a value. Do not use a primitive. Instead:

1. Report: "No token found for [property] in context [element/role]. The closest available token is [X]. Should I use that, or should a new token be created?"
2. Wait for direction before proceeding
3. If instructed to proceed without a token, note it explicitly in your output as a gap to be addressed

### For spacing

List available spacing tokens and match by value:
- 4px → `spacing/1` (or `spacing/4px` depending on naming)
- 8px → `spacing/2`
- 16px → `spacing/4`
- etc.

If semantic spacing exists (e.g. `spacing/component/md`), prefer it for component-level padding. Use primitive spacing for layout gaps.

### For border radius

Match the design intent, not just the pixel value:
- Subtle rounding on inputs/buttons → `border-radius/md`
- Cards, panels → `border-radius/lg`
- Pills, chips, badges → `border-radius/full`
- No rounding → `border-radius/none`

---

## Applying tokens in Figma MCP

When setting a variable-bound property on a layer:

### Color fill
```js
node.fills = [{
  type: 'SOLID',
  color: { r: 0, g: 0, b: 0 },  // placeholder — will be overridden by variable
  boundVariables: {
    color: { type: 'VARIABLE_ALIAS', id: '<variable-id>' }
  }
}];
```

### Stroke color
```js
node.strokes = [{
  type: 'SOLID',
  color: { r: 0, g: 0, b: 0 },
  boundVariables: {
    color: { type: 'VARIABLE_ALIAS', id: '<variable-id>' }
  }
}];
```

### Spacing (auto layout gap, padding)
```js
node.itemSpacing = 0;  // will be overridden
node.boundVariables = {
  itemSpacing: { type: 'VARIABLE_ALIAS', id: '<spacing-variable-id>' }
};
// For padding: paddingTop, paddingBottom, paddingLeft, paddingRight
```

### Corner radius
```js
node.cornerRadius = 0;  // placeholder
node.boundVariables = {
  cornerRadius: { type: 'VARIABLE_ALIAS', id: '<radius-variable-id>' }
};
```

Use `figma_set_fills`, `figma_set_strokes`, or `figma_execute` depending on which MCP tools are available in the current session.

---

## Mode awareness

Tokens are mode-aware by default — when a frame's mode is switched (light → dark), all bound tokens update automatically. This only works if:

- You used a semantic token (not a primitive)
- The token has values set for both modes
- The layer is within a frame that has a mode applied

When building new frames, apply the mode explicitly:

```js
frame.setExplicitVariableModeForCollection(tokensCollection, lightModeId);
```

Do not build designs that only work in one mode. If a token is missing its dark mode value, flag it rather than hardcoding a fallback.

---

## Migration context

If this task involves migrating an existing design (from old tokens or hardcoded values), a confirmed mapping table should exist (produced by `token-migrate`). In that case:

- Follow the mapping table exactly — do not re-derive mappings independently
- If a layer's current value isn't in the mapping table, flag it rather than guessing
- Prefer the mapping table over general token-picking logic when the two conflict

---

## What to report

After completing design work, summarize:

```
Token application summary
─────────────────────────
Layers modified: N
Properties bound to tokens: N
  - Color fills: N
  - Text colors: N
  - Strokes: N
  - Spacing: N
  - Radius: N

Gaps flagged (no matching token):
  - [layer name]: [property] — [description of what was needed]

Primitives used directly (spacing only, acceptable):
  - [token name]: [where used]

Raw values used (unacceptable — requires follow-up):
  - none  ← this should always be "none"
```

If any raw values were used because no token existed and no direction was given, flag them explicitly and recommend creating the missing tokens via `token-generate`. If multiple gaps were found, you can validate the full token set for coverage issues:

```bash
python "${CLAUDE_SKILL_DIR}/../_shared/scripts/validate_tokens.py" token-proposal-[category].json --modes light dark
```

---

## Quick reference — common mistakes to avoid

| Mistake | Correct approach |
|---|---|
| Using `color/blue/500` on a button background | Use `color/surface/brand` or `button/background/primary/default` |
| Hardcoding `#111827` for body text | Use `color/text/primary` |
| Setting `padding: 16` as a raw number | Bind to `spacing/4` variable |
| Using `color/neutral/50` for a card background | Use `color/surface/secondary` |
| Picking any token that's the right color | Pick the token whose *name* matches the *intent* of the element |
| Using the same token for every text element | Differentiate: `text/primary`, `text/secondary`, `text/disabled` |
| Applying tokens only to color, ignoring spacing/radius | All tokenisable properties should be bound |
