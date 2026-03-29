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

## Step 1 — Read the source collection

Use `format: 'filtered'` with the collection name and `verbosity: 'standard'` to fetch only the target collection. For large libraries this is significantly faster than pulling everything.

```
figma_get_variables(
  fileUrl: <source file>,
  format: "filtered",
  collection: "<collection name>",
  verbosity: "standard"
)
```

If the collection name isn't known yet, run a cheap summary first to list available collections (no variable data):

```
figma_get_variables(fileUrl: <source file>, format: "summary")
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

Fetch the matching collection from the target file using the same filtered approach. Also fetch a name → ID inventory of all variables in the target file (needed for alias remapping):

```
# Fetch the matching collection for conflict detection
figma_get_variables(
  fileUrl: <target file>,
  format: "filtered",
  collection: "<collection name>",
  verbosity: "standard"
)

# Fetch all variable names + IDs across the whole file for alias remapping
figma_get_variables(
  fileUrl: <target file>,
  format: "filtered",
  verbosity: "inventory"
)
```

`verbosity: "inventory"` returns names and IDs only (~95% smaller than full) — sufficient for building the alias remapping table without loading all values.

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

Use the helper script to build batch-ready payloads:

```bash
python "${CLAUDE_SKILL_DIR}/../scripts/build_transfer_payload.py" \
  transfer-source.json \
  transfer-target.json \
  --mode merge \
  --out transfer-payloads/
```

The script outputs:
- `transfer_plan.json` — full conflict table with per-variable actions
- `create_batch_NN.json` — variables to create (chunked at 50)
- `update_batch_NN.json` — variables to update (values + aliases, chunked at 50)
- `delete_batch_NN.json` — variables to delete (overwrite mode only; requires separate confirmation)
- `transfer_summary.json` — counts and dangling alias list

Review `transfer_plan.json` to spot-check the plan before writing.

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

Process in dependency order to respect alias chains:

**Pass 1 — Raw values first** (no aliases; safe to create in any order)

```
figma_batch_create_variables([
  { collectionId: <target collection id>, name: "color/blue/500", type: "COLOR" },
  ...up to 50 per call
])
```

Then set their values:

```
figma_batch_update_variables([
  { variableId: <new id>, modeId: <mode id>, value: { r: 0.231, g: 0.510, b: 0.965, a: 1.0 } },
  ...
])
```

**Pass 2 — Alias variables** (must run after all raw-value variables exist)

Create first (no value set yet):

```
figma_batch_create_variables([
  { collectionId: <target collection id>, name: "color/surface/brand", type: "COLOR" },
  ...
])
```

Then set aliases using remapped IDs:

```
figma_batch_update_variables([
  { variableId: <new id>, modeId: <light mode id>, value: { type: "VARIABLE_ALIAS", id: <target id of color/blue/500> } },
  { variableId: <new id>, modeId: <dark mode id>,  value: { type: "VARIABLE_ALIAS", id: <target id of color/blue/600> } },
  ...
])
```

**For overwrite/merge — updating existing variables:**

Use existing target variable IDs (no creation needed):

```
figma_batch_update_variables([
  { variableId: <existing target id>, modeId: <mode id>, value: <source value or remapped alias> },
  ...
])
```

Report progress after each batch: `[Pass 1: 48/48 raw values written] [Pass 2: 24/84 aliases written]`

**For overwrite — deleting target-only variables:**

List them explicitly and ask for a final confirmation before deleting. Delete one at a time via `figma_delete_variable` or via `figma_execute` for bulk deletion.

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

- **Target variable found by name in the target file** → the ID just needs remapping; fix with `figma_batch_update_variables`
- **Target variable doesn't exist at all** → either:
  - Transfer the missing variable (re-run this skill for the missing ones)
  - Create it manually via `token-generate` + `token-push`
  - Set a raw fallback value temporarily and note it for follow-up

Present each case clearly and ask the user how to handle before making changes.

---

## Performance notes

- Variables are transferred in batches of 50 per call
- Alias ID remapping is done locally in the script before any API calls — no per-variable round-trips
- For collections of 200+ variables, expect 4–10 batch calls total
- The broken alias scan is a single `figma_execute` call — not per-variable

---

## Error handling

**"Variable name already exists"** — Conflict detection in Step 2 prevents this. If it still occurs, check for case or whitespace differences in names.

**"Mode not found"** — Mode IDs are always file-specific. Always remap by mode name. If mode names differ ("Light" vs "light"), flag for user confirmation before proceeding.

**"Alias target not found"** — Handled in Step 8. Never silently drop an alias or set it to null; always report it.

**"Rate limit / timeout"** — Reduce batch size to 25 and retry. The transfer is idempotent in merge/add mode — safe to restart from where it left off.

**"Collection doesn't exist in source"** — Re-check the collection name. Figma collection names are case-sensitive. List available collections from `figma_get_variables` output.
