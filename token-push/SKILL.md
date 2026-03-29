---
name: token-push
description: Push a reviewed and approved token proposal into Figma by creating variables, setting aliases, and configuring modes using the Figma MCP tools. Use this skill when someone is ready to write their tokens to Figma, after reviewing the output from token-generate or token-audit. Also use when someone says "push to Figma", "create these variables in Figma", "write the tokens", or wants to apply a token proposal to an actual Figma file.
---

# Token Push

Writes a confirmed token proposal to Figma using the MCP tools. Always run after `token-generate` (new tokens) or `token-audit` (fixes and updates) — never before the designer has reviewed and approved the token list.

---

## Prerequisites

- A reviewed and confirmed token proposal (from `token-generate` or `token-audit`)
- Figma file open and connected via the MCP bridge
- The `Primitives` and `Tokens` collections already exist (from `token-figma-scaffold`)
- Collection IDs known — retrieve with `figma_get_variables` if not already on hand

---

## Step 1 — Load and validate the proposal

Load `token-proposal-[category].json`. Verify `meta.status` is `"approved"` — do not push a `"draft"` proposal.

Run validation:
```bash
python "${CLAUDE_SKILL_DIR}/../_shared/scripts/validate_tokens.py" token-proposal-[category].json --modes light dark
```

If there are errors, fix them before proceeding. Warnings can be noted but don't block the push.

Then confirm with the designer:

> "I'm about to create [N] primitive tokens and [N] semantic tokens in your Figma file. This will modify the [collection names] collections. Shall I proceed?"

Wait for confirmation.

---

## Step 2 — Get collection IDs

If collection IDs aren't already known:

```
figma_get_variables(fileUrl: <current file>)
```

Extract and note:
- `Primitives` collection ID
- `Tokens` collection ID (and its mode IDs for light, dark, etc.)
- `Components` collection ID (if it exists)

---

## Step 3 — Build batch payloads

Use `build_batch_payload.py` to chunk the proposal into Figma-ready batches and convert hex colors:

```bash
python "${CLAUDE_SKILL_DIR}/../_shared/scripts/build_batch_payload.py" token-proposal-[category].json --out payloads/
```

This produces `create_primitives_batch_NN.json`, `create_tokens_batch_NN.json`, and `update_tokens_aliases_batch_NN.json` files. Check the summary output for total API call count.

**Run order is strict: primitives → token creation → alias updates.**

---

## Step 4 — Create semantic variables with aliases

Create semantic tokens in the `Tokens` collection. Each one needs values set per mode.

For each semantic token:

```
figma_create_variable(
  collectionId: <tokens collection id>,
  name: "color/surface/default",
  type: "COLOR"
)
```

Then set the alias for each mode:

```
figma_update_variable(
  variableId: <new semantic variable id>,
  modeId: <light mode id>,
  value: { type: "VARIABLE_ALIAS", id: <id of color/neutral/0> }
)

figma_update_variable(
  variableId: <new semantic variable id>,
  modeId: <dark mode id>,
  value: { type: "VARIABLE_ALIAS", id: <id of color/neutral/950> }
)
```

**Efficiency note:** Use `figma_batch_create_variables` for creation, then `figma_batch_update_variables` for setting aliases, rather than individual calls per variable.

---

## Step 5 — Create component variables (if applicable)

Same process as semantic variables — create in the `Tokens` (or `Components`) collection, then alias to semantic tokens (not directly to primitives).

Component tokens should almost never alias directly to primitives. If you find yourself aliasing a component token to a primitive, check whether a semantic token should be created first.

---

## Step 6 — Verify

After writing, run a verification pass:

```
figma_browse_tokens(fileUrl: <current file>)
```

Check:
- All expected tokens are present
- Alias chains are intact (gray box indicator in Figma = alias is set)
- Both modes have values (no empty/unset mode values)
- Token names match the naming convention from `foundation.md`

Report any discrepancies and fix before closing.

---

## Step 7 — Report and write back

Tell the designer:
- How many variables were created
- Which collections they're in
- Whether any tokens failed to create (and why)
- Next recommended step (e.g. run `token-audit` to validate, or continue with next category in `token-generate`)

Write the Figma-assigned variable IDs back to the proposal file under `figma_ids.variable_ids` and set `meta.status = "pushed"` and `meta.pushed_at` to the current timestamp. This allows `diff_tokens.py` and `token-audit` to reference the same source of truth.

Optionally generate the CSS output now:
```bash
python "${CLAUDE_SKILL_DIR}/../_shared/scripts/tokens_to_css.py" token-proposal-[category].json --format css --all-modes --out tokens-[category].css
```

---

## Error handling

**"Variable already exists"** — Do not overwrite blindly. Check whether the existing variable matches the intended value. If it differs, flag it and ask the designer whether to update or skip.

**"Invalid alias — variable not found"** — The primitive being aliased doesn't exist yet. Create primitives before semantics, semantics before component tokens. Always push in tier order.

**"Rate limit / timeout"** — Split into smaller batches. Create ~25–30 variables per batch call.

**"Color value out of range"** — Figma's color values are 0–1. Check your hex-to-float conversion. Example: `255` → `1.0`, `128` → `0.502`.
