#!/usr/bin/env python3
"""
resolve_contrast.py
-------------------
Grounding helper for spec-generator's Accessibility section (Ground phase).

Resolves a foreground/background pair to concrete colors and computes the WCAG
2.1 contrast ratio. This is what lets the spec emit a real ratio and a ✅/❌
instead of a "[verify against token values]" placeholder.

Two modes:

  1. Literal colors — pass hex or rgb() values directly:
        python resolve_contrast.py --pair "#1a1a1a" "#ffffff"

  2. Token chains — pass token names (without leading dashes) plus a token
     file; the tool walks the var() chain (semantic → primitive → value)
     before computing:
        python resolve_contrast.py --tokens tokens.css \\
            --pair content-primary surface-page

     Names are normalized to `--name` for lookup, so `content-primary` and
     `--content-primary` are equivalent. Bare names avoid the shell/argparse
     ambiguity of arguments that start with a dash.

A pair whose chain cannot be resolved reports `unresolved` and names the token
where resolution stopped — the exact signal the spec renders as
`[unresolved — chain ends at --token]`. It never silently passes.

Supported token files: CSS custom properties (`--name: value;`) and flat JSON
maps (`{"--name": "value"}` or `{"name": "value"}`). Supported colors: #rgb,
#rrggbb, #rrggbbaa, rgb()/rgba(), and the keywords white/black/transparent.

Usage:
    python resolve_contrast.py --pair FG BG [--tokens FILE] [--label "where used"]
    python resolve_contrast.py --tokens tokens.css --pair fg-token bg-token

Output (JSON): one object per pair with resolved colors, ratio, and pass flags.
"""

import argparse
import json
import re
import sys
from pathlib import Path

_HEX = re.compile(r"^#([0-9a-fA-F]{3,8})$")
_RGB = re.compile(r"^rgba?\(([^)]+)\)$", re.IGNORECASE)
_VAR = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+?))?\s*\)", re.IGNORECASE)
_KEYWORDS = {"white": "#ffffff", "black": "#000000"}


# ---------------------------------------------------------------------------
# Token file parsing
# ---------------------------------------------------------------------------

def load_tokens(path: Path) -> dict[str, str]:
    """Parse a CSS custom-property file or flat JSON map into name → raw value."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        return {_normalize_name(k): str(v) for k, v in _flatten(data).items()}
    # CSS: strip comments, then grab `--name: value;` declarations.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    tokens: dict[str, str] = {}
    for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        tokens[name.strip()] = value.strip()
    return tokens


def _flatten(data, prefix: str = "") -> dict:
    out: dict[str, str] = {}
    if isinstance(data, dict):
        # DTCG-style {"$value": ...} leaf.
        if "$value" in data and not isinstance(data["$value"], (dict, list)):
            out[prefix] = data["$value"]
            return out
        for key, value in data.items():
            if key.startswith("$"):
                continue
            child = f"{prefix}-{key}" if prefix else key
            out.update(_flatten(value, child))
    else:
        out[prefix] = data
    return out


def _normalize_name(name: str) -> str:
    name = name.strip()
    return name if name.startswith("--") else f"--{name}"


# ---------------------------------------------------------------------------
# Chain resolution
# ---------------------------------------------------------------------------

class Unresolved(Exception):
    def __init__(self, token: str):
        self.token = token
        super().__init__(token)


def resolve(value: str, tokens: dict[str, str], _seen: set[str] | None = None) -> tuple[str, list[str]]:
    """Resolve a value or token name to a concrete color. Returns (color, chain)."""
    _seen = _seen or set()
    chain: list[str] = []
    value = value.strip()

    # A bare token name (starts with --) is looked up in the token file.
    if value.startswith("--"):
        chain.append(value)
        if value in _seen:
            raise Unresolved(value)  # cycle
        _seen.add(value)
        if value not in tokens:
            raise Unresolved(value)
        color, rest = resolve(tokens[value], tokens, _seen)
        return color, chain + rest

    # A var() reference: follow the token, honoring a fallback if present.
    m = _VAR.search(value)
    if m:
        ref, fallback = m.group(1), m.group(2)
        if ref in tokens and ref not in _seen:
            return resolve(ref, tokens, _seen)
        if fallback:
            return resolve(fallback, tokens, _seen)
        raise Unresolved(ref)

    # Otherwise it should already be a concrete color.
    if parse_color(value) is None:
        raise Unresolved(value)
    return value, chain


# ---------------------------------------------------------------------------
# Color math (WCAG 2.1)
# ---------------------------------------------------------------------------

def parse_color(value: str) -> tuple[int, int, int] | None:
    value = value.strip().lower()
    if value in _KEYWORDS:
        value = _KEYWORDS[value]
    m = _HEX.match(value)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) in (6, 8):
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return None
    m = _RGB.match(value)
    if m:
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",")]
        try:
            return tuple(int(round(float(p.rstrip("%")) * (2.55 if "%" in p else 1))) for p in parts[:3])
        except ValueError:
            return None
    return None


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        cs = c / 255
        return cs / 12.92 if cs <= 0.03928 else ((cs + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    l1, l2 = _luminance(fg), _luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Pair evaluation
# ---------------------------------------------------------------------------

def _endpoint(value: str) -> str:
    """Normalize a pair endpoint: a bare token name becomes `--name` for lookup.
    Literal colors and var() expressions pass through unchanged."""
    value = value.strip()
    if value.startswith("--") or "var(" in value or parse_color(value) is not None:
        return value
    return f"--{value}"


def evaluate(fg: str, bg: str, tokens: dict[str, str], label: str | None) -> dict:
    fg, bg = _endpoint(fg), _endpoint(bg)
    result: dict = {"foreground": fg, "background": bg}
    if label:
        result["label"] = label
    try:
        fg_color, fg_chain = resolve(fg, tokens)
        bg_color, bg_chain = resolve(bg, tokens)
    except Unresolved as e:
        result["resolved"] = False
        result["unresolvedAt"] = e.token
        result["marker"] = f"[unresolved — chain ends at {e.token}]"
        return result

    fg_rgb, bg_rgb = parse_color(fg_color), parse_color(bg_color)
    ratio = round(contrast_ratio(fg_rgb, bg_rgb), 2)
    result.update(
        resolved=True,
        foregroundValue=fg_color,
        backgroundValue=bg_color,
        ratio=ratio,
        display=f"{ratio}:1",
        passes={
            "AA_text": ratio >= 4.5,        # normal text
            "AA_large": ratio >= 3.0,       # large text (≥18.66px bold / 24px)
            "AA_ui": ratio >= 3.0,          # UI components and focus indicators
            "AAA_text": ratio >= 7.0,
        },
    )
    if fg_chain[1:] or bg_chain[1:]:
        result["chain"] = {"foreground": fg_chain, "background": bg_chain}
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pair", nargs=2, action="append", metavar=("FG", "BG"),
                        required=True, help="A foreground/background pair (repeatable)")
    parser.add_argument("--tokens", help="Token file (CSS custom properties or flat JSON)")
    parser.add_argument("--label", action="append", default=[],
                        help="Optional label per --pair, in order")
    args = parser.parse_args(argv)

    tokens: dict[str, str] = {}
    if args.tokens:
        token_path = Path(args.tokens)
        if not token_path.exists():
            print(json.dumps({"error": f"token file not found: {token_path}"}))
            return 1
        tokens = load_tokens(token_path)

    results = []
    for i, (fg, bg) in enumerate(args.pair):
        label = args.label[i] if i < len(args.label) else None
        results.append(evaluate(fg, bg, tokens, label))

    print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
