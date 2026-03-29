---
name: token-repair-aliases
description: Scan all Figma variable collections for broken aliases (pointing to non-existent variable IDs), group them by missing target, infer likely replacements, and apply confirmed fixes. Use this skill after deleting or renaming variables, after a namespace consolidation, or whenever broken aliases are suspected. Also use when someone says "fix broken aliases", "repair tokens", or "scan for missing alias targets".
---

# Token Repair Aliases

Finds and fixes broken variable aliases across all collections in a connected Figma file. A broken alias is a variable whose value in one or more modes points to a variable ID that no longer exists.

This is common after:
- Deleting variables or entire namespaces
- Renaming variables (which creates new IDs in Figma)
- Namespace consolidations (merging multiple groups into one)
- Failed or partial push operations

---

## Prerequisites

- A Figma file open and connected via the Figma MCP (`figma-console`)
- Optionally, `scaffold-state.json` for known variable IDs

---

## Step 1 — Scan for broken aliases

Use `figma_execute` to scan all variables for aliases pointing to non-existent IDs:

```js
// figma_execute — full broken alias scan
const allVars = await figma.variables.getLocalVariablesAsync();
const allIds = new Set(allVars.map(v => v.id));
const idToName = new Map(allVars.map(v => [v.id, v.name]));

const broken = [];
for (const v of allVars) {
  const col = await figma.variables.getVariableCollectionByIdAsync(v.variableCollectionId);
  for (const [modeId, value] of Object.entries(v.valuesByMode)) {
    if (value && typeof value === 'object' && value.type === 'VARIABLE_ALIAS') {
      if (!allIds.has(value.id)) {
        const modeName = col.modes.find(m => m.modeId === modeId)?.name || modeId;
        broken.push({
          name: v.name,
          variableId: v.id,
          collection: col.name,
          mode: modeName,
          modeId: modeId,
          missingId: value.id
        });
      }
    }
  }
}
return { total: broken.length, broken };
```

Report the total count and group by missing ID.

---

## Step 2 — Group and analyze

Group broken aliases by the missing variable ID. For each missing ID:

1. **Count** how many aliases point to it
2. **List** all affected variable names and which modes are broken
3. **Infer likely target** from the variable names and namespace patterns

Present a grouped summary:

```
Missing ID: VariableID:123:456
  Likely was: color/blue/500 (inferred from alias names)
  Affected aliases (3):
    - color/surface/brand (Light mode)
    - button/background/primary/default (Light mode)
    - badge/background/info/default (Light mode)
```

---

## Step 3 — Build repair mapping

For each missing ID, propose a replacement variable:

**Inference strategies (in order of reliability):**
1. **Name match** — search existing variables for one with the same name as the inferred missing variable
2. **Namespace match** — if the variable was renamed/moved, look for variables in the same namespace with similar suffixes
3. **Value match** — if the original hex/number value is known (from a proposal file or scaffold-state.json), find a variable with the same resolved value
4. **Manual** — if no match can be inferred, flag for designer input

Present the repair mapping as a table:

```
Missing ID              | Inferred name       | Proposed replacement        | Confidence
------------------------|---------------------|-----------------------------|------------
VariableID:123:456      | color/blue/500      | color/blue/500 (ID:789:012) | High
VariableID:123:457      | color/red/old        | color/feedback/danger       | Medium
VariableID:123:458      | (unknown)            | — needs designer input —    | None
```

**Stop here and get designer approval before applying any fixes.**

---

## Step 4 — Apply confirmed fixes

For each approved repair, update the alias to point to the new variable ID:

```js
// figma_execute — repair one alias
const variable = await figma.variables.getVariableByIdAsync(VARIABLE_ID);
variable.setValueForMode(MODE_ID, {
  type: 'VARIABLE_ALIAS',
  id: NEW_TARGET_ID
});
```

Process repairs in batches of 20–30 to avoid timeouts. After each batch, report progress.

---

## Step 5 — Verify

After all repairs are applied, re-run the Step 1 scan to confirm zero broken aliases remain.

Also run the standard verification:
1. **Re-fetch variable counts** — confirm no variables were accidentally deleted
2. **Spot-check repaired aliases** — pick 3–5 repaired tokens and verify they resolve to the correct value
3. **Test mode switching** — switch between modes in Figma to confirm repaired aliases display correctly

Report the final state to the designer.

---

## Step 6 — Update state files

If `scaffold-state.json` exists, update the `variable_ids` map with any new or corrected IDs discovered during repair.

If any `token-proposal-[category].json` files reference the old variable IDs in their `figma_ids.variable_ids` section, update those as well.
