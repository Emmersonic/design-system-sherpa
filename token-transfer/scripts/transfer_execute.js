/**
 * transfer_execute.js
 *
 * Paste this script into figma_execute to transfer variables into the current
 * Figma file. Uses a two-phase approach:
 *   Phase 1: Create all variables (no values set yet)
 *   Phase 2: Set all values (raw, cross-collection aliases, self-referential aliases)
 *
 * This handles all three dependency tiers in a single call:
 *   Tier 1: Raw values (no dependencies)
 *   Tier 2: Cross-collection aliases (resolved from existing variables)
 *   Tier 3: Self-referential aliases (resolved from nameToId map built in Phase 1)
 *
 * For large transfers (200+ variables), run multiple times with increasing
 * `offset` values — raw-value variables must be in earlier chunks than the
 * alias variables that reference them.
 *
 * Generate the payload with:
 *   python build_transfer_payload.py source.json target.json --mode <mode> --js-out transfer_execute.js
 *
 * Then set collectionId and modeMap below from the target file before running.
 */

const options = {
  // Required: target collection ID (from figma_get_variables on the target file)
  collectionId: 'REPLACE_WITH_TARGET_COLLECTION_ID',

  // Required: source mode name → target mode ID
  // e.g. { "Light": "1:0", "Dark": "1:1" }
  modeMap: {},

  // Set true to preview what would happen without writing anything
  dryRun: false,
};

// ─── GENERATED PAYLOAD ───────────────────────────────────────────────────────
// Replace this block with output from build_transfer_payload.py --js-out
// Raw-value variables must appear before the alias variables that reference them.

const payload = {
  // Variables to create in the target collection.
  // Raw-value variables first, alias variables second.
  toCreate: [
    // { name: "color/blue/500", type: "COLOR", description: "", valuesByMode: {
    //     "Default": { r: 0.231, g: 0.510, b: 0.965, a: 1.0 }
    // }}
    // { name: "color/surface/brand", type: "COLOR", description: "", valuesByMode: {
    //     "Light": { type: "VARIABLE_ALIAS", targetName: "color/blue/500" },
    //     "Dark":  { type: "VARIABLE_ALIAS", targetName: "color/blue/600" }
    // }}
  ],

  // Existing target variables to update (overwrite / merge modes).
  toUpdate: [
    // { targetId: "VariableID:1:1", valuesByMode: {
    //     "Light": { type: "VARIABLE_ALIAS", targetName: "color/blue/500" }
    // }}
  ],
};

// ─────────────────────────────────────────────────────────────────────────────

// Build name → ID lookup from variables already in the file.
// New variables are added here as they're created, so later aliases in the
// same run can resolve them immediately.
const existingVars = await figma.variables.getLocalVariablesAsync();
const nameToId = Object.fromEntries(existingVars.map(v => [v.name, v.id]));

const created = [];
const updated = [];
const failed  = [];

// ─── Resolve a value (raw or alias) ─────────────────────────────────────────

function resolveValue(val, variableName, modeName) {
  if (val && typeof val === 'object' && val.type === 'VARIABLE_ALIAS') {
    const id = nameToId[val.targetName];
    if (!id) {
      failed.push({ variable: variableName, mode: modeName, reason: `dangling alias: "${val.targetName}" not found in target` });
      return null;
    }
    return { type: 'VARIABLE_ALIAS', id };
  }
  return val;
}

// ─── Phase 1: Create all variables (no values yet) ─────────────────────────
// All variables must exist before setting any values, so that self-referential
// aliases (tier 3) can resolve against the nameToId map.

const createdDefs = []; // { name, id, def } — for Phase 2 value-setting

for (const varDef of payload.toCreate) {
  if (options.dryRun) {
    created.push({ name: varDef.name, status: 'dry-run' });
    continue;
  }
  try {
    const v = figma.variables.createVariable(varDef.name, options.collectionId, varDef.type);
    if (varDef.description) v.description = varDef.description;

    // Register immediately so all aliases (including self-refs) can resolve
    nameToId[varDef.name] = v.id;
    createdDefs.push({ name: varDef.name, id: v.id, def: varDef });
    created.push({ name: varDef.name, id: v.id });
  } catch (e) {
    failed.push({ variable: varDef.name, reason: e.message });
  }
}

// ─── Phase 2: Set all values on created variables ───────────────────────────
// Now every variable in this collection has an ID in nameToId, so tier 1 (raw),
// tier 2 (cross-collection alias), and tier 3 (self-referential alias) all resolve.

for (const { name, id, def } of createdDefs) {
  for (const [modeName, val] of Object.entries(def.valuesByMode || {})) {
    const modeId = options.modeMap[modeName];
    if (!modeId) {
      failed.push({ variable: name, mode: modeName, reason: `mode "${modeName}" not in modeMap` });
      continue;
    }
    try {
      const resolved = resolveValue(val, name, modeName);
      if (resolved !== null) {
        const v = figma.variables.getVariableById(id);
        v.setValueForMode(modeId, resolved);
      }
    } catch (e) {
      failed.push({ variable: name, mode: modeName, reason: e.message });
    }
  }
}

// ─── Update existing variables ───────────────────────────────────────────────

for (const update of payload.toUpdate) {
  if (options.dryRun) {
    updated.push({ id: update.targetId, status: 'dry-run' });
    continue;
  }
  try {
    const v = figma.variables.getVariableById(update.targetId);
    if (!v) {
      failed.push({ id: update.targetId, reason: 'variable not found in target file' });
      continue;
    }

    for (const [modeName, val] of Object.entries(update.valuesByMode || {})) {
      const modeId = options.modeMap[modeName];
      if (!modeId) {
        failed.push({ variable: v.name, mode: modeName, reason: `mode "${modeName}" not in modeMap` });
        continue;
      }
      const resolved = resolveValue(val, v.name, modeName);
      if (resolved !== null) v.setValueForMode(modeId, resolved);
    }

    updated.push({ id: update.targetId, name: v.name });
  } catch (e) {
    failed.push({ id: update.targetId, reason: e.message });
  }
}

// ─── Return summary ───────────────────────────────────────────────────────────

return {
  dryRun: options.dryRun,
  created: created.length,
  updated: updated.length,
  failed: failed.length,
  failedDetails: failed.slice(0, 20),
  failedTruncated: Math.max(0, failed.length - 20),
  createdSample: created.slice(0, 5).map(v => v.name || v.id),
};
