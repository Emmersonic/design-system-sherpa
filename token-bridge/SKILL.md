---
name: token-bridge
description: Create a Legacy mode bridge in an existing Figma Tokens collection that maps new semantic token names to an old token system. Use this skill when migrating component bindings to a new token naming structure while keeping the old system as the live value source — so components are updated to the new names with zero visual change. Also use when someone says "map old tokens to new names without breaking anything", "non-destructive migration", "keep old tokens working while we adopt the new structure", or wants to update component bindings gradually and validate visually before cutting over to new primitives.
---

# Token Bridge

Creates a `Legacy` mode inside the existing `Tokens` collection. Each new semantic token variable aliases its corresponding old token in Legacy mode — so components can be rebound to new names immediately, with no visual change. Graduation (switching aliases from old tokens → new primitives) happens separately, one token or category at a time.

```
Legacy mode:   component → color/surface/brand (new name) → old/Primary (old token) → #3B82F6
After grad.:   component → color/surface/brand (new name) → color/blue/500 (new primitive) → #3B82F6
```

**Why a mode, not separate alias variables:**
- Components switching from Legacy → Light shows exactly what will change before it changes for everyone
- Rollback is a mode toggle, not an undo operation
- Graduation is per-token and reversible until the Legacy mode is deleted

---

## Prerequisites

- A confirmed `foundation.md` from `token-foundation`
- `scaffold-state.json` from `token-figma-scaffold` (collection and mode IDs)
- A Figma library file open and connected via `figma-console` MCP
- The old token system still present in the file (variables, styles, or both)

---

## Stage 1 — Orient

Get a lightweight overview before touching anything.

```
figma_get_design_system_summary()
```

This returns component categories, counts, and collection names from cache — no node scanning. Use it to:
- Confirm which collections exist (identify the old token collection name)
- Understand the component category breakdown (used for batching in Stage 3)
- Estimate total component sets to scan

Also fetch all variables to build the ID→name lookup used in later stages:

```
figma_get_variables(fileUrl: <current file>)
```

Save the full variable list to `bridge-inventory.json`. Record:
- Old token collection name and ID
- Tokens collection ID and existing mode IDs (from `scaffold-state.json` if present)

---

## Stage 2 — Inventory old tokens

Get the full set of old tokens and their resolved values.

```
figma_get_token_values(type: "colors", limit: 50)
figma_get_token_values(type: "spacing", limit: 50)
```

If more than 50 tokens exist in a category, call again with the next page or use `figma_get_variables` filtered by collection ID.

Produce a table:

```
Old token name          | ID                    | Type   | Resolved value
------------------------|----------------------|--------|----------------
Primary                 | VariableID:1:10      | COLOR  | #3B82F6
Text/Default            | VariableID:1:11      | COLOR  | #111827
Background              | VariableID:1:12      | COLOR  | #FFFFFF
Spacing/Base            | VariableID:1:20      | FLOAT  | 16
```

This table is the lookup used when building the mapping in Stage 4.

---

## Stage 3 — Scan component bindings (batched)

Scan what old tokens are actually used on, not what their names suggest. Work in batches of 25 component sets. Stop after the first batch to confirm the approach before continuing.

### 3a. Enumerate component sets

```
figma_get_library_components(libraryFileUrl: <current file>, limit: 25, offset: 0)
```

This returns paginated component sets. Increase `offset` by 25 each batch.

### 3b. Analyze each component set

For each component set returned, call:

```
figma_analyze_component_set(nodeId: <componentSetNodeId>)
```

This returns — without scanning every node individually:
- Variant axes (size, state, type, etc.)
- Fill token, stroke token, text color per variant diff
- Property-to-state mappings

Extract the token names referenced in fill/stroke/text fields. Cross-reference against `bridge-inventory.json` to resolve to old token IDs.

### 3c. Fallback for standalone components and spacing/radius

`figma_analyze_component_set` covers color bindings on COMPONENT_SET nodes. For:
- Standalone `COMPONENT` nodes (not in a set)
- Spacing and radius bindings on any component

Run `scripts/scan_standalone.js` via `figma_execute`. See the script for options — use `filter` to scope to one category and `maxComponents` to limit batch size.

### 3d. Save each batch

After each batch of 25 component sets, write results to `bridge-scan-[n].json`:

```json
{
  "batch": 1,
  "offset": 0,
  "scanned": 25,
  "usage": {
    "VariableID:1:10": {
      "name": "Primary",
      "usedAs": {
        "fill": ["Button", "Badge", "Tag"],
        "textFill": ["Link"]
      }
    }
  }
}
```

### 3e. Confirm after the first batch

**Stop after batch 1.** Present a partial mapping preview (Stage 4 format) for the first batch's findings and ask:
1. Do the semantic name proposals look right for these components?
2. Any surprises — tokens used in contexts you didn't expect?
3. Should any tokens be excluded from bridging (kept as-is)?

**Do not continue scanning until the designer confirms the approach is correct.**

### 3f. Continue remaining batches

Increment offset by 25 and repeat 3a–3d until all component sets are covered. After each batch, append to the running aggregate rather than replacing it.

---

## Stage 4 — Build the mapping table

Aggregate all `bridge-scan-[n].json` files. For each old token, use its actual usage contexts (from Stage 3) — not its name — to propose the new semantic name.

**Decision rules:**
- Same old token used only as fills on containers → `color/surface/[intent]`
- Same old token used only on text nodes → `color/text/[intent]`
- Same old token used as fills on containers AND text → **split into two new tokens** (one per context)
- Same old token used as a stroke → `color/border/[intent]`
- Used on both interactive and neutral elements → flag for designer input

**Format:**

```
Old token            | Usage context         | Proposed new name              | Split? | Confidence
---------------------|-----------------------|--------------------------------|--------|------------
Primary              | fill: Button, Badge   | color/surface/brand            | No     | High
Primary              | textFill: Link        | color/text/link                | Yes    | High
Text/Default         | textFill: all text    | color/text/primary             | No     | High
Background           | fill: surfaces        | color/surface/default          | No     | High
Border/Default       | stroke: inputs, cards | color/border/default           | No     | High
Spacing/Base         | itemSpacing: all      | spacing/4                      | No     | Medium
```

**Confidence levels:**
- **High** — single usage context, unambiguous intent
- **Medium** — mostly one context with minor exceptions
- **Low** — used in 3+ distinct contexts; designer should decide
- **Split** — same token legitimately maps to two new names; both will be created

**Stop here.** Present the full mapping table and ask:
1. Are splits correct, or should some be merged?
2. Any Low-confidence rows to resolve manually?
3. Any old tokens that should NOT be bridged?
4. Any new token names to adjust?

**Do not proceed to Stage 5 until the designer explicitly approves the mapping table.**

Save the approved table to `bridge-mapping.json`.

---

## Stage 5 — Add the Legacy mode

Add a `Legacy` mode to the `Tokens` collection. Do not rename or modify existing modes.

```js
// via figma_execute
const collection = figma.variables.getVariableCollectionById('<tokens-collection-id>');
const legacyMode = collection.addMode('Legacy');
console.log('Legacy mode ID:', legacyMode); // save this ID
```

Or use `figma_add_mode` if available.

Update `scaffold-state.json` with the new mode ID:

```json
{
  "mode_ids": {
    "light": "<existing-id>",
    "dark": "<existing-id>",
    "legacy": "<new-legacy-mode-id>"
  }
}
```

---

## Stage 6 — Create bridge variables

Create the new semantic variables in the `Tokens` collection, then set their `Legacy` mode values as aliases to the corresponding old tokens.

### 6a. Create variable shells

Use `figma_batch_create_variables` in batches of up to 100. At this point, do not set values — just create the named variables:

```
figma_batch_create_variables(
  collectionId: <tokens-collection-id>,
  variables: [
    { name: "color/surface/brand", resolvedType: "COLOR" },
    { name: "color/text/link",     resolvedType: "COLOR" },
    { name: "color/text/primary",  resolvedType: "COLOR" },
    ...
  ]
)
```

For each batch, record the returned variable IDs and add them to `bridge-state.json`.

### 6b. Set Legacy mode aliases

Use `figma_execute` to set each new variable's Legacy mode value as an alias to the old token. Process in batches of 50:

```js
// Set Legacy mode aliases — paste into figma_execute
// Replace LEGACY_MODE_ID and the entries array with actual values
const LEGACY_MODE_ID = 'REPLACE';
const entries = [
  { newVarId: 'VariableID:new:1', oldVarId: 'VariableID:old:10' },
  { newVarId: 'VariableID:new:2', oldVarId: 'VariableID:old:11' },
  // ...up to 50
];

for (const { newVarId, oldVarId } of entries) {
  const newVar = figma.variables.getVariableById(newVarId);
  newVar.setValueForMode(LEGACY_MODE_ID, {
    type: 'VARIABLE_ALIAS',
    id: oldVarId
  });
}
return `Set ${entries.length} Legacy aliases`;
```

After each batch, verify a sample alias resolved correctly:

```js
const v = figma.variables.getVariableById('<new-var-id>');
return v.valuesByMode['<legacy-mode-id>']; // should show { type: 'VARIABLE_ALIAS', id: '...' }
```

### 6c. Set placeholder values for Light and Dark modes

New variables need a value in every mode or Figma will warn. Set the current resolved hex value as a temporary placeholder for Light and Dark modes — this makes the variable non-broken while graduation is in progress:

```
figma_batch_update_variables(updates: [
  { variableId: "VariableID:new:1", modeId: "<light-mode-id>", value: "#3B82F6" },
  { variableId: "VariableID:new:1", modeId: "<dark-mode-id>",  value: "#3B82F6" },
  ...
])
```

These are intentionally raw hex for now — they will be replaced with alias values during graduation.

### 6d. Save bridge state

Write `bridge-state.json` to track status per variable:

```json
{
  "tokens_collection_id": "VariableCollectionId:...",
  "mode_ids": {
    "light": "...",
    "dark": "...",
    "legacy": "..."
  },
  "variables": [
    {
      "new_name": "color/surface/brand",
      "variable_id": "VariableID:new:1",
      "status": "bridged",
      "legacy_alias": "VariableID:old:10",
      "light_alias": null,
      "dark_alias": null
    }
  ]
}
```

---

## Stage 7 — Rebind components

Rebind component layers from old token IDs to new token IDs. Work one component category at a time and validate visually before moving to the next.

Use `scripts/rebind_layer.js` via `figma_execute`. The script accepts a `componentNodeId` and a `mapping` object (`{ oldVarId: newVarId }`). Build the mapping from `bridge-mapping.json` and `bridge-state.json`.

**Per category:**
1. Run `rebind_layer.js` for each component set in the category
2. Capture a screenshot with `figma_take_screenshot`
3. Confirm visuals are unchanged before proceeding to next category

**Important:** Make sure the component's parent frame has the `Legacy` mode applied before rebinding — otherwise you're testing against the placeholder hex values, not the live old-token values.

```js
// Apply Legacy mode to the component's frame — run before rebinding
const frame = figma.getNodeById('<frame-or-page-id>');
const collection = figma.variables.getVariableCollectionById('<tokens-collection-id>');
frame.setExplicitVariableModeForCollection(collection, '<legacy-mode-id>');
```

---

## Stage 8 — Validate

After all components are rebound:

1. Switch the entire library page to Legacy mode; confirm everything looks identical to pre-migration
2. Run `token-audit` to check for any remaining direct old-token bindings on layers
3. Spot-check one component per category across all variant states
4. Check that switching a frame to Light mode shows expected placeholder values (same color, since Stage 6c used matching hex)

Report:
```
Bridge validation summary
─────────────────────────
Components rebound:   N component sets
Layers updated:       N layers
Still using old tokens directly: N layers (requires follow-up)
Legacy mode visual check: ✓ identical
```

Any layers still directly bound to old tokens (not through the bridge) should be listed. Decide whether to rebind them or leave them as known exceptions.

---

## Stage 9 — Graduation (when ready)

Graduation replaces the hex placeholders in Light/Dark modes with real aliases to new primitives. Do this token by token or category by category — not all at once.

### 9a. For each token being graduated

Update the Light and Dark mode values from hex placeholder → alias to new primitive:

```js
// via figma_execute — set real aliases for Light and Dark modes
const entries = [
  {
    varId: 'VariableID:new:1',
    lightAlias: 'VariableID:primitive:blue500',
    darkAlias:  'VariableID:primitive:blue600'
  }
];
const LIGHT_MODE = '<light-mode-id>';
const DARK_MODE  = '<dark-mode-id>';

for (const { varId, lightAlias, darkAlias } of entries) {
  const v = figma.variables.getVariableById(varId);
  v.setValueForMode(LIGHT_MODE, { type: 'VARIABLE_ALIAS', id: lightAlias });
  v.setValueForMode(DARK_MODE,  { type: 'VARIABLE_ALIAS', id: darkAlias });
}
return `Graduated ${entries.length} tokens`;
```

### 9b. Visual review before committing

After updating a category's Light/Dark aliases:
1. Switch the library page to Light mode
2. Take a screenshot — compare visually against Legacy mode
3. Confirm the new primitive values look correct
4. If something looks wrong, the Legacy mode is still intact — switch back and investigate

### 9c. Update bridge-state.json

Mark each graduated token:
```json
{
  "status": "graduated",
  "light_alias": "VariableID:primitive:blue500",
  "dark_alias":  "VariableID:primitive:blue600"
}
```

### 9d. Remove Legacy mode (final step)

Only after **all** tokens are graduated and the visual review is complete:

```js
const collection = figma.variables.getVariableCollectionById('<tokens-collection-id>');
collection.removeMode('<legacy-mode-id>');
```

**This is irreversible.** Confirm with the designer before running.

---

## Notes on risk

- Stages 1–6 are non-destructive: nothing existing is modified
- Stage 7 (rebinding) changes component layer bindings — recommend working on a branch or duplicate file
- Stage 9d (removing Legacy mode) is the only irreversible operation; run it last and only after full validation
- Never set raw hex values on component layers — always alias through the bridge variables
