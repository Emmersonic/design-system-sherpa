# Figma Variables Reference

Reference for the `token-foundation` and `token-figma-scaffold` skills. Covers how Figma's variable system maps to the 3-tier token model.

---

## Collections

Each tier maps to a Figma variable collection:

| Collection name | Tier | Published? | Modes |
|---|---|---|---|
| `Primitives` | Primitive | Hidden | Single mode (values don't change) |
| `Tokens` | Semantic + Component | Yes | One per theme (light, dark, etc.) |

If component tokens are large or need separate governance, they can live in a third `Components` collection — but starting with everything in `Tokens` is simpler.

---

## Variable types

| Token category | Figma variable type |
|---|---|
| Color | Color |
| Spacing, sizing, border-radius | Number |
| Font size, line height | Number |
| Font weight | Number |
| Font family | String |
| Duration, easing | String |
| Boolean flags | Boolean |

**Note:** Figma does not support composite/typography variables. Text styles (heading, body, label, etc.) must remain as Figma **styles**, not variables. Use number variables for individual properties (font-size, line-height) and reference them in code, but use text styles for applying to layers.

---

## Modes

Modes in Figma represent the "contexts" in which tokens take different values. Each mode stores a complete set of values for every variable in the collection.

- **Primitives collection**: single mode only (primitive values never change between contexts)
- **Tokens collection**: one mode per theme — typically `light` and `dark`

To switch themes on a frame: select the frame → right sidebar → Local variables → switch mode.

### Dark mode strategy

Semantic tokens don't change names between modes — only their aliased value changes. Example:

```
color/surface/default
  light mode → color/neutral/0   (#FFFFFF)
  dark  mode → color/neutral/900 (#111827)
```

This is the correct approach. Do **not** create separate dark-mode token names like `color/surface/default-dark`.

---

## Scoping

Figma lets you restrict which properties a variable can be applied to. Use scoping to prevent misuse:

| Token | Recommended scope |
|---|---|
| `color/surface/*` | Fill color only |
| `color/text/*` | Text fill only |
| `color/border/*` | Stroke color only |
| `spacing/*` | Gap, padding, width, height |
| `border-radius/*` | Corner radius |
| `font-size/*` | Font size |

---

## Hiding primitives from publishing

Primitives should not be selectable in the design tool's property panel. To hide them:

1. Open the **Primitives** collection in the variable editor
2. Select all variables (Cmd+A)
3. Right-click → **Edit variables**
4. Uncheck **Show in all supported properties**
5. Check **Hide from publishing**

---

## Aliases (aliasing)

An alias is when one variable's value is set to reference another variable rather than a raw value. This is how the tier system works in Figma.

To create an alias:
1. Edit the semantic/component token's value
2. Instead of entering a raw value, click the variable picker icon
3. Select the primitive token to reference

Aliases update automatically when the source token changes. A gray box around a value in the variable panel indicates it is an alias.

---

## Variable groups

Figma uses the `/` character in variable names to create visual groups in the panel. The naming convention's `/` separators directly create the folder hierarchy in Figma:

```
color/
  surface/
    default
    secondary
    brand
  text/
    primary
    secondary
```

This is why the naming convention uses forward slashes — they're not just aesthetic, they control Figma's UI grouping.
