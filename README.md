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

Run skills in this order when setting up a new system:

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

`token-apply` is not a one-time setup step — it's a constraint layer loaded whenever an AI agent is creating or modifying designs in Figma.

---

## Runtime files

Skills read and write these files in your working directory:

| File | Written by | Read by |
|---|---|---|
| `foundation.md` | `token-foundation` | all skills |
| `scaffold-state.json` | `token-figma-scaffold` | `token-push`, `token-apply` |
| `token-proposal-[category].json` | `token-generate` | `token-push`, `token-audit`, `token-apply` |

Commit these to your repo alongside your Figma file. They are the source of truth the scripts operate on.

### Proposal lifecycle

Each `token-proposal-*.json` file moves through a status lifecycle:

```
draft  →  reviewed  →  approved  →  pushed
```

`token-push` will not write to Figma until `meta.status` is `"approved"`. Set this manually after the designer signs off on the tables from `token-generate`.

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

Skills are `.skill` files — zip archives containing a `SKILL.md` and supporting files.

**Claude Code**

```bash
# Create your skills directory
mkdir -p ~/.claude/skills

# Unzip each skill
unzip token-foundation.skill    -d ~/.claude/skills/token-foundation
unzip token-figma-scaffold.skill -d ~/.claude/skills/token-figma-scaffold
unzip token-generate.skill      -d ~/.claude/skills/token-generate
unzip token-push.skill          -d ~/.claude/skills/token-push
unzip token-audit.skill         -d ~/.claude/skills/token-audit
unzip token-migrate.skill       -d ~/.claude/skills/token-migrate
unzip token-apply.skill         -d ~/.claude/skills/token-apply
```

Then add the skills path to your project's `CLAUDE.md`:
```
Skills path: ~/.claude/skills
```

**Shared / team setup**

Unzip into any shared directory your team has read access to and reference that path in your project config. Skills are plain folders — no registry or package manager required.

**Python scripts**

Scripts are called by Claude from each skill's `scripts/` folder. No global install needed beyond Python 3.8+, and no third-party dependencies.

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
