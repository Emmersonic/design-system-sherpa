#!/usr/bin/env python3
"""
hex_to_figma.py
---------------
Converts hex color values in a token proposal JSON to Figma's {r,g,b,a} float format
and writes the result back to the proposal file (or a new file).

Figma color values are 0–1 floats, not 0–255 integers.
This script populates the `figma_value` field on every COLOR primitive in the proposal,
so token-push can use them directly without doing math.

Usage:
    python hex_to_figma.py proposal.json
    python hex_to_figma.py proposal.json --out proposal-converted.json
    python hex_to_figma.py --hex "#3B82F6"          # single conversion, no file
    python hex_to_figma.py --hex "#3B82F680"        # with alpha (80 = 50% opacity)
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
    Convert a CSS hex color to a Figma RGBA dict with 0–1 float values.

    Accepts:
      #RGB       → expands to #RRGGBB
      #RGBA      → expands to #RRGGBBAA
      #RRGGBB    → standard 6-digit
      #RRGGBBAA  → with alpha channel

    Returns:
      {"r": float, "g": float, "b": float, "a": float}

    Raises:
      ValueError if the input is not a recognised hex format.
    """
    hex_str = hex_str.strip()
    if not hex_str.startswith("#"):
        raise ValueError(f"Expected hex color starting with '#', got: {hex_str!r}")

    h = hex_str[1:]  # strip the '#'

    # Expand shorthand
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    elif len(h) == 4:
        h = "".join(c * 2 for c in h)

    if len(h) == 6:
        h += "ff"  # fully opaque
    elif len(h) != 8:
        raise ValueError(f"Cannot parse hex color: {hex_str!r}")

    if not re.fullmatch(r"[0-9a-fA-F]{8}", h):
        raise ValueError(f"Invalid hex characters in: {hex_str!r}")

    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    a = int(h[6:8], 16) / 255

    return {
        "r": round(r, 4),
        "g": round(g, 4),
        "b": round(b, 4),
        "a": round(a, 4),
    }


def figma_to_hex(figma_color: dict) -> str:
    """
    Reverse conversion: Figma {r,g,b,a} → hex string.
    Useful for verification and audit diffing.
    """
    r = round(figma_color["r"] * 255)
    g = round(figma_color["g"] * 255)
    b = round(figma_color["b"] * 255)
    a = figma_color.get("a", 1.0)

    hex_rgb = f"#{r:02X}{g:02X}{b:02X}"
    if a < 1.0:
        hex_rgb += f"{round(a * 255):02X}"
    return hex_rgb


# ---------------------------------------------------------------------------
# Proposal processing
# ---------------------------------------------------------------------------

def process_proposal(proposal: dict) -> tuple[dict, list[str], list[str]]:
    """
    Walk a token proposal and populate `figma_value` on every COLOR primitive.

    Returns:
        (updated_proposal, converted_names, error_messages)
    """
    converted = []
    errors = []

    primitives = proposal.get("collections", {}).get("primitives", [])
    for token in primitives:
        if token.get("type") != "COLOR":
            continue

        raw = token.get("value")
        if not isinstance(raw, str) or not raw.startswith("#"):
            errors.append(f"  SKIP  {token.get('name', '?')!r}: value {raw!r} is not a hex color")
            continue

        try:
            token["figma_value"] = hex_to_figma(raw)
            converted.append(token["name"])
        except ValueError as e:
            errors.append(f"  ERROR {token.get('name', '?')!r}: {e}")

    return proposal, converted, errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert hex colors in a token proposal to Figma float format."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to token proposal JSON (reads stdin if omitted)",
    )
    parser.add_argument(
        "--out",
        help="Output path (defaults to overwriting the input file)",
    )
    parser.add_argument(
        "--hex",
        help="Convert a single hex value and print the result — no file needed",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="With --hex: interpret input as r,g,b,a floats and convert back to hex",
    )
    args = parser.parse_args()

    # --- Single value mode ---
    if args.hex:
        if args.reverse:
            parts = [float(x) for x in args.hex.split(",")]
            result = figma_to_hex({"r": parts[0], "g": parts[1], "b": parts[2], "a": parts[3] if len(parts) > 3 else 1.0})
            print(result)
        else:
            try:
                result = hex_to_figma(args.hex)
                print(json.dumps(result, indent=2))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        return

    # --- File mode ---
    if args.file:
        input_path = Path(args.file)
        if not input_path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        proposal = json.loads(input_path.read_text())
    else:
        proposal = json.load(sys.stdin)

    proposal, converted, errors = process_proposal(proposal)

    # Report
    print(f"\nhex_to_figma: processed {len(converted)} COLOR primitives")
    if converted:
        for name in converted:
            print(f"  ✓  {name}")
    if errors:
        print(f"\n{len(errors)} issue(s):")
        for msg in errors:
            print(msg)

    # Write output
    output_path = Path(args.out) if args.out else (Path(args.file) if args.file else None)
    if output_path:
        output_path.write_text(json.dumps(proposal, indent=2))
        print(f"\nWrote: {output_path}")
    else:
        print(json.dumps(proposal, indent=2))

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
