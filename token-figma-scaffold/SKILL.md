---
name: token-figma-scaffold
description: Set up the Figma variable collections, modes, and folder structure for a design token system. Use this skill after token-foundation is complete, when someone is ready to create the actual Figma file structure for their tokens — including creating collections, configuring modes (light/dark), setting variable visibility and publishing rules. Also use when someone asks how to set up Figma variables for a design system, or wants to create the token infrastructure in Figma before generating any tokens.
---

# Token Figma Scaffold

Creates the Figma variable collections, modes, and settings needed before any tokens are generated. Run this after `token-foundation` has produced a confirmed `foundation.md`.

This skill uses the Figma MCP tools to execute directly in a connected Figma file.

---

## Prerequisites

- A confirmed `foundation.md` from the `token-foundation` skill
- A Figma file open and connected via the Figma MCP (`figma-console`)
- The file should be a dedicated design system library file, not a product design file

---

## Step 1 — Read the foundation document

Read `foundation.md` and extract:
- Which tiers are needed (primitive + semantic, or all three)
- Which modes are required (e.g. light + dark)
- Which categories are in scope

---

## Step 2 — Check what already exists

Use `figma_get_variables` to inspect the current file state:

```
figma_get_variables(fileUrl: <current file>)
```

Report to the designer:
- Which collections already exist
- Which modes already exist
- Any naming conflicts with the planned structure

If collections already exist that match the plan, confirm whether to reuse or replace them before proceeding.

---

## Step 3 — Create collections

### 3a. Primitives collection

Create the `Primitives` collection with a single mode:

```
figma_create_variable_collection(
  name: "Primitives",
  modes: ["Value"]
)
```

After creation, configure visibility using `figma_execute` with the Plugin API (the `figma_create_variable_collection` tool cannot set `hiddenFromPublishing`):

```js
// figma_execute — hiddenFromPublishing must be set via Plugin API
const col = await figma.variables.getVariableCollectionByIdAsync(COLLECTION_ID);
col.hiddenFromPublishing = true;
```

This prevents primitives from being selectable in the properties panel.

### 3b. Tokens collection

Create the `Tokens` collection with one mode per theme from `foundation.md`:

```
figma_create_variable_collection(
  name: "Tokens",
  modes: ["Light", "Dark"]   ← adjust based on foundation.md
)
```

If additional modes are needed (brand themes, density), add them now:

```
figma_add_mode(
  collectionId: <tokens collection id>,
  name: "High Contrast"
)
```

**Warning — mode renames:** Before renaming any mode, confirm that no external config (Supernova, Style Dictionary, etc.) references this mode by name. Renaming modes will silently break export pipelines that match on mode name strings.

### 3c. Components collection (optional)

Only create if `foundation.md` specifies component tokens in a separate collection:

```
figma_create_variable_collection(
  name: "Components",
  modes: ["Light", "Dark"]
)
```

---

## Figma Variable API requirements

### Async API only

The synchronous variable API methods throw in the current plugin context. Always use the async versions:

| Do NOT use (throws) | Use instead |
|---|---|
| `figma.variables.getLocalVariableCollections()` | `figma.variables.getLocalVariableCollectionsAsync()` |
| `figma.variables.getLocalVariables()` | `figma.variables.getLocalVariablesAsync()` |
| `figma.variables.getVariableCollectionById(id)` | `figma.variables.getVariableCollectionByIdAsync(id)` |
| `figma.variables.getVariableById(id)` | `figma.variables.getVariableByIdAsync(id)` |

### createVariable requires a collection object, not an ID string

Passing a collection ID string to `createVariable()` throws: `"Cannot call createVariable with a collection id in incremental mode."`

Always fetch the collection object first:

```js
// figma_execute
const col = await figma.variables.getVariableCollectionByIdAsync(COLLECTION_ID);
const variable = figma.variables.createVariable("color/blue/500", col, "COLOR");
```

### Capture variable IDs inline at creation

Don't re-query after creation — capture the returned ID immediately and save it to `scaffold-state.json`:

```js
// figma_execute
const col = await figma.variables.getVariableCollectionByIdAsync(COLLECTION_ID);
const variable = figma.variables.createVariable(name, col, type);
state.variables[name] = variable.id; // capture immediately
```

---

## Step 4 — Verify the structure

After creating collections, run a structured verification (required for all Figma-writing skills):

1. **Re-fetch variable counts** — use `figma_get_variables` to confirm the expected number of collections and modes exist
2. **Spot-check properties** — use `figma_browse_tokens` to confirm:
   - Collection names and mode names match the plan
   - `Primitives` is hidden from publishing
   - `Tokens` has the right number of modes
3. **Confirm no broken aliases** — if any variables were created with alias values, verify alias targets resolve

---

## Step 5 — Report and hand off

Tell the designer:
- What was created
- What the collection IDs and mode IDs are

Save these IDs to `scaffold-state.json` in the working directory — downstream skills (`token-push`, `token-generate`) will read collection and mode IDs from here instead of re-fetching them each time:

```json
{
  "figma_file_url": "<file url>",
  "collection_ids": {
    "primitives": "<id>",
    "tokens": "<id>",
    "components": "<id or null>"
  },
  "mode_ids": {
    "light": "<id>",
    "dark": "<id>"
  }
}
```

Tell the designer: the scaffold is ready; next step is `token-generate` to populate tokens by category.

For the canonical format of `scaffold-state.json`, see `references/scaffold-state-schema.json`.

---

## Post-deletion alias scan

After deleting variables or renaming namespaces, always run a verification step to check for broken aliases in other collections:

```js
// figma_execute — scan for broken aliases
const allVars = await figma.variables.getLocalVariablesAsync();
const allIds = new Set(allVars.map(v => v.id));
const broken = [];
for (const v of allVars) {
  for (const [modeId, value] of Object.entries(v.valuesByMode)) {
    if (value && typeof value === 'object' && value.type === 'VARIABLE_ALIAS') {
      if (!allIds.has(value.id)) {
        broken.push({ name: v.name, modeId, missingId: value.id });
      }
    }
  }
}
return broken;
```

Report any broken aliases to the designer before the session ends. Use `token-repair-aliases` for large-scale repair work.

---

## Troubleshooting

**"Not connected to Figma"** — Check that a Figma file is open in Figma Desktop and the MCP bridge plugin is running. Use `figma_get_status` to verify.

**"Collection already exists"** — Do not duplicate. Either reuse the existing collection (if the name and mode structure match) or rename the existing one before creating the new one.

**"Cannot set hiddenFromPublishing"** — Use `figma_execute` with the async Plugin API to set this property directly:
```js
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const primitives = collections.find(c => c.name === 'Primitives');
primitives.hiddenFromPublishing = true;
```

---

## Reference

For background on how Figma collections and modes work with the 3-tier model, see the `token-foundation` skill's `references/figma-variables.md`.
