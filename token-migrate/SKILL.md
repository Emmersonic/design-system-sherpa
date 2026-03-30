---
name: token-migrate
description: Migrate an existing design system from an old token structure (or hardcoded values) to a new 3-tier token system. Use this skill when someone wants to migrate from raw hex values, old Figma styles, a flat token structure, or any previous token system to the primitive/semantic/component model. Also use when someone says "migrate my old tokens", "convert my styles to variables", "update from the old system", "map my existing values to new tokens", or wants to transition their Figma file from one token architecture to another.
---

# Token Migrate

Migrates an existing token system (or raw values) to the 3-tier model. Works in three confirmed stages: inventory → mapping → apply. The designer confirms the mapping table between stage 2 and stage 3 — no changes are made to Figma without explicit approval.

---

## Prerequisites

- A confirmed `foundation.md` from `token-foundation` (the new system's rules)
- The Figma scaffold is in place (`token-figma-scaffold` has been run)
- A Figma file connected via the MCP
- The new tokens should already exist in Figma (run `token-generate` + `token-push` first for each category)

### Figma Bridge files

If the file previously used Figma Bridge, a "Bridge" variable collection will be present. Bridge variables alias into the old semantic layer. This is an advantage: the existing binding tells you exactly which semantic concept the layer was using, which makes mapping to the new component token more deterministic. The goal is re-plumbing — swapping the variable binding to the new component token — without changing any resolved values or visuals.

---

## Stage 1 — Inventory the old system

Scan the current Figma file for everything that needs to be migrated.

### 1a. Find existing variables

Fetch each collection separately to avoid loading everything at once. Start with a summary to see what collections exist:

```
figma_get_variables(fileUrl: <current file>, format: "summary")
```

Then load each collection's data:

```
figma_get_variables(fileUrl: <current file>, format: "filtered", collection: "<collection name>", verbosity: "standard")
```

List all existing variables with:
- Name
- Collection
- Type (color, float, string)
- Current value or alias

### 1b. Find existing styles

Use `figma_get_styles` to find:
- Color styles
- Text styles
- Effect styles (shadows)

### 1c. Detect Figma Bridge variables

Check whether a "Bridge" collection exists:

```
figma_get_variables(fileUrl: <current file>, format: "filtered", collection: "Bridge", verbosity: "standard")
```

If Bridge variables are present, for each one record:
- Bridge variable name (e.g. `bridge/button/background`)
- What it aliases to (the old semantic variable, e.g. `semantic/color/surface/brand`)
- Which layers use it

This alias chain is a strong signal for Stage 2 mapping. A layer bound to a Bridge variable already has a known semantic intent — you just need to find the new component token that matches.

### 1d. Find hardcoded values

If the old system used raw hex values applied directly (no styles or variables), use `figma_lint_design` or `figma_audit_design_system` to surface layers with hardcoded fills, strokes, and text colors.

### 1e. Produce the inventory

Present a complete inventory table. Flag Bridge variables in their own group — they carry the most mapping confidence:

```
Old token / value                      | Type   | Current value   | Used on N layers
---------------------------------------|--------|-----------------|------------------
[BRIDGE] bridge/button/background      | color  | → semantic/...  | 23 layers
[BRIDGE] bridge/button/label           | color  | → semantic/...  | 23 layers
styles/Primary                         | color  | #3B82F6         | 47 layers
styles/Text Default                    | color  | #111827         | 203 layers
styles/Background                      | color  | #FFFFFF         | 89 layers
vars/brand-color                       | color  | → Primary       | 12 layers
#E5E7EB (hardcoded)                    | color  | #E5E7EB         | 8 layers
```

---

## Stage 2 — Build the mapping table

For each old token/value, propose which new token it should map to. Use the new token names from `foundation.md` and the existing new variables in Figma.

**Format:**
```
Old                            | New token                         | Confidence | Notes
-------------------------------|-----------------------------------|------------|------------------
styles/Primary                 | color/surface/brand               | High       |
styles/Primary (on text)       | color/text/on-brand               | High       | Context-dependent
styles/Text Default            | color/text/primary                | High       |
styles/Background              | color/surface/default             | High       |
vars/brand-color               | color/surface/brand               | High       | Alias of Primary
#E5E7EB (hardcoded)            | color/border/default              | Medium     | Matches border value
styles/Gray 500                | color/text/secondary              | Medium     | Check usage context
styles/Shadow Small            | KEEP AS STYLE                     | —          | No variable equivalent
```

**Confidence levels:**
- **High** — value matches exactly and usage context is unambiguous
- **High (Bridge-confirmed)** — layer was using a Bridge variable; the Bridge → semantic alias chain confirms the intent. Use the semantic token name to look up the correct new component token. The resolved value must be identical before and after — if it isn't, something is wrong with the new token, not the mapping.
- **Medium** — value matches but usage context suggests this may apply differently in some layers
- **Low** — best guess; manual review recommended after migration
- **No match** — no appropriate new token exists; either generate a new one or keep the old

**Bridge-confirmed mapping process:** For each Bridge variable, follow the alias chain:
1. Bridge var (e.g. `bridge/button/background`) → aliases to old semantic var (e.g. `semantic/color/surface/brand`)
2. Find the new component token whose semantic alias matches (e.g. `component/button/background` → `color/surface/brand`)
3. Confirm the resolved hex value is unchanged
4. Mark as High (Bridge-confirmed) in the mapping table

**Context-dependent mappings:** Some old tokens were overloaded — the same style used for backgrounds in some places and text in others. Flag these explicitly. They may require layer-by-layer decisions.

**New tokens needed:** If the inventory reveals values with no matching new token, note them as gaps. Decide whether to create new tokens (go back to `token-generate`) or accept that some layers will be manually updated.

### Confirm before proceeding

**Stop here.** Present the mapping table to the designer and ask:

1. Do all the High-confidence mappings look correct?
2. How should Medium/Low-confidence mappings be handled? (Accept the proposal, manually review those layers, or skip?)
3. Are there any old tokens that should NOT be migrated (kept as-is, or deleted)?
4. Should any new tokens be created to fill the gaps?

**Do not proceed to Stage 3 until the designer explicitly confirms the mapping table.**

---

## Stage 3 — Apply the migration

Apply the confirmed mapping to Figma. Work category by category (color first, then spacing, etc.).

### 3a. Remap variable aliases

For old variables that can be remapped to new ones (rather than deleted):

```
figma_update_variable(
  variableId: <old variable id>,
  value: { type: "VARIABLE_ALIAS", id: <new token id> }
)
```

This preserves any layers already using the old variable — they now inherit the new token's value through the alias chain.

**For Bridge variables:** Do not remap the Bridge variable itself. Instead, rebind the layers that reference the Bridge variable directly to the new component token. This removes the Bridge intermediary and establishes a clean direct binding. The resolved value must not change — verify this before and after with `figma_get_token_values` or a screenshot comparison.

### 3b. Remap Figma styles to variables

For old color styles being replaced by new variables:

Use `figma_execute` to iterate through layers and rebind fills/strokes from the old style to the new variable:

```js
// Example: rebind layers from a style to a variable
const pages = figma.root.children;
for (const page of pages) {
  for (const node of page.findAll()) {
    if (node.fillStyleId === '<old-style-id>') {
      node.fillStyleId = ''; // detach from style
      node.fills = [{ type: 'SOLID', color: ..., boundVariables: { color: { type: 'VARIABLE_ALIAS', id: '<new-variable-id>' } } }];
    }
  }
}
```

**Important:** This is irreversible within the session. Recommend the designer duplicate the file or create a branch before running Stage 3.

### 3c. Remap hardcoded values

For layers with hardcoded hex values (no style or variable), use `figma_execute` to find and rebind them:

```js
const target = { r: 0.898, g: 0.910, b: 0.922, a: 1 }; // #E5E7EB
for (const node of figma.root.findAll()) {
  if (!node.fills) continue;
  node.fills = node.fills.map(fill => {
    if (fill.type === 'SOLID' && colorsMatch(fill.color, target)) {
      return { ...fill, boundVariables: { color: { type: 'VARIABLE_ALIAS', id: '<new-variable-id>' } } };
    }
    return fill;
  });
}
```

### 3d. Handle text styles

Text styles cannot be directly replaced by variables (Figma limitation). Options:
- Keep existing text styles and update their color fill to use new color variables
- Document text style names in the foundation as the source of truth for composite typography
- Note this as a remaining manual step if the designer wants to fully migrate to a variables-only system

---

## Stage 4 — Validate

After applying:

1. **No-visual-change check** — take a screenshot before and after Stage 3. The output must be pixel-identical. Any visual difference means a token resolved to the wrong value and must be investigated before continuing.
2. Run `token-audit` to check for any remaining hardcoded values or broken aliases
3. Spot-check 5–10 layers across different component types to verify tokens applied correctly
4. Switch between light and dark mode to confirm tokens respond correctly
5. Check for any layers that still reference old Bridge variables or styles

For Bridge-migrated layers specifically: confirm the new component token binding is in place and the Bridge variable is no longer referenced. The Bridge collection can be removed once all references are gone.

Report: how many layers were migrated (broken down by Bridge-confirmed vs. other), what's still using old values, and what requires manual attention.

---

## Stage 5 — Clean up old tokens

After confirming the migration looks correct:

**For old variables being replaced:**
- Apply the deprecation pattern: update description to `DEPRECATED: migrated to [new-token-name]`, alias to new token
- Schedule for deletion in the next major version cycle

**For old styles being replaced:**
- Unlink from layers (done in Stage 3b)
- Delete the style from the Figma file when safe

**For hardcoded values:**
- No cleanup needed — they were replaced in-place

---

## Notes on risk

Migration is the highest-risk operation in this skill set. Recommend:
- Working on a branch or duplicate file
- Migrating one component or page at a time rather than the whole file at once
- Running Stage 4 validation between each batch before proceeding
