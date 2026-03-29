---
name: token-generate
description: Generate design tokens for a specific category (color, spacing, typography, border-radius, etc.) across all three tiers — primitives, semantic aliases, and optionally component tokens. Use this skill whenever someone wants to create tokens for a category, expand their token set, add a new component's tokens, or generate the actual token values and aliases for their design system. Also use when someone says "generate my color tokens", "create spacing tokens", "add button tokens", or asks to populate any part of their token system with actual values.
---

# Token Generate

Generates the full token set for one category at a time, across all tiers. Call once per category (color, spacing, typography, etc.).

**Input required:** A category name and a confirmed `foundation.md` from `token-foundation`.
**Output:** A structured token proposal for review, ready to be pushed to Figma via `token-push`.

---

## Step 1 — Identify what to generate

Ask the designer:
1. Which **category** are we generating? (color, spacing, typography, border-radius, elevation, motion, or a specific component)
2. Do we need **component tokens** for this category? (buttons, inputs, cards, etc.) — or just primitive + semantic?
3. Any specific **values, brand colors, or scale** to use? If none provided, propose sensible defaults.
4. Are we **adding a new mode** to an existing collection (e.g. adding Dark when Light exists)? If so, see the "Alias-only mode generation" section below.

### Building on an existing primitive set

If `scaffold-state.json` exists and contains variable IDs from a previous generation pass, load those IDs and use them as alias targets directly. Do not re-describe primitive values that already exist — reference them by their known IDs.

```
1. Read scaffold-state.json → extract variable IDs
2. For each semantic token alias target, use the existing primitive variable ID
3. Only generate new primitives for values not already in the file
```

This avoids duplicate primitives and ensures alias chains are stable.

---

## Step 2 — Generate primitives

Produce a table of all primitive tokens for this category. Follow the naming convention from `foundation.md`.

**Format:**
```
Token name                  | Type   | Value
----------------------------|--------|------------------
color/blue/50               | color  | #EFF6FF
color/blue/100              | color  | #DBEAFE
color/blue/500              | color  | #3B82F6
color/blue/600              | color  | #2563EB
color/blue/900              | color  | #1E3A8A
```

**Color ramp guidance:**
- Generate 7–9 stops per hue: 50, 100, 200, 300, 400, 500, 600, 700, 800, 900
- Lower numbers = lighter (more white), higher = darker (more black)
- Include neutral/gray ramp for surfaces, text, and borders
- Include semantic hues: blue (info/brand), red (danger), green (success), amber (warning)
- Add any brand-specific hues from the designer's input

**Spacing scale guidance:**
- Use 4pt base: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96
- Or 8pt base: 8, 16, 24, 32, 48, 64, 96
- Name as `spacing/1`, `spacing/2` etc. (index-based, not px-based)

**Border-radius guidance:**
- none (0), sm (4px), md (8px), lg (12px), xl (16px), 2xl (24px), full (9999px)

**Typography guidance:**
- Font sizes: 12, 14, 16, 18, 20, 24, 28, 32, 36, 48
- Font weights: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)
- Line heights: 1.25 (tight), 1.5 (normal), 1.75 (relaxed)

### STRING variable aliases (font-family, font-weight)

Not all tokens are colors or numbers. STRING primitives are used for font-family and font-weight values. Include them in the proposal using the same format:

**Primitive STRING tokens:**
```
Token name                  | Type    | Value
----------------------------|---------|------------------
font-family/sans            | STRING  | Inter, system-ui, sans-serif
font-family/mono            | STRING  | JetBrains Mono, monospace
font-weight/regular         | STRING  | Regular
font-weight/medium          | STRING  | Medium
font-weight/semibold        | STRING  | Semi Bold
font-weight/bold            | STRING  | Bold
```

**Semantic STRING aliases:**
```
Token name                      | Light mode alias          | Dark mode alias
--------------------------------|---------------------------|---------------------------
text/font-family/default        | font-family/sans          | font-family/sans
text/font-family/code           | font-family/mono          | font-family/mono
text/font-weight/heading        | font-weight/semibold      | font-weight/semibold
text/font-weight/body           | font-weight/regular       | font-weight/regular
```

STRING aliases follow the same proposal format as COLOR aliases — the `modes` dict maps mode names to primitive token names. The `type` field should be `"STRING"`.

---

## Step 3 — Generate semantic tokens

For each semantic token, show:
- The token name (intent-based)
- The light-mode alias (which primitive it points to)
- The dark-mode alias (which primitive it points to in dark mode)

**Format:**
```
Token name                      | Light mode alias      | Dark mode alias
--------------------------------|-----------------------|----------------------
color/surface/default           | color/neutral/0       | color/neutral/950
color/surface/secondary         | color/neutral/50      | color/neutral/900
color/surface/brand             | color/blue/500        | color/blue/600
color/text/primary              | color/neutral/900     | color/neutral/50
color/text/secondary            | color/neutral/500     | color/neutral/400
color/text/on-brand             | color/neutral/0       | color/neutral/0
color/border/default            | color/neutral/200     | color/neutral/700
color/border/focus              | color/blue/500        | color/blue/400
```

**Coverage checklist for color semantic tokens:**
- [ ] `surface/` — all background contexts (default, secondary, tertiary, brand, brand-subtle, danger, success, warning, info)
- [ ] `text/` — all text contexts (primary, secondary, disabled, on-brand, danger, success, warning, info, link)
- [ ] `border/` — all stroke contexts (default, strong, focus, danger, success)
- [ ] `icon/` — icon fill contexts if icons need separate tokens from text

For spacing, semantic tokens are optional. Only create them if the team uses named roles (e.g. `spacing/component/md`, `spacing/layout/lg`). Skip if the primitives are used directly.

---

## Step 4 — Generate component tokens (if requested)

For each component, generate the full state × property matrix.

**Ask:** Which components? (e.g. button, input, checkbox, card, badge, tooltip)

**Format:**
```
Token name                              | Alias (semantic token)
----------------------------------------|----------------------------------
button/background/primary/default       | color/surface/brand
button/background/primary/hover         | color/blue/600
button/background/primary/active        | color/blue/700
button/background/primary/disabled      | color/surface/brand-subtle
button/background/primary/focus         | color/surface/brand
button/text/primary/default             | color/text/on-brand
button/text/primary/disabled            | color/text/disabled
button/border/primary/focus             | color/border/focus

button/background/secondary/default     | color/surface/default
button/background/secondary/hover       | color/surface/secondary
button/background/secondary/disabled    | color/surface/secondary
button/text/secondary/default           | color/text/primary
button/text/secondary/disabled          | color/text/disabled
button/border/secondary/default         | color/border/default
button/border/secondary/focus           | color/border/focus
```

**Property coverage per component:**
- background (fill)
- text (foreground)
- border (stroke)
- icon (if component contains icons)
- shadow (if component uses elevation)

**State coverage:**
- default, hover, active/pressed, disabled, focus, focus-visible

Only generate states that are meaningful for each property. Not every property needs all states.

---

## Step 4b — Generate component token aliases

When wiring component tokens (e.g. `component_next/`) to semantic tokens (e.g. `semantic_next/`), follow this structured path:

1. **List all component token slots** — for each component, enumerate every property × variant × state combination (e.g. `button/background/primary/default`)
2. **Map each slot to a semantic token** — identify the semantic token that best matches the intent (e.g. `button/background/primary/default` → `color/surface/brand`)
3. **Handle slots with no semantic equivalent** — if a component slot has no matching semantic token:
   - Flag it as a gap and propose a new semantic token to create
   - Or alias directly to a primitive with a note explaining why the semantic tier is skipped
4. **Present the mapping table** for review before generating

**Format:**
```
Component token                         | Semantic alias               | Notes
----------------------------------------|------------------------------|------------------
button/background/primary/default       | color/surface/brand          |
button/background/primary/hover         | color/surface/brand-hover    |
button/icon/primary/default             | color/icon/on-brand          |
card/shadow/elevated                    | elevation/md                 | no semantic match — aliased to primitive
```

Component tokens should almost never alias directly to primitives. If you find yourself doing this, check whether a semantic token should be created first.

---

## Step 5 — Present for review

Present the full token proposal as tables (primitives → semantic → component) and explicitly ask:

1. Do the primitive values look right? Any colors/values to change?
2. Do the semantic aliases make sense? Are any use cases missing?
3. Are there any component tokens missing states or properties?
4. Anything to add or remove before pushing to Figma?

**Do not push to Figma yet.** The next skill, `token-push`, handles that after confirmation.

---

## Step 6 — Save the proposal file

After the designer confirms the token tables, save the proposal as `token-proposal-[category].json` conforming to `${CLAUDE_SKILL_DIR}/../_shared/references/token-schema.json`.

Key points:
- `meta.status` must be `"draft"` at this point — the designer confirms it to `"approved"` before pushing
- Color primitive `value` fields use hex strings (`"#3B82F6"`) — `hex_to_figma.py` will populate `figma_value` during push
- Alias tokens use the `modes` dict: `{ "light": "color/neutral/0", "dark": "color/neutral/950" }`

Run validation before handing off:
```bash
python "${CLAUDE_SKILL_DIR}/../_shared/scripts/validate_tokens.py" token-proposal-[category].json --modes light dark
```

Fix any errors before proceeding to `token-push`.

---

## Alias-only mode generation

When adding a new mode to an existing semantic collection (e.g. adding Dark mode when Light already exists with all primitives in place), do not regenerate the full token set. Instead:

1. **Load the existing proposal** — read `token-proposal-[category].json` to get the current token names and light-mode aliases
2. **Generate a diff, not a full set** — produce only the tokens whose alias target changes in the new mode
3. **Present as a delta table:**

```
Token name                      | Light mode (existing)     | Dark mode (new)
--------------------------------|---------------------------|---------------------------
color/surface/default           | color/neutral/0           | color/neutral/950
color/surface/brand             | color/blue/500            | color/blue/600
color/text/primary              | color/neutral/900         | color/neutral/50
```

4. Tokens where the value is the same across modes can be omitted from the table (they inherit the same alias)
5. After approval, update the existing proposal file — add the new mode column to each token's `modes` dict

This keeps proposals focused and avoids re-reviewing tokens that don't change between modes.

---

## When the token-proposal JSON schema doesn't apply

The `references/token-schema.json` schema validates the standard proposal format — primitives with raw values and alias tokens with mode mappings. It does **not** cover:

- **Alias-only proposals** (new modes on existing collections) — these only add mode columns, no new primitives
- **STRING variable types** (font-family, font-weight) — the schema's `figma_value` definition is color-specific

For these cases, skip `validate_tokens.py` or use it with `--modes` only for the modes that apply. Validate naming conventions and alias integrity manually.

---

## Notes on typography

Figma currently does not support composite typography variables (a variable that bundles font-family + size + weight + line-height). Typography tokens should be handled as:
- Individual number variables for font-size, line-height (can be done here)
- Individual string variables for font-family
- Figma **text styles** for composite styles (heading, body, label, etc.) — these are created separately and are not part of the variable system

If the designer asks about text styles, note this limitation and offer to generate the text style names and specs in a separate table.

---

## Verification (required)

After saving the proposal file, run a structured verification before handing off:

1. **Re-read the saved file** — confirm it parses as valid JSON and matches the expected structure
2. **Spot-check a sample of values** — verify 3–5 primitives have correct hex/number values and 3–5 aliases point to valid primitive names
3. **Confirm no broken aliases** — every alias target in the `modes` dict must correspond to a token name that exists in the proposal's `collections.primitives` array (or already in Figma)

Report any discrepancies before proceeding to `token-push`.
