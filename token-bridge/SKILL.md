---
name: token-bridge
description: Migrate component bindings from a legacy token system to a new semantic token structure with zero visual change. Creates a Legacy mode that aliases to an existing, untouched legacy token collection — so components can be rebound immediately and graduated to the new semantic system one category at a time. Use when migrating component bindings non-destructively, keeping old tokens as the live value source while adopting new names.
---

# Token Bridge

Bridges an existing legacy token collection to a new semantic token structure by adding a `Legacy` mode. Components are rebound to new token names immediately — in Legacy mode they still resolve to the old values via the untouched legacy collection. Graduation happens separately, per category.

The legacy collection is never modified. Light and dark modes live on the semantic (Tokens) collection and are bypassed entirely when Legacy mode is active.

---

> **Plugin API requirement**
> All `figma_execute` scripts must use the `Async` API variants exclusively:
> - `figma.variables.getLocalVariablesAsync()`
> - `figma.variables.getLocalVariableCollectionsAsync()`
> - `figma.getNodeByIdAsync(nodeId)`
>
> The synchronous forms (`getLocalVariables()`, `getLocalVariableCollections()`, `getNodeById()`) throw errors in the current plugin context (`documentAccess: dynamic-page`).

> **Variable ID safety**
> `figma_get_variables` and other MCP tools return IDs from a REST API cache that can differ from the real plugin API IDs. Use MCP tools for human-readable exploration only — **never** use their IDs for write operations (alias-setting, rebinding). Always source IDs used in `setValueForMode` or `setBoundVariable` from a `figma_execute` call that reads `getLocalVariablesAsync()` in the same session.

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
- The legacy token collection name (this will not be modified)
- The Tokens (semantic) collection and existing mode IDs
- Component categories and counts

Then build the full name→ID lookup for both the legacy and Tokens collections in a single `figma_execute` call:

```js
const allVars = await figma.variables.getLocalVariablesAsync();
const allColls = await figma.variables.getLocalVariableCollectionsAsync();

// Identify collections by name — update these to match your file
const LEGACY_COLL_NAME = 'REPLACE_WITH_LEGACY_COLLECTION_NAME';
const TOKENS_COLL_NAME = 'REPLACE_WITH_TOKENS_COLLECTION_NAME';

const legacyColl = allColls.find(c => c.name === LEGACY_COLL_NAME);
const tokensColl = allColls.find(c => c.name === TOKENS_COLL_NAME);

if (!legacyColl) throw new Error(`Legacy collection "${LEGACY_COLL_NAME}" not found`);
if (!tokensColl) throw new Error(`Tokens collection "${TOKENS_COLL_NAME}" not found`);

const legacyById  = {};
const tokensByName = {};

for (const v of allVars) {
  if (v.variableCollectionId === legacyColl.id) {
    legacyById[v.name] = v.id;
  }
  if (v.variableCollectionId === tokensColl.id) {
    tokensByName[v.name] = v.id;
  }
}

return {
  legacyCollectionId:  legacyColl.id,
  tokensCollectionId:  tokensColl.id,
  tokensModesIds:      tokensColl.modes,
  legacyCount:         Object.keys(legacyById).length,
  tokensCount:         Object.keys(tokensByName).length,
  legacyById,
  tokensByName,
};
```

Save the full output to `bridge-inventory.json`. Record:
- `legacyCollectionId`
- `tokensCollectionId`
- `tokensModesIds`
- `legacyById` — name→ID map for the legacy collection
- `tokensByName` — name→ID map for the Tokens collection

All subsequent stages that need variable IDs load from this file. Only re-run this `figma_execute` call if new variables are added mid-session.

---

## Stage 2 — Inventory legacy tokens

Get the full set of legacy tokens and their resolved values using the Variables API:

```js
const allVars = await figma.variables.getLocalVariablesAsync();
const allColls = await figma.variables.getLocalVariableCollectionsAsync();

// Use the collection ID from bridge-inventory.json
const LEGACY_COLLECTION_ID = 'REPLACE_WITH_LEGACY_COLLECTION_ID';

const legacyColl = allColls.find(c => c.id === LEGACY_COLLECTION_ID);
if (!legacyColl) throw new Error('Legacy collection not found');

const defaultModeId = legacyColl.defaultModeId;
const legacyVars = allVars.filter(v => v.variableCollectionId === LEGACY_COLLECTION_ID);

const inventory = legacyVars.map(v => {
  const val = v.valuesByMode[defaultModeId];
  const resolved = val?._a ? `alias → ${val._a}` : JSON.stringify(val);
  return { name: v.name, id: v.id, type: v.resolvedType, resolved };
});

return { count: inventory.length, inventory };
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

### Stage 2 exit check — skip Stage 3?

After the inventory, examine the naming patterns in both the legacy and new collections. If both collections use **component-prefixed names** (e.g. `button/primary/brand`, `input/border/default`) with enough context to determine semantic intent directly from the name, Stage 3 can be skipped.

**Skip Stage 3 if:**
- Legacy token names include the component and state context (e.g. `button/bg/hover`, `status/neutral/surface`)
- New token names follow the same component-level convention
- No ambiguity exists about which new token a legacy token maps to

Proceed to Stage 4 with a note: *"Stage 3 skipped — both collections use component-level naming, mapping built directly from names."*

**Run Stage 3 if:**
- Legacy tokens are visually grounded (e.g. `Primary`, `Blue-500`, `Brand`) and the correct new semantic name depends on which component is using the token
- Naming is ambiguous and requires inspecting component layers to determine correct mapping

---

## Stage 3 — Scan component bindings (batched)

> **Skip if** both collections use component-level naming (see Stage 2 exit check).

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
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const collection = collections.find(c => c.id === '<tokens-collection-id>');
if (!collection) throw new Error('Tokens collection not found');
const legacyModeId = collection.addMode('Legacy');
console.log('Legacy mode ID:', legacyModeId);
return { legacyModeId };
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
return { collectionId: collection.id, legacyModeId };
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

Record returned variable IDs in `bridge-state.json`. These are the authoritative IDs — use them in 6b, not IDs from `figma_get_variables`.

#### 6b. Set Legacy mode aliases → legacy collection

Set all aliases in a single `figma_execute` call. Build the MAP from `bridge-mapping.json` (legacy name → new semantic name). The name→ID lookups come from `bridge-inventory.json` (built in Stage 1) inlined into the script.

```js
// via figma_execute
const LEGACY_MODE_ID = 'REPLACE_WITH_LEGACY_MODE_ID';

// MAP: [ [new semantic token name, legacy token name], ... ]
// Inline all entries — no need to batch; a single call handles 400+ aliases
const MAP = [
  ['color/surface/action', 'Primary'],
  ['color/text/link',      'Primary'],
  // ... all entries from bridge-mapping.json
];

// Build name→ID lookups from the live plugin API (not MCP cache)
const allVars = await figma.variables.getLocalVariablesAsync();
const allColls = await figma.variables.getLocalVariableCollectionsAsync();

const TOKENS_COLL_ID = 'REPLACE_WITH_TOKENS_COLLECTION_ID';
const LEGACY_COLL_ID = 'REPLACE_WITH_LEGACY_COLLECTION_ID';

const newByName    = {};
const legacyByName = {};
for (const v of allVars) {
  if (v.variableCollectionId === TOKENS_COLL_ID) newByName[v.name]    = v;
  if (v.variableCollectionId === LEGACY_COLL_ID) legacyByName[v.name] = v;
}

let set = 0;
const errors = [];
for (const [newName, legName] of MAP) {
  const newVar    = newByName[newName];
  const legacyVar = legacyByName[legName];
  if (!newVar)    { errors.push(`New token not found: ${newName}`);    continue; }
  if (!legacyVar) { errors.push(`Legacy token not found: ${legName}`); continue; }
  newVar.setValueForMode(LEGACY_MODE_ID, { type: 'VARIABLE_ALIAS', id: legacyVar.id });
  set++;
}
return { set, errors };
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

Set all aliases in a single `figma_execute` call. Use the live plugin API for all IDs.

> **Name-collision warning:** If the component collection shares token names with the Tokens (semantic) collection (e.g. `text/primary`, `status/neutral/surface`), build two separate name→ID maps — one for pre-existing variables (`priorByName`) and one for the newly created component variables (`compByName`). Always resolve alias targets using `priorByName` first. Using a single merged map causes newly created variables to alias themselves, producing silent `#FFFFFF` failures.

```js
// via figma_execute
const LEGACY_MODE_ID  = 'REPLACE_WITH_COMPONENT_LEGACY_MODE_ID';
const COMP_COLL_ID    = 'REPLACE_WITH_COMPONENT_COLLECTION_ID';
const LEGACY_COLL_ID  = 'REPLACE_WITH_LEGACY_COLLECTION_ID';

// MAP: [ [component token name, legacy token name], ... ]
const MAP = [
  ['button/bg/primary',  'Primary'],
  ['link/text/default',  'Primary'],
  // ... all entries from bridge-mapping.json
];

const allVars = await figma.variables.getLocalVariablesAsync();

// Snapshot prior variables BEFORE the new component collection was created
// to avoid resolving alias targets to the newly created component variables.
const priorByName = {};   // semantic + legacy collections
const compByName  = {};   // component collection only
const legacyByName = {};  // legacy collection only

for (const v of allVars) {
  if (v.variableCollectionId === COMP_COLL_ID) {
    compByName[v.name] = v;
  } else {
    priorByName[v.name] = v;
    if (v.variableCollectionId === LEGACY_COLL_ID) legacyByName[v.name] = v;
  }
}

let set = 0;
const errors = [];
for (const [compName, legName] of MAP) {
  const compVar   = compByName[compName];
  const legacyVar = legacyByName[legName];
  if (!compVar)   { errors.push(`Component token not found: ${compName}`); continue; }
  if (!legacyVar) { errors.push(`Legacy token not found: ${legName}`);     continue; }
  compVar.setValueForMode(LEGACY_MODE_ID, { type: 'VARIABLE_ALIAS', id: legacyVar.id });
  set++;
}
return { set, errors };
```

Legacy mode aliases terminate at the legacy collection. The semantic layer (Tokens collection, light/dark modes) is not involved and cannot affect these values.

#### 6c. Set Light and Dark mode aliases → semantic tokens

**Pre-flight check:** Before running, count how many component token Value/Light/Dark mode entries are already correctly aliased to the Tokens collection:

```js
// via figma_execute — pre-flight check only, no writes
const COMP_COLL_ID   = 'REPLACE_WITH_COMPONENT_COLLECTION_ID';
const TOKENS_COLL_ID = 'REPLACE_WITH_TOKENS_COLLECTION_ID';
const LEGACY_MODE_ID = 'REPLACE_WITH_COMPONENT_LEGACY_MODE_ID';

const allVars = await figma.variables.getLocalVariablesAsync();
const allColls = await figma.variables.getLocalVariableCollectionsAsync();

const compColl = allColls.find(c => c.id === COMP_COLL_ID);
const nonLegacyModes = compColl.modes.filter(m => m.modeId !== LEGACY_MODE_ID);

const compVars = allVars.filter(v => v.variableCollectionId === COMP_COLL_ID);
const tokensVarIds = new Set(
  allVars.filter(v => v.variableCollectionId === TOKENS_COLL_ID).map(v => v.id)
);

let alreadySet = 0;
let missing = 0;
const gaps = [];

for (const v of compVars) {
  for (const mode of nonLegacyModes) {
    const val = v.valuesByMode[mode.modeId];
    if (val?.type === 'VARIABLE_ALIAS' && tokensVarIds.has(val.id)) {
      alreadySet++;
    } else {
      missing++;
      gaps.push({ token: v.name, mode: mode.name });
    }
  }
}

return { alreadySet, missing, sample: gaps.slice(0, 20) };
```

Only write aliases for the tokens reported as missing or incorrect. Do not overwrite already-correct values.

```js
// via figma_execute — write only missing aliases
const COMP_COLL_ID   = 'REPLACE_WITH_COMPONENT_COLLECTION_ID';
const TOKENS_COLL_ID = 'REPLACE_WITH_TOKENS_COLLECTION_ID';
const LEGACY_MODE_ID = 'REPLACE_WITH_COMPONENT_LEGACY_MODE_ID';

// MAP: [ [component token name, semantic token name], ... ]
// Include ONLY the tokens identified as missing in the pre-flight check
const MAP = [
  ['button/bg/primary',  'color/surface/action'],
  ['callout/bg/primary', 'color/surface/brand'],
  // ...
];

const allVars = await figma.variables.getLocalVariablesAsync();
const allColls = await figma.variables.getLocalVariableCollectionsAsync();

const compColl   = allColls.find(c => c.id === COMP_COLL_ID);
const nonLegacyModes = compColl.modes.filter(m => m.modeId !== LEGACY_MODE_ID);

const compByName    = {};
const semanticByName = {};
for (const v of allVars) {
  if (v.variableCollectionId === COMP_COLL_ID)   compByName[v.name]    = v;
  if (v.variableCollectionId === TOKENS_COLL_ID) semanticByName[v.name] = v;
}

let set = 0;
const errors = [];
for (const [compName, semanticName] of MAP) {
  const compVar     = compByName[compName];
  const semanticVar = semanticByName[semanticName];
  if (!compVar)     { errors.push(`Component token not found: ${compName}`);   continue; }
  if (!semanticVar) { errors.push(`Semantic token not found: ${semanticName}`); continue; }
  for (const mode of nonLegacyModes) {
    compVar.setValueForMode(mode.modeId, { type: 'VARIABLE_ALIAS', id: semanticVar.id });
  }
  set++;
}
return { set, errors };
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

> **Hand off to `token-migrate`**
> Use the **token-migrate** skill for this step. Pass it `bridge-mapping.json` as the source of old→new variable ID pairs. `token-migrate` handles layer scanning, batched rebinding, and visual validation per component category.
>
> `token-bridge` is complete once the bridge variables are created and aliases are set (Stage 6). Component layer rebinding is `token-migrate`'s responsibility.

---

## Stage 8 — Validate

After all components are rebound (via `token-migrate`):

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

Replace hex placeholders in Light/Dark modes with real aliases to new semantic tokens:

```js
// via figma_execute
const TOKENS_COLL_ID = 'REPLACE_WITH_TOKENS_COLLECTION_ID';
const LIGHT_MODE = '<light-mode-id>';
const DARK_MODE  = '<dark-mode-id>';

// MAP: [ [new token variable ID, semantic alias variable ID], ... ]
const entries = [
  { varId: 'VariableID:new:1', semanticAlias: 'VariableID:tokens:action' }
];

const allVars = await figma.variables.getLocalVariablesAsync();
const varsById = Object.fromEntries(allVars.map(v => [v.id, v]));

let updated = 0;
for (const { varId, semanticAlias } of entries) {
  const v = varsById[varId];
  if (!v) continue;
  v.setValueForMode(LIGHT_MODE, { type: 'VARIABLE_ALIAS', id: semanticAlias });
  v.setValueForMode(DARK_MODE,  { type: 'VARIABLE_ALIAS', id: semanticAlias });
  updated++;
}
return { updated };
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
// via figma_execute
const allColls = await figma.variables.getLocalVariableCollectionsAsync();
const collection = allColls.find(c => c.id === '<tokens-collection-id>');
collection.removeMode('<legacy-mode-id>');
```

**Option B:**
```js
// via figma_execute
// Delete the entire Component collection — removes Legacy mode and all component tokens
const allColls = await figma.variables.getLocalVariableCollectionsAsync();
const collection = allColls.find(c => c.id === '<component-collection-id>');
collection.remove();
```

**This is irreversible. Confirm with the designer before running.**

---

## Notes on risk

- Stages 1–6 are non-destructive: the legacy collection and Tokens collection are not modified (Option A adds a mode and new variables; Option B creates a new collection)
- Stage 7 (rebinding via `token-migrate`) changes component layer bindings — work on a branch or duplicate file
- Stage 9 removal is the only irreversible operation; run it last and only after full validation
- The legacy collection is never modified at any stage
- Never set raw hex values on component layers — always alias through the bridge variables
