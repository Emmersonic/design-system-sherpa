/**
 * scan_standalone.js
 *
 * Paste this script into figma_execute to scan variable bindings on components
 * that are NOT covered by figma_analyze_component_set:
 *   - Standalone COMPONENT nodes (not inside a COMPONENT_SET)
 *   - Spacing and radius bindings on any component type
 *
 * Configure the options object below before running.
 * Results are returned as a compact usage map — save to bridge-scan-[n].json.
 *
 * Usage:
 *   - Set filter to a component name prefix (e.g. "Icon") to scope to one category
 *   - Set maxComponents to limit batch size (recommended: 50)
 *   - Set includeSpacing: false to skip spacing/radius (color only)
 *   - Run multiple times with different filters to cover all categories
 */

const options = {
  filter: null,          // string | null — match component names starting with this prefix
  maxComponents: 50,     // number | null — max components to scan per run
  includeSpacing: true,  // boolean — include spacing + radius bindings
};

// ─── Build variable ID → name lookup ────────────────────────────────────────

const allVars = await figma.variables.getLocalVariablesAsync();
const varLookup = Object.fromEntries(
  allVars.map(v => [v.id, { name: v.name, collectionId: v.variableCollectionId }])
);

// ─── Find standalone components ─────────────────────────────────────────────
// "Standalone" = COMPONENT whose parent is not a COMPONENT_SET.
// COMPONENT_SET nodes are handled by figma_analyze_component_set.

let components = figma.root.findAll(
  n => n.type === 'COMPONENT' && n.parent?.type !== 'COMPONENT_SET'
);

if (options.filter) {
  components = components.filter(c => c.name.startsWith(options.filter));
}
if (options.maxComponents != null) {
  components = components.slice(0, options.maxComponents);
}

// ─── Property groups ─────────────────────────────────────────────────────────

const SPACING_PROPS = [
  'itemSpacing',
  'counterAxisSpacing',
  'paddingTop',
  'paddingBottom',
  'paddingLeft',
  'paddingRight',
];

const RADIUS_PROPS = [
  'cornerRadius',
  'topLeftRadius',
  'topRightRadius',
  'bottomLeftRadius',
  'bottomRightRadius',
];

// ─── Accumulate usage ────────────────────────────────────────────────────────
// Structure: { [variableId]: { name, usedAs: { [propType]: [componentCategory, ...] } } }

const usage = {};

function record(varId, propType, componentName) {
  if (!varLookup[varId]) return; // variable not in this file
  if (!usage[varId]) {
    usage[varId] = { name: varLookup[varId].name, usedAs: {} };
  }
  if (!usage[varId].usedAs[propType]) {
    usage[varId].usedAs[propType] = [];
  }
  // Store the top-level category (first path segment) to keep output compact
  const category = componentName.split('/')[0].trim();
  if (!usage[varId].usedAs[propType].includes(category)) {
    usage[varId].usedAs[propType].push(category);
  }
}

function walkNode(node, rootComponentName) {
  const bv = node.boundVariables;
  if (bv) {

    // Fills — distinguish text fills from other fills for mapping accuracy
    if (Array.isArray(bv.fills)) {
      bv.fills.forEach(alias => {
        if (alias?.id) {
          record(alias.id, node.type === 'TEXT' ? 'textFill' : 'fill', rootComponentName);
        }
      });
    }

    // Strokes
    if (Array.isArray(bv.strokes)) {
      bv.strokes.forEach(alias => {
        if (alias?.id) record(alias.id, 'stroke', rootComponentName);
      });
    }

    // Spacing and radius (only if enabled)
    if (options.includeSpacing) {
      [...SPACING_PROPS, ...RADIUS_PROPS].forEach(prop => {
        if (bv[prop]?.id) record(bv[prop].id, prop, rootComponentName);
      });
    }

    // Opacity
    if (bv.opacity?.id) record(bv.opacity.id, 'opacity', rootComponentName);
  }

  // Recurse into children
  if ('children' in node) {
    node.children.forEach(child => walkNode(child, rootComponentName));
  }
}

components.forEach(component => walkNode(component, component.name));

// ─── Return compact result ────────────────────────────────────────────────────

return {
  scanned: components.length,
  filter: options.filter,
  components: components.map(c => ({ id: c.id, name: c.name })),
  usage,
};
