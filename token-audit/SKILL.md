---
name: token-audit
description: Audit an existing Figma design token system for health issues — including naming violations, orphaned tokens, broken aliases, missing mode values, primitives applied directly to layers, and documentation drift. Use this skill when someone wants to check the health of their token system, review what tokens exist, catch inconsistencies, update their changelog, or assess whether any changes are breaking. Also use when someone asks to "audit my tokens", "check my design system", "what tokens are missing", "find broken aliases", or wants to do a periodic review of their token set.
---

# Token Audit

A single-pass health check of an existing token system. Covers drift detection, naming validation, alias integrity, mode coverage, documentation, and versioning impact.

Run this periodically (e.g. after adding a new component, before a release, or when something feels off). Output is a structured report — use `token-push` to apply any fixes.

---

## Prerequisites

- A Figma file connected via the MCP
- Ideally, a `foundation.md` from `token-foundation` to check naming against
- Optionally, a previous audit report or changelog to diff against

---

## Step 1 — Pull current token state

Start with a summary to get collection names, counts, and mode structure without loading all variable data:

```
figma_get_variables(fileUrl: <current file>, format: "summary")
```

Then load each collection's variables using `format: "filtered"` to avoid fetching everything at once. For large libraries (200+ variables) this is significantly faster:

```
figma_get_variables(fileUrl: <current file>, format: "filtered", collection: "Primitives", verbosity: "standard")
figma_get_variables(fileUrl: <current file>, format: "filtered", collection: "Tokens", verbosity: "standard")
```

Repeat for each collection present. Note:
- Collection names and mode names
- Total variable count per collection
- All variable names

---

## Step 2 — Run checks

Work through each check category and collect findings. Record every issue with: the token name, the problem, and the recommended fix.

### Check 1 — Naming convention violations

Compare every token name against the naming rules in `foundation.md`.

Flag tokens that:
- Use camelCase or PascalCase instead of kebab-case: `backgroundColor` → should be `color/surface/default`
- Use appearance names in semantic tier: `color/blue-primary` → should describe intent
- Use hyphens as tier separators instead of slashes: `color-surface-brand` → `color/surface/brand`
- Use abbreviations: `bg`, `txt`, `btn`, `pri`, `sec`
- Include raw values in names: `color/16px-radius`, `color/333333`
- Put state before property: `hover-background` → should be `background/.../hover`

### Check 2 — Broken aliases

For every semantic and component token, verify the alias target exists.

Flag tokens where:
- The aliased primitive no longer exists (was renamed or deleted)
- The alias chain is broken mid-chain (semantic → missing primitive)
- A component token aliases a primitive directly instead of a semantic token

### Check 3 — Missing mode values

For every token in the `Tokens` collection, check that all modes have a value set.

Flag tokens where:
- One or more modes have no value (empty/unset)
- One mode uses a raw value but another uses an alias (inconsistency)

### Check 4 — Primitives applied directly to layers

Use `figma_audit_design_system` if available, or manually check by scanning whether any layers in the connected file use primitive tokens directly (e.g. `color/blue/500` applied to a text layer, bypassing the semantic tier).

Flag: any layer using a primitive token directly.
Recommend: remap to the appropriate semantic token.

### Check 5 — Orphaned tokens

Identify tokens that are defined but not used anywhere in the file (no layers reference them, and they are not aliased by any other token).

Flag orphaned tokens. Ask the designer: keep (for future use), deprecate (add `$deprecated` note), or delete?

### Check 6 — Coverage gaps

Compare the token set against the expected coverage from `foundation.md`.

Flag missing tokens:
- Expected semantic subcategories with no tokens (e.g. `color/icon/` was planned but not created)
- Expected component states not covered (e.g. `button/background/primary/focus` missing)
- Categories from `foundation.md` that have no tokens at all yet

### Check 7 — Documentation drift

Check whether the `foundation.md` and any changelog match the actual state of the file.

Flag:
- Tokens that exist in Figma but aren't in `foundation.md`
- Decisions log entries that seem outdated based on current token structure

---

## Step 3 — Versioning impact assessment

For each finding, classify the change type using semantic versioning logic:

| Change type | Version impact | Examples |
|---|---|---|
| New token added | **Patch** | New `color/surface/info` |
| Alias value updated (light mode) | **Patch** | `color/surface/brand` now points to `blue/600` instead of `blue/500` |
| New mode added | **Minor** | Added `high-contrast` mode |
| Token renamed | **Major (breaking)** | `color/bg/primary` → `color/surface/default` |
| Token deleted | **Major (breaking)** | Removing `color/text/muted` |
| Semantic token now aliases different primitive tier | **Minor** | Now uses a darker shade |

Aggregate to the highest applicable level and note whether this audit cycle results in a patch, minor, or major version bump.

---

## Step 4 — Produce the audit report

Before writing the report manually, run the diff script if a previous proposal snapshot exists:

```bash
python "${CLAUDE_SKILL_DIR}/../_shared/scripts/diff_tokens.py" token-proposal-[category]-prev.json token-proposal-[category].json --format markdown
```

This generates the changelog entry and version impact classification automatically. Use its output as the basis for the report's **Changelog entry** and **Version impact** sections.

Then output the full structured report:

```markdown
# Token audit — [date]

## Summary
- Collections: [list]
- Total tokens: [N] (Primitives: N, Tokens: N)
- Issues found: [N] (Critical: N, Warnings: N, Info: N)
- Version impact: [patch / minor / major]

## Critical issues (must fix)
- [token name]: [problem] → [recommended fix]

## Warnings (should fix)
- [token name]: [problem] → [recommended fix]

## Info (consider)
- [token name]: [observation]

## Changelog entry
### [version] — [date]
**Changed**
- [description]
**Added**
- [description]
**Deprecated**
- [description]
**Breaking**
- [description]

## Coverage gaps
- [missing tokens to create]
```

---

## Step 5 — Confirm fixes

Present the report. Ask the designer:
1. Which critical issues should be fixed now?
2. Which orphaned tokens should be kept, deprecated, or deleted?
3. Which coverage gaps should be filled in this cycle?

For any agreed fixes that change token values or aliases, proceed to `token-push` to apply them.
For new tokens to be added, use `token-generate` to produce the proposal, then `token-push`.

---

## Deprecation pattern

When a token should be removed but may still be in use:

1. Don't delete it yet
2. Update its description in Figma to: `DEPRECATED: use [new-token-name] instead`
3. Set its value to alias the replacement token
4. Document in the changelog as deprecated
5. In the next major version cycle, delete the deprecated tokens

This gives consuming teams (code, other Figma files) one version cycle to migrate.
