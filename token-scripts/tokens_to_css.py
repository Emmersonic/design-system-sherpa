#!/usr/bin/env python3
"""
tokens_to_css.py
----------------
Exports a token proposal JSON to platform-ready code output.

Supported formats:
  css   — CSS custom properties with :root and [data-theme] blocks
  scss  — SCSS variables ($token-name: value)
  js    — ES module export (const tokens = {...})
  ts    — TypeScript const with type annotation
  json  — W3C Design Token Community Group (DTCG) format

Usage:
    python tokens_to_css.py proposal.json --format css
    python tokens_to_css.py proposal.json --format scss
    python tokens_to_css.py proposal.json --format js
    python tokens_to_css.py proposal.json --format ts
    python tokens_to_css.py proposal.json --format json
    python tokens_to_css.py proposal.json --format css --mode light --out tokens.css
    python tokens_to_css.py proposal.json --format css --all-modes  # generates one block per mode
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def token_name_to_css_var(name: str) -> str:
    """'color/surface/default' → '--color-surface-default'"""
    return "--" + name.replace("/", "-")


def token_name_to_scss_var(name: str) -> str:
    """'color/surface/default' → '$color-surface-default'"""
    return "$" + name.replace("/", "-")


def token_name_to_js_key(name: str) -> str:
    """'color/surface/default' → 'colorSurfaceDefault' (camelCase)"""
    parts = name.replace("/", "-").split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def figma_color_to_hex(fc: dict) -> str:
    r = round(fc["r"] * 255)
    g = round(fc["g"] * 255)
    b = round(fc["b"] * 255)
    a = fc.get("a", 1.0)
    hex_str = f"#{r:02X}{g:02X}{b:02X}"
    if a < 1.0:
        hex_str += f"{round(a * 255):02X}"
    return hex_str


def resolve_primitive_value(token: dict) -> str:
    """Get a CSS-ready string value for a primitive token."""
    t = token.get("type", "").upper()
    raw = token.get("value")
    figma_val = token.get("figma_value")

    if t == "COLOR":
        if figma_val:
            return figma_color_to_hex(figma_val)
        if isinstance(raw, str) and raw.startswith("#"):
            return raw
        return str(raw)
    elif t == "FLOAT":
        # Infer unit from token name
        name = token.get("name", "")
        if any(seg in name for seg in ["font-size", "line-height", "letter-spacing"]):
            return f"{raw}px" if isinstance(raw, (int, float)) else str(raw)
        elif "font-weight" in name:
            return str(raw)
        elif "opacity" in name:
            return str(raw)
        elif any(seg in name for seg in ["spacing", "border-radius", "size", "width", "height"]):
            return f"{raw}px" if isinstance(raw, (int, float)) else str(raw)
        else:
            return str(raw)
    elif t == "STRING":
        return str(raw)
    elif t == "BOOLEAN":
        return "true" if raw else "false"

    return str(raw) if raw is not None else ""


def build_primitive_value_map(proposal: dict) -> dict[str, str]:
    """Returns {token_name: css_value} for all primitives."""
    mapping = {}
    for token in proposal.get("collections", {}).get("primitives", []) or []:
        name = token.get("name", "")
        if name:
            mapping[name] = resolve_primitive_value(token)
    return mapping


def resolve_alias_value(alias_target: str, primitive_map: dict) -> str:
    """
    Resolve an alias chain to a concrete value.
    For CSS output we use var() references for semantic tokens.
    For SCSS/JS we resolve to the actual value.
    """
    return primitive_map.get(alias_target, alias_target)


# ---------------------------------------------------------------------------
# CSS output
# ---------------------------------------------------------------------------

def generate_css(proposal: dict, mode_filter: str | None = None, all_modes: bool = False) -> str:
    primitive_map = build_primitive_value_map(proposal)
    lines = []
    meta = proposal.get("meta", {})

    lines.append(f"/* Token system — {meta.get('category', 'all')} */")
    lines.append(f"/* Generated from proposal v{meta.get('version', '?')} */")
    lines.append("")

    # --- Primitive variables (always in :root, never change) ---
    prim_lines = []
    for token in proposal.get("collections", {}).get("primitives", []) or []:
        name = token.get("name", "")
        value = resolve_primitive_value(token)
        if name and value:
            prim_lines.append(f"  {token_name_to_css_var(name)}: {value};")

    if prim_lines:
        lines.append("/* Primitives — raw values, do not use directly in components */")
        lines.append(":root {")
        lines.extend(prim_lines)
        lines.append("}")
        lines.append("")

    # --- Semantic / component tokens ---
    all_alias_tokens = (
        (proposal.get("collections", {}).get("tokens", []) or []) +
        (proposal.get("collections", {}).get("components", []) or [])
    )

    if not all_alias_tokens:
        return "\n".join(lines)

    # Collect all mode names
    all_modes_set: set[str] = set()
    for t in all_alias_tokens:
        all_modes_set.update(t.get("modes", {}).keys())
    mode_names = sorted(all_modes_set)

    if not mode_names:
        return "\n".join(lines)

    # Determine which modes to output
    modes_to_output = mode_names if (all_modes or mode_filter is None) else [mode_filter]

    for i, mode in enumerate(modes_to_output):
        selector = ":root" if i == 0 else f'[data-theme="{mode}"]'
        comment = f"/* {mode.capitalize()} mode */" if len(modes_to_output) > 1 else "/* Semantic tokens */"
        mode_lines = []

        for token in all_alias_tokens:
            name = token.get("name", "")
            alias_target = (token.get("modes") or {}).get(mode)
            if not name or alias_target is None:
                continue

            # Reference the primitive as a var()
            css_name = token_name_to_css_var(name)
            css_target = token_name_to_css_var(alias_target)
            mode_lines.append(f"  {css_name}: var({css_target});")

        if mode_lines:
            lines.append(comment)
            lines.append(f"{selector} {{")
            lines.extend(mode_lines)
            lines.append("}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SCSS output
# ---------------------------------------------------------------------------

def generate_scss(proposal: dict, mode: str | None = None) -> str:
    primitive_map = build_primitive_value_map(proposal)
    lines = []
    meta = proposal.get("meta", {})

    lines.append(f"// Token system — {meta.get('category', 'all')}")
    lines.append(f"// Generated from proposal v{meta.get('version', '?')}")
    lines.append("")

    # Primitives
    prims = proposal.get("collections", {}).get("primitives", []) or []
    if prims:
        lines.append("// Primitives")
        for token in prims:
            name = token.get("name", "")
            value = resolve_primitive_value(token)
            if name and value:
                lines.append(f"{token_name_to_scss_var(name)}: {value};")
        lines.append("")

    # Semantic/component in requested mode
    all_alias = (
        (proposal.get("collections", {}).get("tokens", []) or []) +
        (proposal.get("collections", {}).get("components", []) or [])
    )
    if not all_alias:
        return "\n".join(lines)

    # Default to first mode if none specified
    if mode is None:
        first = all_alias[0].get("modes", {})
        mode = next(iter(first), None)

    if mode:
        lines.append(f"// Semantic tokens — {mode} mode")
        for token in all_alias:
            name = token.get("name", "")
            alias_target = (token.get("modes") or {}).get(mode)
            if not name or alias_target is None:
                continue
            # Resolve to concrete value for SCSS
            value = primitive_map.get(alias_target, alias_target)
            lines.append(f"{token_name_to_scss_var(name)}: {value};")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JS / TS output
# ---------------------------------------------------------------------------

def generate_js(proposal: dict, mode: str | None = None, typescript: bool = False) -> str:
    primitive_map = build_primitive_value_map(proposal)
    lines = []
    meta = proposal.get("meta", {})

    lang = "TypeScript" if typescript else "JavaScript"
    lines.append(f"// Token system — {meta.get('category', 'all')} ({lang})")
    lines.append(f"// Generated from proposal v{meta.get('version', '?')}")
    lines.append("")

    all_tokens = (
        (proposal.get("collections", {}).get("primitives", []) or []) +
        (proposal.get("collections", {}).get("tokens", []) or []) +
        (proposal.get("collections", {}).get("components", []) or [])
    )

    if mode is None:
        first_alias = next(
            (t for t in all_tokens if "modes" in t and t["modes"]),
            None
        )
        mode = next(iter(first_alias["modes"]), None) if first_alias else None

    entries = []
    for token in all_tokens:
        name = token.get("name", "")
        if "value" in token:
            value = resolve_primitive_value(token)
        elif "modes" in token and mode:
            alias_target = (token.get("modes") or {}).get(mode)
            value = primitive_map.get(alias_target, alias_target) if alias_target else None
        else:
            continue

        if name and value is not None:
            key = token_name_to_js_key(name)
            entries.append((key, value))

    type_ann = ": Record<string, string>" if typescript else ""
    lines.append(f"export const tokens{type_ann} = {{")
    for key, value in entries:
        lines.append(f'  {key}: "{value}",')
    lines.append("};")
    lines.append("")
    lines.append("export default tokens;")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# W3C DTCG JSON output
# ---------------------------------------------------------------------------

def generate_dtcg_json(proposal: dict) -> str:
    """
    W3C Design Token Community Group format.
    Each token is an object with $value and $type.
    Aliases use {token.name} syntax.
    """
    result = {}

    def nest(d: dict, path: list[str], value):
        key = path[0]
        if len(path) == 1:
            d[key] = value
        else:
            if key not in d:
                d[key] = {}
            nest(d[key], path[1:], value)

    all_tokens = (
        (proposal.get("collections", {}).get("primitives", []) or []) +
        (proposal.get("collections", {}).get("tokens", []) or []) +
        (proposal.get("collections", {}).get("components", []) or [])
    )

    for token in all_tokens:
        name = token.get("name", "")
        if not name:
            continue

        t = (token.get("type") or "").upper()
        dtcg_type = {"COLOR": "color", "FLOAT": "number", "STRING": "string", "BOOLEAN": "boolean"}.get(t, "other")

        if "value" in token:
            raw = token.get("value")
            figma_val = token.get("figma_value")
            if t == "COLOR" and figma_val:
                val = figma_color_to_hex(figma_val)
            elif t == "COLOR" and isinstance(raw, str) and raw.startswith("#"):
                val = raw
            else:
                val = raw
            entry = {"$value": val, "$type": dtcg_type}
        elif "modes" in token:
            # Use first mode's alias for $value, note it's aliased
            modes = token.get("modes") or {}
            first_mode = next(iter(modes), None)
            if first_mode:
                target = modes[first_mode]
                # DTCG alias syntax: {path.to.token} using dots
                dtcg_ref = "{" + target.replace("/", ".") + "}"
                entry = {"$value": dtcg_ref, "$type": dtcg_type}
                if len(modes) > 1:
                    entry["$extensions"] = {
                        "modes": {mode: "{" + alias.replace("/", ".") + "}" for mode, alias in modes.items()}
                    }
            else:
                continue
        else:
            continue

        if token.get("description"):
            entry["$description"] = token["description"]

        path = name.split("/")
        nest(result, path, entry)

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Export a token proposal to platform code.")
    parser.add_argument("file", help="Path to token proposal JSON")
    parser.add_argument("--format", choices=["css", "scss", "js", "ts", "json"], default="css")
    parser.add_argument("--mode", help="Which mode to use for resolved values (e.g. 'light')")
    parser.add_argument("--all-modes", action="store_true", help="CSS only: output all modes with data-theme selectors")
    parser.add_argument("--out", help="Output file path (prints to stdout if omitted)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    proposal = json.loads(path.read_text())

    fmt = args.format
    if fmt == "css":
        output = generate_css(proposal, mode_filter=args.mode, all_modes=args.all_modes)
    elif fmt == "scss":
        output = generate_scss(proposal, mode=args.mode)
    elif fmt == "js":
        output = generate_js(proposal, mode=args.mode, typescript=False)
    elif fmt == "ts":
        output = generate_js(proposal, mode=args.mode, typescript=True)
    elif fmt == "json":
        output = generate_dtcg_json(proposal)
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Wrote {fmt} output to {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
