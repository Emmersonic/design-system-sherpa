#!/usr/bin/env python3
"""
hex_to_figma.py — Convert token proposal values to Figma API format.

Reads a token-proposal.json (or a partial one), converts all primitive COLOR
values from hex strings to Figma's {r,g,b,a} format (0-1 range), and writes
the result back with `figma_value` fields populated.

Also usable as a library: import `hex_to_figma` and call it directly.

Usage:
    python hex_to_figma.py token-proposal.json
    python hex_to_figma.py token-proposal.json --out token-proposal-converted.json
    python hex_to_figma.py --color "#3B82F6"          # single color, prints result
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def hex_to_figma(hex_str: str) -> dict:
    """
    Convert a CSS hex color string to Figma's {r, g, b, a} format (0-1 range).

    Accepts: #RGB, #RGBA, #RRGGBB, #RRGGBBAA
    Returns: {"r": float, "g": float, "b": float, "a": float}
    Raises:  ValueError on unrecognised format.
    """
    hex_str = hex_str.strip().lstrip("#")

    # Expand shorthand
    if len(hex_str) in (3, 4):
        hex_str = "".join(c * 2 for c in hex_str)

    if len(hex_str) == 6:
        hex_str += "ff"

    if len(hex_str) != 8 or not re.fullmatch(r"[0-9a-fA-F]{8}", hex_str):
        raise ValueError(f"Unrecognised hex color format: #{hex_str!r}")

    r = int(hex_str[0:2], 16) / 255
    g = int(hex_str[2:4], 16) / 255
    b = int(hex_str[4:6], 16) / 255
    a = int(hex_str[6:8], 16) / 255

    # Round to 3 decimal places — matches Figma's own export precision
    return {"r": round(r, 3), "g": round(g, 3), "b": round(b, 3), "a": round(a, 3)}


def figma_to_hex(figma_color: dict) -> str:
    """
    Convert a Figma {r,g,b,a} color back to a CSS hex string.
    Useful for round-trip validation.
    """
    r = round(figma_color["r"] * 255)
    g = round(figma_color["g"] * 255)
    b = round(figma_color["b"] * 255)
    a = round(figma_color.get("a", 1.0) * 255)
    if a == 255:
        return f"#{r:02X}{g:02X}{b:02X}"
    return f"#{r:02X}{g:02X}{b:02X}{a:02X}"


def process_proposal(proposal: dict) -> tuple:
    """
    Walk a token-proposal.json dict and populate `figma_value` on all
    COLOR primitives. Leaves non-COLOR and already-converted tokens untouched.
    Returns (updated_proposal, list_of_warnings).
    """
    warnings = []
    for token in proposal.get("primitives", []):
        token_type = token.get("type", "")
        value = token.get("value")

        if token_type != "COLOR":
            if "figma_value" not in token:
                token["figma_value"] = value
            continue

        if "figma_value" in token:
            continue

        if not isinstance(value, str):
            warnings.append(f"  SKIP  {token.get('name', '?')} -- COLOR token has non-string value: {value!r}")
            continue

        try:
            token["figma_value"] = hex_to_figma(value)
        except ValueError as exc:
            warnings.append(f"  WARN  {token.get('name', '?')} -- {exc}")

    return proposal, warnings


def main():
    parser = argparse.ArgumentParser(description="Convert token-proposal.json hex colors to Figma {r,g,b,a} format.")
    parser.add_argument("input", nargs="?", help="Path to token-proposal.json (reads stdin if omitted)")
    parser.add_argument("--out", help="Output path (overwrites input file if omitted)")
    parser.add_argument("--color", help="Convert a single hex color and print the result")
    args = parser.parse_args()

    if args.color:
        try:
            print(json.dumps(hex_to_figma(args.color), indent=2))
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    if args.input:
        input_path = Path(args.input)
        proposal = json.loads(input_path.read_text())
    else:
        proposal = json.loads(sys.stdin.read())
        input_path = None

    proposal, warnings = process_proposal(proposal)
    for w in warnings:
        print(w, file=sys.stderr)

    output = json.dumps(proposal, indent=2)
    out_path = Path(args.out) if args.out else input_path
    if out_path:
        out_path.write_text(output)
        print(f"Written to {out_path}  ({len(proposal.get('primitives', []))} primitives)")
    else:
        print(output)


if __name__ == "__main__":
    main()
