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

## Notes on typography

Figma currently does not support composite typography variables (a variable that bundles font-family + size + weight + line-height). Typography tokens should be handled as:
- Individual number variables for font-size, line-height (can be done here)
- Individual string variables for font-family
- Figma **text styles** for composite styles (heading, body, label, etc.) — these are created separately and are not part of the variable system

If the designer asks about text styles, note this limitation and offer to generate the text style names and specs in a separate table.
