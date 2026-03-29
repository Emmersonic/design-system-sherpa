#!/usr/bin/env python3
"""
build_batch_payload.py
----------------------
Takes a token proposal JSON (conforming to token-schema.json) and produces
Figma-ready batch payloads for figma_batch_create_variables and
figma_batch_update_variables — chunked to avoid API timeouts.

This script handles:
  - Hex → Figma RGBA conversion (calls hex_to_figma logic inline)
  - Chunking into batches of ≤30 variables (configurable)
  - Tier-ordered output: primitives always before semantics/components
  - Separate payloads for creation vs. alias updates (Figma requires two passes)

Usage:
    python build_batch_payload.py proposal.json
    python build_batch_payload.py proposal.json --chunk-size 25
    python build_batch_payload.py proposal.json --tier primitives
    python build_batch_payload.py proposal.json --tier tokens
    python build_batch_payload.py proposal.json --out payloads/
    python build_batch_payload.py proposal.json --summary
"""

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_CHUNK_SIZE = 30


# ---------------------------------------------------------------------------
# Colour conversion (inline — no dependency on hex_to_figma.py)
# ---------------------------------------------------------------------------

def hex_to_figma(hex_str: str) -> dict:
    hex_str = hex_str.strip()
    if not hex_str.startswith("#"):
        raise ValueError(f"Not a hex color: {hex_str!r}")
    h = hex_str[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    elif len(h) == 4:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "ff"
    if len(h) != 8 or not re.fullmatch(r"[0-9a-fA-F]{8}", h):
        raise ValueError(f"Invalid hex: {hex_str!r}")
    return {
        "r": round(int(h[0:2], 16) / 255, 4),
        "g": round(int(h[2:4], 16) / 255, 4),
        "b": round(int(h[4:6], 16) / 255, 4),
        "a": round(int(h[6:8], 16) / 255, 4),
    }


def resolve_color_value(token: dict) -> dict | None:
    """
    Get the Figma-ready color value for a COLOR primitive.
    Uses pre-computed figma_value if present; otherwise converts from hex value.
    """
    if "figma_value" in token:
        return token["figma_value"]
    raw = token.get("value")
    if isinstance(raw, str) and raw.startswith("#"):
        return hex_to_figma(raw)
    return None


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

def build_creation_payload(token: dict, collection_id: str) -> dict | None:
    """
    Build the creation record for figma_batch_create_variables.
    Primitives only — alias tokens need a separate create+update pair.
    """
    token_type = token.get("type", "").upper()
    name = token.get("name", "")

    entry = {
        "name": name,
        "type": token_type,
        "collectionId": collection_id,
    }

    # Initial value for primitives
    if token_type == "COLOR":
        color = resolve_color_value(token)
        if color:
            entry["value"] = color
    elif token_type == "FLOAT":
        val = token.get("value")
        if val is not None:
            entry["value"] = float(val)
    elif token_type in ("STRING", "BOOLEAN"):
        val = token.get("value")
        if val is not None:
            entry["value"] = val

    # Optional metadata
    if token.get("description"):
        entry["description"] = token["description"]
    if token.get("scopes"):
        entry["scopes"] = token["scopes"]

    return entry


def build_alias_update_records(token: dict, token_id: str, mode_ids: dict[str, str], variable_ids: dict[str, str]) -> list[dict]:
    """
    Build update records for figma_batch_update_variables to set aliases per mode.
    Requires that both the token and its alias targets already exist in Figma.

    mode_ids:      { "light": "1:0", "dark": "1:1" }
    variable_ids:  { "color/blue/500": "VariableID:123:456" }
    """
    records = []
    for mode_name, alias_target in (token.get("modes") or {}).items():
        mode_id = mode_ids.get(mode_name)
        target_id = variable_ids.get(alias_target)

        if not mode_id:
            print(f"  WARNING: no mode ID for '{mode_name}' — skipping alias on '{token['name']}'", file=sys.stderr)
            continue
        if not target_id:
            print(f"  WARNING: no variable ID for alias target '{alias_target}' — skipping '{token['name']}' [{mode_name}]", file=sys.stderr)
            continue

        records.append({
            "variableId": token_id,
            "modeId": mode_id,
            "value": {
                "type": "VARIABLE_ALIAS",
                "id": target_id,
            },
        })

    return records


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def build_payloads(proposal: dict, chunk_size: int = DEFAULT_CHUNK_SIZE, tier_filter: str | None = None) -> dict:
    """
    Returns a structured dict with all payloads:
    {
      "creation_batches": {
        "primitives": [[batch], [batch], ...],
        "tokens": [[batch], ...],
        "components": [[batch], ...],
      },
      "alias_update_batches": {
        "tokens": [[batch], ...],
        "components": [[batch], ...],
      },
      "summary": { ... }
    }
    """
    collections = proposal.get("collections", {})
    figma_ids = proposal.get("figma_ids", {})
    collection_ids = figma_ids.get("collection_ids", {})
    mode_ids = figma_ids.get("mode_ids", {})
    variable_ids = figma_ids.get("variable_ids", {})

    result = {
        "creation_batches": {},
        "alias_update_batches": {},
        "summary": {
            "primitives_to_create": 0,
            "semantic_tokens_to_create": 0,
            "alias_updates_to_apply": 0,
            "total_api_calls": 0,
        },
    }

    # --- Primitives ---
    if tier_filter in (None, "primitives"):
        prim_coll_id = collection_ids.get("primitives", "PRIMITIVES_COLLECTION_ID")
        prim_entries = []

        for token in collections.get("primitives", []) or []:
            entry = build_creation_payload(token, prim_coll_id)
            if entry:
                prim_entries.append(entry)

        batches = chunk(prim_entries, chunk_size)
        result["creation_batches"]["primitives"] = batches
        result["summary"]["primitives_to_create"] = len(prim_entries)
        result["summary"]["total_api_calls"] += len(batches)

    # --- Semantic / component tokens ---
    for key in ("tokens", "components"):
        if tier_filter and tier_filter != key:
            continue

        coll_id = collection_ids.get(key, f"{key.upper()}_COLLECTION_ID")
        create_entries = []
        alias_records = []

        for token in collections.get(key, []) or []:
            name = token.get("name", "")

            # Creation (no value set yet — aliases are set in the update pass)
            create_entry = {
                "name": name,
                "type": token.get("type", "COLOR"),
                "collectionId": coll_id,
            }
            if token.get("description"):
                create_entry["description"] = token["description"]
            if token.get("scopes"):
                create_entry["scopes"] = token["scopes"]
            create_entries.append(create_entry)

            # Alias updates (requires variable_ids to be populated after creation)
            token_id = variable_ids.get(name, f"ID_FOR_{name.replace('/', '_').upper()}")
            records = build_alias_update_records(token, token_id, mode_ids, variable_ids)
            alias_records.extend(records)

        create_batches = chunk(create_entries, chunk_size)
        update_batches = chunk(alias_records, chunk_size)

        result["creation_batches"][key] = create_batches
        result["alias_update_batches"][key] = update_batches

        result["summary"]["semantic_tokens_to_create"] += len(create_entries)
        result["summary"]["alias_updates_to_apply"] += len(alias_records)
        result["summary"]["total_api_calls"] += len(create_batches) + len(update_batches)

    return result


def print_summary(payloads: dict, chunk_size: int):
    s = payloads["summary"]
    print(f"\nbuild_batch_payload summary")
    print(f"{'─'*40}")
    print(f"  Chunk size:               {chunk_size}")
    print(f"  Primitives to create:     {s['primitives_to_create']}")
    print(f"  Semantic tokens to create:{s['semantic_tokens_to_create']}")
    print(f"  Alias updates to apply:   {s['alias_updates_to_apply']}")
    print(f"  Total Figma API calls:    {s['total_api_calls']}")
    print()

    for tier, batches in payloads["creation_batches"].items():
        if batches:
            print(f"  {tier} creation: {len(batches)} batch(es) × ≤{chunk_size} variables")
    for tier, batches in payloads["alias_update_batches"].items():
        if batches:
            print(f"  {tier} alias updates: {len(batches)} batch(es)")
    print()


def write_payloads(payloads: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # Creation payloads
    for tier, batches in payloads["creation_batches"].items():
        for i, batch in enumerate(batches):
            path = out_dir / f"create_{tier}_batch_{i+1:02d}.json"
            path.write_text(json.dumps({"variables": batch}, indent=2))

    # Alias update payloads
    for tier, batches in payloads["alias_update_batches"].items():
        for i, batch in enumerate(batches):
            path = out_dir / f"update_{tier}_aliases_batch_{i+1:02d}.json"
            path.write_text(json.dumps({"updates": batch}, indent=2))

    # Summary
    summary_path = out_dir / "push_summary.json"
    summary_path.write_text(json.dumps(payloads["summary"], indent=2))

    print(f"Wrote payloads to {out_dir}/")
    print(f"  Run order: create primitives → create tokens → update aliases")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build Figma batch API payloads from a token proposal.")
    parser.add_argument("file", help="Path to token proposal JSON")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Max variables per batch call (default: {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--tier", choices=["primitives", "tokens", "components"],
                        help="Only build payloads for this tier")
    parser.add_argument("--out", help="Directory to write payload files to")
    parser.add_argument("--summary", action="store_true", help="Print summary only, no payload output")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    proposal = json.loads(path.read_text())

    payloads = build_payloads(proposal, chunk_size=args.chunk_size, tier_filter=args.tier)

    print_summary(payloads, args.chunk_size)

    if args.summary:
        return

    if args.out:
        write_payloads(payloads, Path(args.out))
    else:
        # Print to stdout as a single JSON object
        print(json.dumps(payloads, indent=2))


if __name__ == "__main__":
    main()
