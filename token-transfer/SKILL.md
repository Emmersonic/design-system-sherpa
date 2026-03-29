---
name: token-transfer
description: Copy or move a variable collection from one Figma file to another, with control over which collections to transfer and how to handle conflicts. Use this skill when someone wants to "copy variables between files", "move a collection to another file", "sync tokens from one file to another", "share variables across projects", or transfer part of a design system from a source file to a destination. Also use when someone says "transfer my tokens", "duplicate a collection to another file", or wants to consolidate multiple Figma files.
---

# Token Transfer

Copies a variable collection from a source Figma file into a target Figma file. Handles cross-file alias remapping, mode matching, and gives explicit control over conflict resolution.

**Transfer modes:**
- **overwrite** — Variables that exist in both files are updated to the source value. Variables in target but not in source are deleted (with confirmation).
- **merge** — Variables that exist in both are updated to the source value. Variables unique to the target are left untouched.
- **add** — Only variables that don't already exist in the target are added. Conflicts are skipped entirely.

---

## Prerequisites

- Both the source and target Figma files must be open and accessible via the `figma-console` MCP
- You know which collection(s) to transfer
- For alias integrity: if transferring semantic tokens that alias primitives, the primitives must already exist in the target file (or be included in the same transfer)

---

## Steps 1 & 2 — Read source and target (run in parallel)

Steps 1 and 2 are independent reads from different files — issue them at the same time.

---

## Step 1 — Read the source collection

Use `figma_execute` to read all source variables in a single call — faster than `figma_get_variables` for large collections as it runs inside Figma's plugin runtime without serialization overhead per variable.

```js
// figma_execute — run in source file context
const vars = await figma.variables.getLocalVariablesAsync();
const colls = await figma.variables.getLocalVariableCollectionsAsync();

// Filter to the target collection
const coll = colls.find(c => c.name === '<collection name>');
if (!coll) return { error: 'Collection not found', available: colls.map(c => c.name) };

const collVars = vars.filter(v => v.variableCollectionId === coll.id);

return {
  collection: {
    id: coll.id,
    name: coll.name,
    modes: coll.modes.map(m => ({ id: m.modeId, name: m.name })),
  },
  variables: collVars.map(v => ({
    id: v.id,
    name: v.name,
    type: v.resolvedType,
    description: v.description,
    valuesByMode: Object.fromEntries(
      coll.modes.map(m => [m.name, v.valuesByMode[m.modeId]])
    ),
  })),
};
```

If the collection name isn't known yet, run a cheap summary first:

```js
// figma_execute — list available collections
const colls = await figma.variables.getLocalVariableCollectionsAsync();
return colls.map(c => ({ name: c.name, modes: c.modes.map(m => m.name), variableCount: c.variableIds.length }));
```

For each variable in the response, record:
- ID, name, type (COLOR, FLOAT, STRING, BOOLEAN)
- Value per mode (raw value or alias — note whether it's a `VARIABLE_ALIAS` and the alias target's ID)
- Description

Also record each collection's mode names and IDs.

Save the source data to `transfer-source.json` using the normalized format:

```json
{
  "collection": {
    "id": "<source collection id>",
    "name": "Tokens",
    "modes": [
      { "id": "1:0", "name": "Light" },
      { "id": "1:1", "name": "Dark" }
    ]
  },
  "variables": [
    {
      "id": "VariableID:1:1",
      "name": "color/surface/brand",
      "type": "COLOR",
      "description": "",
      "valuesByMode": {
        "Light": { "type": "VARIABLE_ALIAS", "targetName": "color/blue/500" },
        "Dark":  { "type": "VARIABLE_ALIAS", "targetName": "color/blue/600" }
      }
    },
    {
      "id": "VariableID:2:1",
      "name": "color/blue/500",
      "type": "COLOR",
      "description": "",
      "valuesByMode": {
        "Default": { "r": 0.231, "g": 0.510, "b": 0.965, "a": 1.0 }
      }
    }
  ]
}
```

**Important:** Resolve alias IDs to names now (while you still have the source variable list). When `valuesByMode` contains a `VARIABLE_ALIAS`, look up the target variable by its ID and record its `name` as `targetName` instead of the raw ID. This is what enables remapping in the target file.

Present a summary to the user before continuing:

```
Source collection: Tokens
Modes: Light, Dark
Variables: 132 (84 aliases, 48 raw values)
```

---

## Step 2 — Read the target collection

Use `figma_execute` to fetch both the matching collection and a full name→ID inventory in one call (needed for alias remapping and conflict detection):

```js
// figma_execute — run in target file context
const vars = await figma.variables.getLocalVariablesAsync();
const colls = await figma.variables.getLocalVariableCollectionsAsync();

const coll = colls.find(c => c.name === '<collection name>');

return {
  // Full name→ID map for alias remapping (all variables in file, not just this collection)
  allVariables: Object.fromEntries(vars.map(v => [v.name, v.id])),

  // Matching collection data for conflict detection (null if not yet present)
  collection: coll ? {
    id: coll.id,
    name: coll.name,
    modes: coll.modes.map(m => ({ id: m.modeId, name: m.name })),
  } : null,
  variables: coll
    ? vars
        .filter(v => v.variableCollectionId === coll.id)
        .map(v => ({
          id: v.id,
          name: v.name,
          type: v.resolvedType,
          description: v.description,
          valuesByMode: Object.fromEntries(
            coll.modes.map(m => [m.name, v.valuesByMode[m.modeId]])
          ),
        }))
    : [],
};
```

One call returns everything needed: the conflict table and the alias remapping lookup.

**When to skip the target read:** If the target collection does **not** exist (fresh creation) and the source has no cross-collection aliases, skip the target read entirely — variable IDs will be available locally after creation (see Step 6). For updates to existing variables, the full read is always required.

**Fallback:** If using `figma_get_variables` instead of `figma_execute`, always use `verbosity: 'inventory'` — it returns names and IDs only (~95% smaller than `standard`), sufficient for building the alias remapping table.

Check whether a collection with the same name exists in the target.

Save the target state to `transfer-target.json` in the same normalized format.

Then build the conflict report:

```
Variable                      | Source value       | Target value       | Action
------------------------------|--------------------|--------------------|----------------
color/surface/brand           | → color/blue/500   | → color/teal/500   | conflict
color/surface/secondary       | → color/neutral/50 | (not in target)    | add
color/legacy/primary          | (not in source)    | → color/blue/500   | target-only
```

Counts:
- **Add:** N variables (in source, not in target)
- **Update (conflict):** N variables (in both, values differ)
- **Match:** N variables (in both, values identical — no action needed)
- **Target-only:** N variables (in target, not in source)

---

## Step 3 — Confirm transfer plan

Show the full plan and **stop**. Do not write anything until the user explicitly confirms.

```
Transfer plan
─────────────────────────────────────────────
Source: [file name]
Target: [file name]
Collection: Tokens
Mode: merge

Variables to add:    48  (new — will be created)
Variables to update: 12  (conflict — source value wins)
Variables to skip:   8   (conflict — target value kept)   ← add mode only
Variables to match:  64  (identical — no action)
Variables to delete: 0   (target-only — will be removed)  ← overwrite mode only

Modes
  Source: Light, Dark
  Target: Light, Dark
  → Match. No remapping needed.

  (or if modes differ:)
  Source: Light, Dark
  Target: Light, Dark, High Contrast
  → Target has extra mode "High Contrast". Transferred variables will have no
    value for this mode unless you specify a fallback.

Alias remapping
  84 variables use VARIABLE_ALIAS.
  → 81 alias targets found in target file by name. Will be remapped.
  → 3 alias targets NOT in target file:
       color/brand/vivid  (used by 2 variables)
       color/error/base   (used by 1 variable)
    These will be flagged as dangling aliases after transfer.
    Resolve by: (a) including them in this transfer, or (b) creating them first.
```

If there are dangling aliases, ask whether to:
1. Expand the transfer to include the missing alias targets
2. Proceed and resolve dangling aliases after transfer (Step 8)
3. Cancel and gather the missing variables first

Wait for explicit confirmation.

---

## Step 4 — Build transfer payloads

Use `--js-out` to generate `figma_execute`-ready scripts instead of batch JSON payloads. This produces far fewer Figma calls — each JS file does up to 150 creates/updates in one execution rather than one call per 50:

```bash
python "${CLAUDE_SKILL_DIR}/../scripts/build_transfer_payload.py" \
  transfer-source.json \
  transfer-target.json \
  --mode merge \
  --js-out transfer_execute.js
```

For a 600-variable collection this produces **4 JS files** instead of **24 batch API calls**.

The script outputs alongside the JS file(s):
- `transfer_plan.json` — full conflict table with per-variable actions
- `transfer_summary.json` — counts and dangling alias list
- `delete_ids.json` — variables to delete (overwrite mode only; requires confirmation)

Review `transfer_plan.json` to spot-check the plan before writing.

Set `collectionId` and `modeMap` in the `options` block of each generated file before running (values come from Step 5).

---

## Step 5 — Create or update the collection in the target

### 5a. If the collection doesn't exist in the target

```
figma_create_variable_collection(
  name: <collection name>,
  modes: [<mode names from source>]
)
```

Record the new collection ID and mode IDs.

### 5b. If the collection exists

Compare modes by name:
- Source modes missing from target → create them:
  ```
  figma_add_mode(collectionId: <target collection id>, name: <missing mode name>)
  ```
- Target modes missing from source → warn; transferred variables won't have values for those modes

---

## Step 6 — Execute the transfer

### 3-tier dependency model

Variables have three tiers with different resolution strategies:

| Tier | Type | Resolution |
|------|------|------------|
| 1 | Raw value variables (RGBA, numbers, strings) | No dependencies — create first |
| 2 | Cross-collection aliases | Depend on variables in *other* collections already in the target — look up by name from target inventory |
| 3 | Self-referential aliases | Depend on variables *within the same collection* — look up by name from the `nameToId` map built after creation |

The key insight: **create all variables first (no values), then set all values**. After creation, every variable has an ID in `nameToId`, so all three tiers resolve in the same value-setting pass — no separate passes per tier.

### Execution

Run each generated JS file in order via `figma_execute` (in the target file context). File 01 always contains raw-value variables; later files contain alias variables and updates.

```
figma_execute(code: <contents of transfer_execute_01.js>)
figma_execute(code: <contents of transfer_execute_02.js>)
...
```

Each call returns `{ created: N, updated: N, failed: N, failedDetails: [...] }`. Check `failedDetails` after each file before running the next.

The script registers each newly created variable in its local `nameToId` map immediately, so alias variables later in the same chunk can reference variables created earlier in the same chunk — including self-referential aliases (tier 3). No second-pass ID substitution needed.

**For overwrite — deleting target-only variables:**

List `delete_ids.json` and ask for explicit confirmation, then run:

```js
// figma_execute — bulk delete (run only after confirmed)
const ids = [/* paste from delete_ids.json */];
const allVars = await figma.variables.getLocalVariablesAsync();
const deleted = [];
for (const v of allVars) {
  if (ids.includes(v.id)) { v.remove(); deleted.push(v.name); }
}
return { deleted: deleted.length, names: deleted };
```

---

## Step 7 — Verify

Run verification in the target file:

1. **Count check** — re-fetch variables and confirm expected counts per collection
2. **Spot-check 3–5 variables** — verify name, type, value, and alias target are correct
3. **Broken alias scan:**

```js
// figma_execute — run in target file context
const allVars = await figma.variables.getLocalVariablesAsync();
const allIds = new Set(allVars.map(v => v.id));
const broken = [];
for (const v of allVars) {
  for (const [modeId, val] of Object.entries(v.valuesByMode)) {
    if (val?.type === 'VARIABLE_ALIAS' && !allIds.has(val.id)) {
      broken.push({ name: v.name, modeId, missingId: val.id });
    }
  }
}
return broken;
```

4. **Mode coverage** — confirm all transferred variables have values in all target modes (no empty slots)

Report:
- Variables created / updated / skipped / deleted
- Broken aliases (proceed to Step 8 if any)

---

## Step 8 — Resolve dangling aliases (if any)

Dangling aliases occur when a transferred variable points to a target that wasn't included in the transfer. For each one:

- **Target variable found by name in the target file** → the ID just needs remapping; fix via `figma_execute`
- **Target variable doesn't exist at all** → either:
  - Transfer the missing variable (re-run this skill for the missing ones)
  - Create it manually via `token-generate` + `token-push`
  - Set a raw fallback value temporarily and note it for follow-up

Present each case clearly and ask the user how to handle before making changes.

---

## Step 9 — Export portable manifest (optional)

After a successful transfer, export a portable name-based manifest. On future re-transfers to different files, load this manifest to skip Steps 1–3 entirely (the source hasn't changed).

```bash
python "${CLAUDE_SKILL_DIR}/../scripts/build_transfer_payload.py" \
  transfer-source.json \
  transfer-target.json \
  --mode merge \
  --export-manifest transfer-manifest.json
```

Manifest format (no file-specific IDs — portable across files):

```json
[
  {
    "collection": "semantic_next",
    "modes": ["Homebase Light", "Homebase Dark", "Clover Light"],
    "variables": [
      {
        "name": "brand/primary",
        "type": "COLOR",
        "description": "",
        "valuesByMode": {
          "Homebase Light": { "type": "VARIABLE_ALIAS", "targetName": "color/blue/600" },
          "Homebase Dark":  { "type": "VARIABLE_ALIAS", "targetName": "color/blue/400" }
        }
      }
    ]
  }
]
```

To use a manifest on a subsequent transfer, pass it as the source instead of re-reading the Figma file:

```bash
python "${CLAUDE_SKILL_DIR}/../scripts/build_transfer_payload.py" \
  transfer-manifest.json \
  transfer-target.json \
  --mode merge \
  --from-manifest
```

---

## Performance notes

- **Reads (Steps 1 & 2):** Run in parallel — both are independent reads from different files
- **Reads use `figma_execute`:** Runs inside Figma's plugin runtime in a single call; avoids serialization overhead of multiple `figma_get_variables` round-trips
- **Writes use `figma_execute` (Step 6):** 150 variables per execution vs 50 per batch API call; alias targets are available immediately after creation within the same call — no deferred ID substitution pass needed
- **For 600 variables:** ~4 `figma_execute` write calls vs ~24 batch API calls
- **Broken alias scan (Step 7):** Single `figma_execute` call — not per-variable

---

## Error handling

**"Variable name already exists"** — Conflict detection in Step 2 prevents this. If it still occurs, check for case or whitespace differences in names.

**"Mode not found"** — Mode IDs are always file-specific. Always remap by mode name. If mode names differ ("Light" vs "light"), flag for user confirmation before proceeding.

**"Alias target not found"** — Handled in Step 8. Never silently drop an alias or set it to null; always report it.

**"Rate limit / timeout"** — Reduce batch size to 25 and retry. The transfer is idempotent in merge/add mode — safe to restart from where it left off.

**"Collection doesn't exist in source"** — Re-check the collection name. Figma collection names are case-sensitive. List available collections from `figma_get_variables` output.
