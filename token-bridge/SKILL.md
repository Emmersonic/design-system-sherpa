---
name: token-bridge
description: Migrate component bindings from a legacy token system to a new semantic token structure with zero visual change. Creates a Legacy mode that aliases to an existing, untouched legacy token collection — so components can be rebound immediately and graduated to the new semantic system one category at a time. Use when migrating component bindings non-destructively, keeping old tokens as the live value source while adopting new names.
---

# Token Bridge

Bridges an existing legacy token collection to a new semantic token structure by adding a `Legacy` mode. Components are rebound to new token names immediately — in Legacy mode they still resolve to the old values via the untouched legacy collection. Graduation happens separately, per category.

The legacy collection is never modified. Light and dark modes live on the semantic (Tokens) collection and are bypassed entirely when Legacy mode is active.

---

## Step 0 — Clarify bridge level

**Before doing anything else, ask the designer:**

> The bridge can live at two levels. Which fits your situation?
>
> **A — Semantic collection**
> A `Legacy` mode is added to the existing Tokens collection. Each semantic token's Legacy mode value aliases to the corresponding old token in the legacy collection. Components bind directly to semantic tokens.
>
> ```
> component layer
>   → color/surface/action  (Tokens/Legacy mode)
>   → legacy/Primary        (legacy collection, untouched)
>   → #3B82F6
> ```
>
> Best when: old tokens had fairly consistent semantic meaning and the new names map cleanly to them. Simpler, fewer variables.
>
> **B — Component collection**
> A new component token collection is created with a `Legacy` mode. Each component token's Legacy mode aliases directly to the legacy collection, bypassing the semantic layer. Light and dark mode values alias to the correct semantic token per component context.
>
> ```
> component layer
>   → button/bg/primary  (Component collection/Legacy mode)
>   → legacy/Primary     (legacy collection, untouched)
>   → #3B82F6
>
> component layer
>   → button/bg/primary  (Component collection/Light or Dark — resolved via Tokens collection)
>   → color/surface/action
> ```
>
> Best when: old tokens were visually grounded (one token used in multiple semantically distinct contexts across components), so the correct new semantic token varies by component. More variables, but each component expresses its own semantic intent.
>
> **Which fits your system?**

Save the answer. All stages from Stage 5 onwards branch based on this choice.

---

## Prerequisites

- A confirmed `foundation.md` from `token-foundation`
- `scaffold-state.json` from `token-figma-scaffold` (collection and mode IDs)
- A Figma library file open and connected via `figma-console` MCP
- The legacy token collection still present in the file (untouched)

---

## Stage 1 — Orient

```
figma_get_design_system_summary()
```

Confirms which collections exist. Identify:
- The legacy token collection name and ID (this will not be modified)
- The Tokens (semantic) collection ID and existing mode IDs
- Component categories and counts (used for batching in Stage 3)

Also fetch all variables to build the ID→name lookup. Use `verbosity: "inventory"` to get names and IDs only (~95% smaller than full) — sufficient for building the mapping table:

```
figma_get_variables(fileUrl: <current file>, verbosity: "inventory")
```

Save to `bridge-inventory.json`. Record legacy collection ID, Tokens collection ID, and all existing mode IDs.

---

## Stage 2 — Inventory legacy tokens

Get the full set of legacy tokens and their resolved values.

```
figma_get_token_values(type: "colors", limit: 50)
figma_get_token_values(type: "spacing", limit: 50)
```

Produce a table:

```
Legacy token name    | ID                  | Type   | Resolved value
---------------------|---------------------|--------|---------------
Primary              | VariableID:1:10     | COLOR  | #3B82F6
Text/Default         | VariableID:1:11     | COLOR  | #111827
Background           | VariableID:1:12     | COLOR  | #FFFFFF
Spacing/Base         | VariableID:1:20     | FLOAT  | 16
```

This is the lookup used when building aliases in Stage 6.

---

## Stage 3 — Scan component bindings (batched)

Scan what legacy tokens are used on, and in what context. Work in batches of 25 component sets.

### 3a. Enumerate component sets

```
figma_get_library_components(libraryFileUrl: <current file>, limit: 25, offset: 0)
```

### 3b. Analyse each component set

```
figma_analyze_component_set(nodeId: <componentSetNodeId>)
```

Extract the token names referenced in fill/stroke/text fields. Cross-reference against `bridge-inventory.json` to resolve to legacy token IDs.

### 3c. Fallback for standalone components and spacing/radius

Run `scripts/scan_standalone.js` via `figma_execute` for standalone `COMPONENT` nodes and spacing/radius bindings.

### 3d. Save each batch

Write results to `bridge-scan-[n].json`:

```json
{
  "batch": 1,
  "offset": 0,
  "scanned": 25,
  "usage": {
    "VariableID:1:10": {
      "name": "Primary",
      "usedAs": {
        "fill":     ["Button", "Badge"],
        "textFill": ["Link"]
      }
    }
  }
}
```

### 3e. Confirm after the first batch

**Stop after batch 1.** Present a partial mapping preview and ask:
1. Do the proposed new names look right for these components?
2. Any tokens used in contexts you didn't expect?
3. Any tokens to exclude from bridging?

**Do not continue until confirmed.**

### 3f. Continue remaining batches

Increment offset by 25 and repeat until all component sets are covered. Aggregate results into a single running object.

---

## Stage 4 — Build the mapping table

### Option A — Semantic-level bridge

Aggregate all scan results. For each legacy token, use its actual usage context to propose the new semantic name.

**Decision rules:**
- Used only as fills on containers → `color/surface/[intent]`
- Used only on text nodes → `color/text/[intent]`
- Used as fills AND text → **split into two new semantic tokens**
- Used as a stroke → `color/border/[intent]`
- Used on both interactive and neutral elements → flag for designer input

```
Legacy token    | Usage context         | Proposed semantic name        | Split? | Confidence
----------------|-----------------------|-------------------------------|--------|------------
Primary         | fill: Button, Badge   | color/surface/action          | No     | High
Primary         | textFill: Link        | color/text/link               | Yes    | High
Text/Default    | textFill: all text    | color/text/primary            | No     | High
Background      | fill: surfaces        | color/surface/default         | No     | High
```

### Option B — Component-level bridge

For each component, map each legacy token binding to both:
1. The new component token name (used in the component collection)
2. The correct semantic token for that component's context (used in Light/Dark modes)

```
Component       | Legacy token  | New component token            | Semantic alias (Light/Dark)
----------------|---------------|--------------------------------|-----------------------------
Button          | Primary       | button/bg/primary              | color/surface/action
Callout         | Primary       | callout/bg/primary             | color/surface/brand
Link            | Primary       | link/text/default              | color/text/link
Input           | Border        | input/border/default           | color/border/default
```

The same legacy token mapping to different semantic tokens across components is expected and correct.

---

**Stop here.** Present the full table and ask:
1. Are the proposed names correct?
2. Any splits (Option A) or per-component divergences (Option B) to adjust?
3. Any Low-confidence rows to resolve?
4. Any tokens to exclude?

**Do not proceed to Stage 5 until explicitly approved.** Save the approved table to `bridge-mapping.json`.

---

## Stage 5 — Add the Legacy mode

### Option A — Add Legacy mode to the Tokens collection

```js
// via figma_execute
const collection = figma.variables.getVariableCollectionById('<tokens-collection-id>');
const legacyModeId = collection.addMode('Legacy');
console.log('Legacy mode ID:', legacyModeId);
```

Update `scaffold-state.json`:

```json
{
  "mode_ids": {
    "light":  "<existing-id>",
    "dark":   "<existing-id>",
    "legacy": "<new-legacy-mode-id>"
  }
}
```

### Option B — Create the Component token collection

```js
// via figma_execute
const collection = figma.variables.createVariableCollection('Components');
const legacyModeId = collection.addMode('Legacy');
// Rename the default mode if one was created automatically
console.log('Collection ID:', collection.id, 'Legacy mode ID:', legacyModeId);
```

Save to `bridge-state.json`:

```json
{
  "bridge_level": "component",
  "component_collection_id": "<new-collection-id>",
  "tokens_collection_id": "<existing-tokens-collection-id>",
  "mode_ids": {
    "component_legacy": "<new-legacy-mode-id>"
  }
}
```

---

## Stage 6 — Create bridge variables and set aliases

### Option A — Create semantic variables with Legacy mode aliases

#### 6a. Create variable shells in the Tokens collection

```
figma_batch_create_variables(
  collectionId: <tokens-collection-id>,
  variables: [
    { name: "color/surface/action", resolvedType: "COLOR" },
    { name: "color/text/link",      resolvedType: "COLOR" },
    ...
  ]
)
```

Record returned variable IDs in `bridge-state.json`.

#### 6b. Set Legacy mode aliases → legacy collection

```js
// via figma_execute — batches of 50
const LEGACY_MODE_ID = 'REPLACE';
const entries = [
  { newVarId: 'VariableID:new:1', oldVarId: 'VariableID:legacy:10' },
  ...
];

for (const { newVarId, oldVarId } of entries) {
  const v = figma.variables.getVariableById(newVarId);
  v.setValueForMode(LEGACY_MODE_ID, { type: 'VARIABLE_ALIAS', id: oldVarId });
}
return `Set ${entries.length} Legacy aliases`;
```

#### 6c. Set placeholder values for Light and Dark modes

New variables must have a value in every mode. Use the resolved hex value as a placeholder until graduation:

```
figma_batch_update_variables(updates: [
  { variableId: "VariableID:new:1", modeId: "<light-mode-id>", value: "#3B82F6" },
  { variableId: "VariableID:new:1", modeId: "<dark-mode-id>",  value: "#3B82F6" },
  ...
])
```

These hex values are replaced with semantic aliases during Stage 9 graduation.

---

### Option B — Create component tokens with Legacy and semantic aliases

#### 6a. Create variable shells in the Component collection

```
figma_batch_create_variables(
  collectionId: <component-collection-id>,
  variables: [
    { name: "button/bg/primary",   resolvedType: "COLOR" },
    { name: "callout/bg/primary",  resolvedType: "COLOR" },
    { name: "link/text/default",   resolvedType: "COLOR" },
    ...
  ]
)
```

#### 6b. Set Legacy mode aliases → legacy collection (direct, bypasses semantic layer)

```js
// via figma_execute — batches of 50
const LEGACY_MODE_ID = 'REPLACE';
const entries = [
  { compVarId: 'VariableID:comp:1', legacyVarId: 'VariableID:legacy:10' },
  ...
];

for (const { compVarId, legacyVarId } of entries) {
  const v = figma.variables.getVariableById(compVarId);
  v.setValueForMode(LEGACY_MODE_ID, { type: 'VARIABLE_ALIAS', id: legacyVarId });
}
return `Set ${entries.length} Legacy aliases`;
```

Legacy mode aliases terminate at the legacy collection. The semantic layer (Tokens collection, light/dark modes) is not involved and cannot affect these values.

#### 6c. Set Light and Dark mode aliases → semantic tokens

Unlike Option A, there are no hex placeholders. Each component token's Light/Dark value is the correct semantic token for that component's context, as determined in Stage 4:

```js
// via figma_execute — batches of 50
// Light and Dark both point to the same semantic token;
// the Tokens collection's own light/dark modes handle the actual value difference.
const entries = [
  { compVarId: 'VariableID:comp:1', semanticVarId: 'VariableID:tokens:action' },  // button/bg/primary → color/surface/action
  { compVarId: 'VariableID:comp:2', semanticVarId: 'VariableID:tokens:brand'  },  // callout/bg/primary → color/surface/brand
  ...
];

// Set for all non-legacy modes on the component collection
const compCollection = figma.variables.getVariableCollectionById('<component-collection-id>');
const nonLegacyModes = compCollection.modes.filter(m => m.name !== 'Legacy');

for (const { compVarId, semanticVarId } of entries) {
  const v = figma.variables.getVariableById(compVarId);
  for (const mode of nonLegacyModes) {
    v.setValueForMode(mode.modeId, { type: 'VARIABLE_ALIAS', id: semanticVarId });
  }
}
return `Set ${entries.length} semantic aliases`;
```

#### 6d. Save bridge state

```json
{
  "bridge_level": "component",
  "component_collection_id": "VariableCollectionId:...",
  "tokens_collection_id": "VariableCollectionId:...",
  "mode_ids": {
    "component_legacy": "..."
  },
  "variables": [
    {
      "component_token":  "button/bg/primary",
      "variable_id":      "VariableID:comp:1",
      "legacy_alias":     "VariableID:legacy:10",
      "semantic_alias":   "VariableID:tokens:action",
      "status":           "bridged"
    }
  ]
}
```

---

## Stage 7 — Rebind components

Rebind component layers from legacy token IDs to new token IDs. Work one component category at a time and validate visually after each.

Use `scripts/rebind_layer.js` via `figma_execute`. Build the `mapping` object (`{ oldVarId: newVarId }`) from `bridge-mapping.json` and `bridge-state.json`.

Before rebinding each category, ensure the component's parent frame has Legacy mode applied:

```js
// Option A: apply Legacy mode on the Tokens collection
const frame = figma.getNodeById('<frame-or-page-id>');
const tokensCollection = figma.variables.getVariableCollectionById('<tokens-collection-id>');
frame.setExplicitVariableModeForCollection(tokensCollection, '<legacy-mode-id>');

// Option B: apply Legacy mode on the Component collection
const frame = figma.getNodeById('<frame-or-page-id>');
const compCollection = figma.variables.getVariableCollectionById('<component-collection-id>');
frame.setExplicitVariableModeForCollection(compCollection, '<component-legacy-mode-id>');
```

Per category:
1. Run `rebind_layer.js` for each component set in the category
2. Capture a screenshot with `figma_take_screenshot`
3. Confirm visuals are unchanged before moving to the next category

---

## Stage 8 — Validate

After all components are rebound:

1. Switch the entire library page to Legacy mode; confirm everything looks identical to the original
2. Run `token-audit` to check for any remaining direct legacy-token bindings on component layers
3. Spot-check one component per category across all variant states

Report:

```
Bridge validation summary
─────────────────────────
Bridge level:                 semantic | component
Components rebound:           N component sets
Layers updated:               N layers
Still using legacy directly:  N layers (requires follow-up)
Legacy mode visual check:     ✓ identical
```

---

## Stage 9 — Graduation (when ready)

### Option A

Replace hex placeholders in Light/Dark modes with real aliases to new semantic tokens (which in turn alias to new primitives via the Tokens collection):

```js
const entries = [
  { varId: 'VariableID:new:1', semanticAlias: 'VariableID:tokens:action' }
];
const LIGHT_MODE = '<light-mode-id>';
const DARK_MODE  = '<dark-mode-id>';

for (const { varId, semanticAlias } of entries) {
  const v = figma.variables.getVariableById(varId);
  v.setValueForMode(LIGHT_MODE, { type: 'VARIABLE_ALIAS', id: semanticAlias });
  v.setValueForMode(DARK_MODE,  { type: 'VARIABLE_ALIAS', id: semanticAlias });
}
```

After each category: switch to Light mode, take a screenshot, compare against Legacy mode, confirm.

### Option B

Semantic aliases were set in Stage 6c. Graduation is a review step, not an alias-swap:

1. Switch to Light mode — confirm each component looks correct with the semantic token values
2. Fix any incorrect semantic aliases found during review (update `bridge-state.json` and re-run Stage 6c for affected tokens)
3. Once all components look correct in Light and Dark, the bridge is ready to close

### Remove Legacy mode (final step, both options)

Only after all tokens are graduated and all visual reviews pass:

**Option A:**
```js
const collection = figma.variables.getVariableCollectionById('<tokens-collection-id>');
collection.removeMode('<legacy-mode-id>');
```

**Option B:**
```js
// Delete the entire Component collection — removes Legacy mode and all component tokens
const collection = figma.variables.getVariableCollectionById('<component-collection-id>');
collection.remove();
```

**This is irreversible. Confirm with the designer before running.**

---

## Notes on risk

- Stages 1–6 are non-destructive: the legacy collection and Tokens collection are not modified (Option A adds a mode and new variables; Option B creates a new collection)
- Stage 7 (rebinding) changes component layer bindings — work on a branch or duplicate file
- Stage 9 removal is the only irreversible operation; run it last and only after full validation
- The legacy collection is never modified at any stage
- Never set raw hex values on component layers — always alias through the bridge variables
