# Design Token Skills

A set of Claude skills for building and maintaining a 3-tier design token system in Figma. Each skill handles one stage of the pipeline — from initial architecture decisions through to pushing tokens into Figma and exporting to code.

---

## What's included

| Skill | What it does |
|---|---|
| `token-foundation` | Interview-driven setup of naming conventions, tiers, modes, and categories. Produces `foundation.md`. |
| `token-figma-scaffold` | Creates the Figma variable collections and modes before any tokens are generated. Produces `scaffold-state.json`. |
| `token-generate` | Generates a full token set for one category (color, spacing, typography, etc.) across all tiers. Produces `token-proposal-[category].json`. |
| `token-push` | Validates and pushes an approved token proposal into Figma. Writes variable IDs back to the proposal file. |
| `token-audit` | Health check of an existing token system — naming violations, broken aliases, missing mode values, orphaned tokens. |
| `token-migrate` | Migrates an existing system (old styles, flat tokens, hardcoded values) to the 3-tier model. |
| `token-bridge` | Non-destructive migration path: adds a `Legacy` mode to the `Tokens` collection that maps new semantic token names to an old token system. Components get rebound to new names with zero visual change; graduation to new primitives happens per-token, with visual preview at each step. |
| `token-apply` | Constraint layer for AI-assisted design work — ensures every visual property assigned to a Figma layer comes from the correct token tier. |

Each skill ships with a `scripts/` folder and a `references/token-schema.json`. See [Scripts](#scripts) below.

---

## The 3-tier model

```
Primitives          raw values        color/blue/500 → #3B82F6
    ↓
Semantic tokens     intent aliases    color/surface/brand → color/blue/500 (light)
    ↓                                                      → color/blue/600 (dark)
Component tokens    component aliases button/background/primary/default → color/surface/brand
    ↓
Design layers       bound in Figma
```

- **Primitives** live in the `Primitives` Figma collection, hidden from publishing. Never applied to layers directly.
- **Semantic tokens** live in the `Tokens` collection with one value per mode (light/dark). These are what get applied to design elements.
- **Component tokens** are optional — use them for complex, state-heavy components that need to be updated independently.

---

## Pipeline

### New system

Run skills in this order when setting up a system from scratch:

```
token-foundation  →  foundation.md
        ↓
token-figma-scaffold  →  scaffold-state.json
        ↓
token-generate  →  token-proposal-[category].json  (repeat per category)
        ↓
   [designer reviews and sets status: "approved"]
        ↓
token-push  →  variables in Figma + figma_ids written back to proposal
        ↓
token-audit  (run periodically, before releases, after adding components)
```

### Migrating an existing system

Two paths depending on how much risk is acceptable:

```
                        existing Figma file
                               ↓
                    token-foundation  →  foundation.md
                    token-figma-scaffold  →  scaffold-state.json
                    token-generate + token-push  (new primitives + semantics)
                               ↓
              ┌────────────────┴─────────────────┐
              │                                  │
        token-bridge                       token-migrate
    (non-destructive)                      (destructive)
              │                                  │
    Adds Legacy mode to Tokens          Replaces old bindings
    Components rebound with             with new token values
    zero visual change                  in one pass
    Graduation is per-token             No rollback once applied
    and reversible                      Best for smaller systems
              │                                  │
              └──────────────┬───────────────────┘
                             ↓
                        token-audit
```

**Use `token-bridge` when:**
- The design system is large (many components, many token consumers)
- The team needs zero visual disruption during migration
- You want to graduate tokens category-by-category and validate at each step
- There's an ongoing product team using the library who can't absorb a big-bang change

**Use `token-migrate` when:**
- The old system is small or poorly structured (easier to cut over cleanly)
- You're replacing hardcoded values or Figma styles (no variables to alias)
- The migration can happen in a branch or duplicate file with no active consumers

`token-apply` is not a one-time setup step — it's a constraint layer loaded whenever an AI agent is creating or modifying designs in Figma.

---

## Runtime files

Skills read and write these files in your working directory:

| File | Written by | Read by |
|---|---|---|
| `foundation.md` | `token-foundation` | all skills |
| `scaffold-state.json` | `token-figma-scaffold` | `token-push`, `token-apply`, `token-bridge` |
| `token-proposal-[category].json` | `token-generate` | `token-push`, `token-audit`, `token-apply` |
| `bridge-mapping.json` | `token-bridge` | `token-bridge` (Stage 7 rebind) |
| `bridge-state.json` | `token-bridge` | `token-bridge` (graduation tracking) |

Commit these to your repo alongside your Figma file. They are the source of truth the scripts operate on.

### Proposal lifecycle

Each `token-proposal-*.json` file moves through a status lifecycle:

```
draft  →  reviewed  →  approved  →  pushed
```

`token-push` will not write to Figma until `meta.status` is `"approved"`. Set this manually after the designer signs off on the tables from `token-generate`.

---

## token-bridge

`token-bridge` is a non-destructive migration skill. Rather than replacing old token bindings directly, it adds a `Legacy` mode to the existing `Tokens` collection and creates new semantic variables whose `Legacy` mode values alias the old tokens. Components are then rebound to the new names — with all values still flowing from the old system, unchanged.

```
Before:   component layer  →  old/Primary  →  #3B82F6
After:    component layer  →  color/surface/brand (Legacy mode)  →  old/Primary  →  #3B82F6
Graduated: component layer  →  color/surface/brand (Light mode)  →  color/blue/500  →  #3B82F6
```

### Why a mode rather than separate alias variables

A dedicated `Legacy` mode makes the bridge a first-class Figma concept:

- **Instant comparison** — switch any frame from `Legacy` to `Light` to see exactly what new primitive values look like before anyone else sees them
- **Real rollback** — if something looks wrong after graduation, switch back to `Legacy`; the old aliases are still intact
- **Clean lifecycle** — when migration is complete, deleting the `Legacy` mode removes all bridge references in one operation

### When to run it in the process

Run `token-bridge` after new primitives and semantics exist in Figma (i.e. after `token-generate` + `token-push` for each category), but before any components are manually updated to use the new names.

```
token-generate + token-push  (new primitives and semantics in Figma)
        ↓
token-bridge  (add Legacy mode, create bridge variables, rebind components)
        ↓
[validation: switch frames to Legacy, confirm visuals are unchanged]
        ↓
[graduation: per-category, switch Light/Dark aliases to new primitives]
        ↓
token-audit  (confirm no remaining old-token bindings)
        ↓
[delete Legacy mode]
```

### How the scan works

Before building the mapping table, the skill scans what old tokens are actually bound to in components — not what their names suggest. This is important because old tokens are often overloaded: the same `Primary` token might be used as a background fill on buttons, a text color on links, and a stroke on focus rings. Those contexts map to three different new semantic tokens (`color/surface/brand`, `color/text/link`, `color/border/focus`). Name inference would assign one mapping and be wrong in two places.

The scan uses two mechanisms:

| Mechanism | What it covers |
|---|---|
| `figma_analyze_component_set` | Color fill, stroke, and text color bindings on COMPONENT_SET nodes — the bulk of any design system |
| `scripts/scan_standalone.js` | Standalone COMPONENT nodes not in a set; spacing and radius bindings on all components |

Components are processed in batches of 25. After the first batch the skill pauses for confirmation before continuing — this validates the approach on a representative sample before committing to the full scan.

### Graduation

Graduation means updating a new bridge variable's `Light` and `Dark` mode values from temporary hex placeholders to real aliases pointing at the new primitives. It happens per-token or per-category, not all at once.

The `bridge-state.json` file tracks status for every variable:

```
bridged     — Legacy mode aliases old token; Light/Dark hold a hex placeholder
graduated   — Light/Dark aliases point to new primitives; Legacy still intact
```

The `Legacy` mode is only removed after every variable reaches `graduated` status and a full visual review confirms correctness. This is the only irreversible operation in the entire workflow.

### Best practices

**Work on a branch or duplicate file for Stage 7 (rebinding).** Stages 1–6 are purely additive — a new mode and new variables. Stage 7 changes component layer bindings, which is harder to undo.

**Validate per category, not at the end.** After rebinding each component category, take a screenshot in Legacy mode and confirm it matches the pre-migration state. Catching a bad mapping on `Button` is cheap; catching it after rebinding 40 component sets is not.

**Don't delete the old tokens until graduation is complete.** Bridge variables in Legacy mode alias the old tokens directly. Deleting old tokens before graduation breaks the Legacy aliases and defeats the point of the bridge.

**Keep `bridge-state.json` committed.** It's the only record of which variables are bridged vs. graduated. If it's lost, you'd need to re-inspect variable aliases to reconstruct the state.

**Token splits require two separate new variables.** When an overloaded old token maps to two new semantic names (e.g. `Primary` → `color/surface/brand` + `color/text/link`), both new variables must be created. Layers that used `Primary` as a fill will be rebound to `color/surface/brand`; layers that used it as a text color will be rebound to `color/text/link`. The rebind script handles this via the mapping table — one old ID can map to different new IDs depending on context — but the mapping must be explicit in `bridge-mapping.json`.

**Use `token-audit` after rebinding each batch** to catch any layers that still reference old tokens directly (not through the bridge). Some layers may have been missed by the scan (instances with local overrides, detached components, etc.).

---

### token-bridge scripts

These scripts are JavaScript for use with `figma_execute` via the `figma-console` MCP. They live in `token-bridge/scripts/` and are pasted into `figma_execute` directly — they are not run from the terminal.

#### `scan_standalone.js`

Scans variable bindings on components not covered by `figma_analyze_component_set`:
- Standalone `COMPONENT` nodes (not inside a `COMPONENT_SET`)
- Spacing and radius bindings (`itemSpacing`, `paddingTop`, `cornerRadius`, etc.) on all component types

Configure the `options` object at the top before running:

```js
const options = {
  filter: 'Icon',      // scope to one category by name prefix
  maxComponents: 50,   // batch size — keep under 100 for large libraries
  includeSpacing: true // set false for color-only pass
};
```

Returns a compact JSON object grouped by variable ID — save output to `bridge-scan-[n].json` and aggregate after all batches complete.

Run once per component category (using `filter`) rather than scanning everything in one pass. This keeps individual `figma_execute` calls fast and bounded.

#### `rebind_layer.js`

Rebinds variable references on a single component or component set from old token IDs to new bridge token IDs. Populate `componentNodeId` and `mapping` from `bridge-mapping.json` and `bridge-state.json` before running.

```js
const options = {
  componentNodeId: '214:274',   // COMPONENT or COMPONENT_SET node ID
  mapping: {
    'VariableID:1:10': 'VariableID:2:101',  // old → new
    'VariableID:1:11': 'VariableID:2:102',
  },
  dryRun: false  // set true to preview changes without writing
};
```

Always run with `dryRun: true` first on a new component category to confirm the mapping looks right before committing. The returned summary shows exactly which layers will be rebound and which will be skipped (already on new tokens, or not in the mapping).

Run this after applying `Legacy` mode to the component's parent frame so the visual result is verifiable immediately after.

---

## Scripts

Every skill includes a `scripts/` folder with five shared Python scripts. They require Python 3.8+ and no third-party dependencies.

### `hex_to_figma.py`

Converts hex color values in a token proposal to Figma's `{r, g, b, a}` float format (0–1 range). Populates the `figma_value` field on every `COLOR` primitive so `token-push` doesn't do arithmetic.

```bash
# Convert all colors in a proposal
python scripts/hex_to_figma.py token-proposal-color.json

# Spot-check a single value
python scripts/hex_to_figma.py --hex "#3B82F6"
# → { "r": 0.231, "g": 0.510, "b": 0.965, "a": 1.0 }
```

---

### `validate_tokens.py`

Validates a token proposal against the 3-tier naming convention and structural rules before anything touches Figma.

Checks performed:
- Naming convention — kebab-case, slash separators, no abbreviations, no raw values in names
- Appearance words in semantic/component tiers (`color/blue-primary` should be `color/surface/brand`)
- Alias integrity — every alias target exists in the proposal
- Mode coverage — all alias tokens have values for every declared mode
- Type consistency — alias chains don't change variable type mid-chain
- Proposal status — warns if status is not `"approved"` before push

```bash
# Validate with explicit mode list
python scripts/validate_tokens.py token-proposal-color.json --modes light dark

# Fail on warnings too (useful in CI)
python scripts/validate_tokens.py token-proposal-color.json --strict

# Auto-fix safe naming issues (camelCase → kebab-case, underscores → hyphens)
python scripts/validate_tokens.py token-proposal-color.json --fix
```

Exit code `0` = pass, `1` = errors found.

---

### `build_batch_payload.py`

Chunks a token proposal into Figma-ready batch API payloads. Handles hex → Figma color conversion and enforces the required call order: primitives first, then token creation, then alias updates.

```bash
# Build all payloads and write to a directory
python scripts/build_batch_payload.py token-proposal-color.json --out payloads/

# Preview without writing files
python scripts/build_batch_payload.py token-proposal-color.json --summary

# Build only primitives
python scripts/build_batch_payload.py token-proposal-color.json --tier primitives

# Adjust chunk size (default: 30 variables per batch)
python scripts/build_batch_payload.py token-proposal-color.json --chunk-size 20
```

Output files are named for their run order:
```
payloads/
  create_primitives_batch_01.json
  create_tokens_batch_01.json
  update_tokens_aliases_batch_01.json
```

---

### `diff_tokens.py`

Compares two token proposal snapshots and produces a structured diff with semantic version impact classification.

Change types and their version impact:

| Change | Impact |
|---|---|
| Token added | patch |
| Value / alias changed | patch |
| Mode added | minor |
| Token removed | **major (breaking)** |
| Token renamed | **major (breaking)** |
| Mode removed | **major (breaking)** |

```bash
# Human-readable diff with changelog entry
python scripts/diff_tokens.py proposal-v1.json proposal-v2.json

# Markdown changelog entry only
python scripts/diff_tokens.py proposal-v1.json proposal-v2.json --format markdown

# JSON output for programmatic use
python scripts/diff_tokens.py proposal-v1.json proposal-v2.json --format json

# Write changelog to a file
python scripts/diff_tokens.py proposal-v1.json proposal-v2.json --out CHANGELOG.md
```

Exit codes: `0` = no changes, `1` = patch/minor changes, `2` = breaking changes.

---

### `tokens_to_css.py`

Exports a token proposal to platform-ready code. Semantic tokens are output as `var()` references to primitives in CSS, keeping the full alias chain live in the browser.

Supported formats: `css`, `scss`, `js`, `ts`, `json` (W3C DTCG format).

```bash
# CSS with :root (light) and [data-theme="dark"] blocks
python scripts/tokens_to_css.py token-proposal-color.json --format css --all-modes

# Single mode
python scripts/tokens_to_css.py token-proposal-color.json --format css --mode light

# SCSS variables (resolved to concrete values)
python scripts/tokens_to_css.py token-proposal-color.json --format scss

# ES module
python scripts/tokens_to_css.py token-proposal-color.json --format js

# TypeScript
python scripts/tokens_to_css.py token-proposal-color.json --format ts

# W3C DTCG JSON
python scripts/tokens_to_css.py token-proposal-color.json --format json

# Write to file
python scripts/tokens_to_css.py token-proposal-color.json --format css --all-modes --out tokens.css
```

CSS output example:
```css
/* Primitives */
:root {
  --color-blue-500: #3B82F6;
  --color-neutral-0: #FFFFFF;
}

/* Light mode */
:root {
  --color-surface-default: var(--color-neutral-0);
  --color-surface-brand: var(--color-blue-500);
}

/* Dark mode */
[data-theme="dark"] {
  --color-surface-default: var(--color-neutral-950);
  --color-surface-brand: var(--color-blue-600);
}
```

---

## Installation

**1. Clone the repo**

```bash
git clone https://github.com/your-org/ds-token-skills.git ~/ds-token-skills
cd ~/ds-token-skills
```

**2. Run the install script**

```bash
./install.sh
```

This will symlink the skills into `~/.claude/skills/` and prompt you for your design system project path to copy the Python scripts there.

To skip the prompt and provide the path upfront:
```bash
./install.sh --scripts /path/to/your/design-system-project
```

To install skills only without copying scripts:
```bash
./install.sh --skip-scripts
```

**3. Reload Claude Code** to pick up the new skills.

---

**How it works**

Skills are plain directories containing a `SKILL.md`. They live in `~/.claude/skills/` and are loaded globally by Claude Code — no per-project config needed.

The Python scripts (`scripts/`) run from your project's working directory, so they need to be in your project alongside your token proposal files. They require Python 3.8+ and no third-party dependencies.

**Team / shared setup**

Clone to any shared path your team has read access to, then run `install.sh` on each machine. The symlinks point back to the cloned repo, so a `git pull` updates everyone's skills without re-running the installer.

---

## Schema

All skills share `references/token-schema.json` — a JSON Schema defining the `token-proposal-*.json` format. Key fields:

```jsonc
{
  "meta": {
    "category": "color",           // which category this proposal covers
    "version": "1.0.0",            // semver of the token system
    "status": "draft",             // draft | reviewed | approved | pushed
    "figma_file_url": "https://..."
  },
  "collections": {
    "primitives": [
      // { name, type, value (hex), figma_value (populated by hex_to_figma.py) }
    ],
    "tokens": [
      // { name, type, modes: { light: "alias-target", dark: "alias-target" } }
    ],
    "components": [ /* same shape as tokens */ ]
  },
  "figma_ids": {
    // Written by token-push after variables are created
    "collection_ids": { "primitives": "...", "tokens": "..." },
    "mode_ids": { "light": "1:0", "dark": "1:1" },
    "variable_ids": { "color/blue/500": "VariableID:123:456" }
  }
}
```

See `references/token-schema.json` in any skill for the full schema with descriptions.
