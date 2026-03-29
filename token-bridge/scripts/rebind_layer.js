/**
 * rebind_layer.js
 *
 * Paste this script into figma_execute to rebind variable references on a
 * component from old token IDs to new bridge token IDs.
 *
 * Run once per component set / standalone component.
 * Build the mapping object from bridge-mapping.json + bridge-state.json.
 *
 * Usage:
 *   1. Set componentNodeId to the COMPONENT or COMPONENT_SET node ID
 *   2. Populate mapping with { "oldVarId": "newVarId" } entries
 *   3. Paste into figma_execute and run
 *   4. Review the returned summary before moving to the next component
 *
 * Note: Run AFTER the component's parent frame has Legacy mode applied,
 * so you can validate visually that nothing changed.
 */

const options = {
  componentNodeId: 'REPLACE_WITH_NODE_ID', // e.g. '214:274'

  // Map of old variable ID → new bridge variable ID
  // Paste entries from bridge-mapping.json for this component's tokens
  mapping: {
    // 'VariableID:1:10': 'VariableID:2:101',
    // 'VariableID:1:11': 'VariableID:2:102',
  },

  // Set to true for a dry run — reports what would change without writing anything
  dryRun: false,
};

// ─── Validate inputs ─────────────────────────────────────────────────────────

const root = figma.getNodeById(options.componentNodeId);
if (!root) throw new Error(`Node not found: ${options.componentNodeId}`);
if (Object.keys(options.mapping).length === 0) {
  throw new Error('mapping is empty — populate it from bridge-mapping.json before running');
}

// ─── Property groups ─────────────────────────────────────────────────────────

// Array-valued bound variable props (fills/strokes store an array of aliases)
const ARRAY_PROPS = ['fills', 'strokes'];

// Scalar bound variable props (single alias per property)
const SCALAR_PROPS = [
  'itemSpacing',
  'counterAxisSpacing',
  'paddingTop',
  'paddingBottom',
  'paddingLeft',
  'paddingRight',
  'cornerRadius',
  'topLeftRadius',
  'topRightRadius',
  'bottomLeftRadius',
  'bottomRightRadius',
  'opacity',
  'width',
  'height',
];

// ─── Counters ────────────────────────────────────────────────────────────────

let rebound = 0;
let skipped = 0;  // bound to a variable not in the mapping (already on new token, or out of scope)
let unbound = 0;  // no variable binding at all (raw value — not our concern here)
const reboundDetails = [];

// ─── Rebind a single node ────────────────────────────────────────────────────

function rebindNode(node) {
  const bv = node.boundVariables;
  if (!bv) {
    unbound++;
    if ('children' in node) node.children.forEach(rebindNode);
    return;
  }

  // Array props: fills and strokes
  // Each entry in bv.fills/bv.strokes is { type: 'VARIABLE_ALIAS', id: '...' }
  ARRAY_PROPS.forEach(prop => {
    const aliases = bv[prop];
    if (!Array.isArray(aliases) || aliases.length === 0) return;

    const currentValues = node[prop];
    if (!Array.isArray(currentValues)) return;

    let changed = false;
    const updated = currentValues.map((paintValue, i) => {
      const alias = aliases[i];
      if (!alias?.id) return paintValue;

      const newId = options.mapping[alias.id];
      if (!newId) { skipped++; return paintValue; }

      changed = true;
      rebound++;
      reboundDetails.push(`${node.name} › ${prop}[${i}]: ${alias.id} → ${newId}`);

      return {
        ...paintValue,
        boundVariables: {
          color: { type: 'VARIABLE_ALIAS', id: newId },
        },
      };
    });

    if (changed && !options.dryRun) {
      node[prop] = updated;
    }
  });

  // Scalar props: spacing, radius, opacity, dimensions
  SCALAR_PROPS.forEach(prop => {
    const alias = bv[prop];
    if (!alias?.id) return;

    const newId = options.mapping[alias.id];
    if (!newId) { skipped++; return; }

    rebound++;
    reboundDetails.push(`${node.name} › ${prop}: ${alias.id} → ${newId}`);

    if (!options.dryRun) {
      const newVar = figma.variables.getVariableById(newId);
      if (newVar) node.setBoundVariable(prop, newVar);
    }
  });

  // Recurse
  if ('children' in node) {
    node.children.forEach(rebindNode);
  }
}

// ─── Run ─────────────────────────────────────────────────────────────────────

// For COMPONENT_SET nodes, walk the variants (children are COMPONENT nodes)
if (root.type === 'COMPONENT_SET') {
  root.children.forEach(variant => rebindNode(variant));
} else {
  rebindNode(root);
}

// ─── Return summary ───────────────────────────────────────────────────────────

return {
  dryRun: options.dryRun,
  component: root.name,
  rebound,
  skipped,
  unbound,
  // Full detail list — useful for verifying a sample; truncated for large components
  sample: reboundDetails.slice(0, 20),
  truncated: reboundDetails.length > 20 ? reboundDetails.length - 20 : 0,
};
