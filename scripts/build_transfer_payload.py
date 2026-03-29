#!/usr/bin/env python3
"""
build_transfer_payload.py
-------------------------
Takes normalized variable data from a source and target Figma file and produces
batch payloads for figma_batch_create_variables and figma_batch_update_variables.

Input format (transfer-source.json / transfer-target.json):
{
  "collection": {
    "id": "VariableCollectionId:1:0",
    "name": "Tokens",
    "modes": [
      { "id": "1:0", "name": "Light" },
      { "id": "1:1", "name": "Dark" }
    ]
  },
  "variables": [
    {
      "id": "VariableID:1:1",
      "name": "color/surface/brand",
      "type": "COLOR",
      "description": "",
      "valuesByMode": {
        "Light": { "type": "VARIABLE_ALIAS", "targetName": "color/blue/500" },
        "Dark":  { "type": "VARIABLE_ALIAS", "targetName": "color/blue/600" }
      }
    }
  ]
}

Note: alias values must use "targetName" (the target variable's name), NOT the
source variable ID. Claude resolves IDs to names when producing transfer-source.json.

Transfer modes:
  overwrite  Update conflicts; delete target-only variables (with confirmation list)
  merge      Update conflicts; leave target-only variables untouched
  add        Skip conflicts; only add variables absent from target

Usage:
    python build_transfer_payload.py source.json target.json --mode merge
    python build_transfer_payload.py source.json target.json --mode overwrite --out payloads/
    python build_transfer_payload.py source.json target.json --mode add --chunk-size 25
    python build_transfer_payload.py source.json target.json --mode merge --summary
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_CHUNK_SIZE = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chunk(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def values_equal(a, b) -> bool:
    """Shallow equality check for Figma variable values."""
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        if a.get("type") == "VARIABLE_ALIAS" and b.get("type") == "VARIABLE_ALIAS":
            return a.get("targetName") == b.get("targetName")
        # Raw color: compare rounded to 3 decimal places
        if all(k in a for k in ("r", "g", "b")):
            return all(round(a.get(k, 0), 3) == round(b.get(k, 0), 3) for k in ("r", "g", "b", "a"))
        return a == b
    return a == b


def is_alias(value: dict) -> bool:
    return isinstance(value, dict) and value.get("type") == "VARIABLE_ALIAS"


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze(source_data: dict, target_data: dict, mode: str) -> dict:
    """
    Compare source and target variables within a collection and produce a
    per-variable action plan.

    Returns:
    {
      "source_modes": [...],
      "target_modes": [...],
      "mode_map": { "Light": "target_mode_id", ... },
      "missing_modes": ["High Contrast"],   # in target but not source
      "extra_modes": ["Legacy"],            # in source but not target
      "variables": [
        {
          "name": "color/surface/brand",
          "action": "add" | "update" | "skip" | "match" | "delete",
          "source": { ... } | null,
          "target_id": "VariableID:..." | null,
          "dangling_aliases": ["color/brand/vivid"]   # aliases with no target in destination
        }
      ],
      "dangling_aliases": { "color/brand/vivid": ["color/surface/brand", ...] }
    }
    """
    src_vars = {v["name"]: v for v in source_data.get("variables", [])}
    tgt_vars = {v["name"]: v for v in target_data.get("variables", [])}

    # All variable names in the target file (for alias remapping lookups)
    all_target_names = set(tgt_vars.keys())

    # Mode mapping: source mode name → target mode id
    src_modes = {m["name"]: m["id"] for m in source_data.get("collection", {}).get("modes", [])}
    tgt_modes = {m["name"]: m["id"] for m in target_data.get("collection", {}).get("modes", [])}

    mode_map = {}  # source mode name → target mode id
    for mode_name, _ in src_modes.items():
        if mode_name in tgt_modes:
            mode_map[mode_name] = tgt_modes[mode_name]

    missing_modes = [n for n in tgt_modes if n not in src_modes]  # target has, source doesn't
    extra_modes = [n for n in src_modes if n not in tgt_modes]    # source has, target doesn't

    # Track all dangling alias targets across the whole collection
    dangling_registry: dict[str, list[str]] = {}

    variable_plans = []

    # Variables in source
    for name, src_var in src_vars.items():
        tgt_var = tgt_vars.get(name)

        # Collect dangling aliases for this variable
        dangling = []
        for mode_name, val in src_var.get("valuesByMode", {}).items():
            if is_alias(val):
                target_name = val.get("targetName")
                if target_name and target_name not in all_target_names:
                    dangling.append(target_name)
                    dangling_registry.setdefault(target_name, [])
                    if name not in dangling_registry[target_name]:
                        dangling_registry[target_name].append(name)

        if tgt_var is None:
            # Not in target — always add
            variable_plans.append({
                "name": name,
                "action": "add",
                "source": src_var,
                "target_id": None,
                "dangling_aliases": dangling,
            })
        else:
            # Exists in both — check for value differences
            src_modes_vals = src_var.get("valuesByMode", {})
            tgt_modes_vals = tgt_var.get("valuesByMode", {})

            has_difference = False
            for mode_name in src_modes_vals:
                if mode_name in tgt_modes_vals:
                    if not values_equal(src_modes_vals[mode_name], tgt_modes_vals[mode_name]):
                        has_difference = True
                        break
                else:
                    has_difference = True
                    break

            if not has_difference:
                action = "match"
            elif mode == "add":
                action = "skip"
            else:
                # overwrite or merge: update conflicts
                action = "update"

            variable_plans.append({
                "name": name,
                "action": action,
                "source": src_var,
                "target_id": tgt_var["id"],
                "dangling_aliases": dangling,
            })

    # Variables only in target (overwrite mode: mark for deletion; others: leave)
    for name, tgt_var in tgt_vars.items():
        if name not in src_vars:
            variable_plans.append({
                "name": name,
                "action": "delete" if mode == "overwrite" else "target-only",
                "source": None,
                "target_id": tgt_var["id"],
                "dangling_aliases": [],
            })

    return {
        "source_modes": list(src_modes.items()),
        "target_modes": list(tgt_modes.items()),
        "mode_map": mode_map,
        "missing_modes": missing_modes,
        "extra_modes": extra_modes,
        "variables": variable_plans,
        "dangling_aliases": dangling_registry,
    }


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

def build_create_entry(var: dict, collection_id: str) -> dict:
    entry = {
        "name": var["name"],
        "type": var["type"],
        "collectionId": collection_id,
    }
    if var.get("description"):
        entry["description"] = var["description"]
    if var.get("scopes"):
        entry["scopes"] = var["scopes"]
    return entry


def build_value_updates(var: dict, var_id: str, mode_map: dict, target_name_to_id: dict) -> list[dict]:
    """Build update records for all modes of a variable."""
    updates = []
    for mode_name, val in var.get("valuesByMode", {}).items():
        mode_id = mode_map.get(mode_name)
        if not mode_id:
            print(f"  WARNING: no target mode ID for '{mode_name}' — skipping value for '{var['name']}'", file=sys.stderr)
            continue

        if is_alias(val):
            target_var_name = val.get("targetName")
            target_id = target_name_to_id.get(target_var_name)
            if not target_id:
                print(f"  WARNING: alias target '{target_var_name}' not found in target — skipping '{var['name']}' [{mode_name}]", file=sys.stderr)
                continue
            resolved_value = {"type": "VARIABLE_ALIAS", "id": target_id}
        else:
            resolved_value = val

        updates.append({
            "variableId": var_id,
            "modeId": mode_id,
            "value": resolved_value,
        })
    return updates


def build_payloads(plan: dict, source_data: dict, target_data: dict,
                   collection_id: str, chunk_size: int) -> dict:
    """
    Produces batch payloads from the analysis plan.
    Returns:
    {
      "create_batches": [[...], ...],
      "update_batches": [[...], ...],
      "delete_ids": [...],
      "summary": { ... }
    }
    """
    mode_map = plan["mode_map"]

    # name → id lookup for variables already in target (before any creates)
    # Used for remapping VARIABLE_ALIAS values
    existing_target: dict[str, str] = {v["name"]: v["id"] for v in target_data.get("variables", [])}

    # We'll also need IDs for variables we're about to create — placeholder IDs
    # are filled in by Claude after creation; we note them here so the update pass
    # can reference them by name.
    # The script marks them as PENDING so Claude knows to substitute IDs post-creation.

    create_entries_raw = []
    update_records_existing = []
    update_records_new = []  # deferred: needs IDs from creation step
    delete_ids = []

    # Separate raw-value and alias variables for ordering (raw first)
    def is_pure_alias_var(var: dict) -> bool:
        return all(is_alias(v) for v in var.get("valuesByMode", {}).values())

    vars_by_action = {
        "add_raw": [],
        "add_alias": [],
        "update_existing": [],
        "delete": [],
    }

    for entry in plan["variables"]:
        action = entry["action"]
        if action == "add":
            if is_pure_alias_var(entry["source"]):
                vars_by_action["add_alias"].append(entry)
            else:
                vars_by_action["add_raw"].append(entry)
        elif action in ("update", "match"):
            if action == "update":
                vars_by_action["update_existing"].append(entry)
        elif action == "delete":
            vars_by_action["delete"].append(entry)

    # --- Pass 1: create raw-value variables ---
    for entry in vars_by_action["add_raw"]:
        src = entry["source"]
        create_entries_raw.append(build_create_entry(src, collection_id))
        # Value updates deferred until IDs are known (marked as PENDING)
        update_records_new.append({
            "__pending_name": src["name"],  # Claude replaces this with real variableId post-creation
            "updates": build_value_updates(src, "PENDING", mode_map, existing_target),
        })

    # --- Pass 2: create alias variables ---
    create_entries_alias = []
    for entry in vars_by_action["add_alias"]:
        src = entry["source"]
        create_entries_alias.append(build_create_entry(src, collection_id))
        # Alias targets may be in existing_target OR in raw-value variables just created
        # Targets newly created won't have IDs yet — also marked PENDING
        update_records_new.append({
            "__pending_name": src["name"],
            "updates": build_value_updates(src, "PENDING", mode_map, existing_target),
        })

    # --- Update existing variables (overwrite/merge mode) ---
    for entry in vars_by_action["update_existing"]:
        src = entry["source"]
        target_id = entry["target_id"]
        update_records_existing.extend(
            build_value_updates(src, target_id, mode_map, existing_target)
        )

    # --- Deletions (overwrite mode) ---
    for entry in vars_by_action["delete"]:
        delete_ids.append(entry["target_id"])

    return {
        "create_batches_raw": chunk(create_entries_raw, chunk_size),
        "create_batches_alias": chunk(create_entries_alias, chunk_size),
        "update_batches_existing": chunk(update_records_existing, chunk_size),
        "pending_updates_new": update_records_new,  # needs IDs substituted post-creation
        "delete_ids": delete_ids,
        "summary": {
            "raw_variables_to_create": len(create_entries_raw),
            "alias_variables_to_create": len(create_entries_alias),
            "existing_variables_to_update": len(vars_by_action["update_existing"]),
            "variables_to_delete": len(delete_ids),
            "dangling_aliases": {k: v for k, v in plan["dangling_aliases"].items()},
            "extra_modes_in_source": plan["extra_modes"],
            "missing_modes_in_source": plan["missing_modes"],
        },
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_summary(plan: dict, payloads: dict, mode: str):
    variables = plan["variables"]
    counts = {a: sum(1 for v in variables if v["action"] == a)
              for a in ("add", "update", "skip", "match", "delete", "target-only")}

    print(f"\nbuild_transfer_payload summary")
    print(f"{'─' * 44}")
    print(f"  Transfer mode:              {mode}")
    print()
    print(f"  Variables to add:           {counts['add']}")
    print(f"  Variables to update:        {counts['update']}")
    print(f"  Variables to skip:          {counts['skip']}   (add mode only)")
    print(f"  Variables identical:        {counts['match']}   (no action)")
    print(f"  Variables to delete:        {counts['delete']}   (overwrite mode only)")
    print(f"  Target-only (kept):         {counts['target-only']}   (merge/add mode)")
    print()

    s = payloads["summary"]
    print(f"  Batch calls (create raw):   {len(payloads['create_batches_raw'])}")
    print(f"  Batch calls (create alias): {len(payloads['create_batches_alias'])}")
    print(f"  Batch calls (update):       {len(payloads['update_batches_existing'])}")
    print(f"  Pending post-create updates:{len(payloads['pending_updates_new'])}  (IDs needed after creation)")
    print()

    if s["extra_modes_in_source"]:
        print(f"  Modes in source, missing from target: {s['extra_modes_in_source']}")
        print(f"    → These modes must be created before transfer.")
    if s["missing_modes_in_source"]:
        print(f"  Modes in target, not in source: {s['missing_modes_in_source']}")
        print(f"    → Transferred variables will have no value for these modes.")
    if s["dangling_aliases"]:
        print(f"\n  Dangling aliases ({len(s['dangling_aliases'])} target(s) not in destination file):")
        for target_name, used_by in s["dangling_aliases"].items():
            print(f"    '{target_name}' — referenced by: {', '.join(used_by)}")
    print()


def write_payloads(plan: dict, payloads: dict, mode: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # Creation payloads
    for i, batch in enumerate(payloads["create_batches_raw"]):
        path = out_dir / f"create_raw_batch_{i+1:02d}.json"
        path.write_text(json.dumps({"variables": batch}, indent=2))

    for i, batch in enumerate(payloads["create_batches_alias"]):
        path = out_dir / f"create_alias_batch_{i+1:02d}.json"
        path.write_text(json.dumps({"variables": batch}, indent=2))

    # Update payloads (existing variables only; new ones need IDs first)
    for i, batch in enumerate(payloads["update_batches_existing"]):
        path = out_dir / f"update_existing_batch_{i+1:02d}.json"
        path.write_text(json.dumps({"updates": batch}, indent=2))

    # Pending updates (new variables — IDs must be filled in after creation)
    if payloads["pending_updates_new"]:
        path = out_dir / "pending_updates_new.json"
        path.write_text(json.dumps(payloads["pending_updates_new"], indent=2))

    # Delete list (overwrite mode)
    if payloads["delete_ids"]:
        path = out_dir / "delete_ids.json"
        path.write_text(json.dumps({"variable_ids": payloads["delete_ids"]}, indent=2))

    # Full transfer plan (for review)
    plan_path = out_dir / "transfer_plan.json"
    plan_path.write_text(json.dumps(plan["variables"], indent=2))

    # Summary
    summary_path = out_dir / "transfer_summary.json"
    summary_path.write_text(json.dumps(payloads["summary"], indent=2))

    print(f"Wrote payloads to {out_dir}/")
    print(f"  Run order:")
    print(f"    1. Create modes in target if needed (extra_modes_in_source)")
    print(f"    2. create_raw_batch_NN.json  → batch create raw-value variables")
    print(f"    3. Substitute real variable IDs into pending_updates_new.json")
    print(f"    4. create_alias_batch_NN.json → batch create alias variables")
    print(f"    5. update_existing_batch_NN.json → update existing conflicts")
    print(f"    6. Apply pending_updates_new.json (with real IDs)")
    if payloads["delete_ids"]:
        print(f"    7. Confirm deletions in delete_ids.json — then delete")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build Figma batch transfer payloads from normalized source/target variable data."
    )
    parser.add_argument("source", help="Path to transfer-source.json (normalized variables from source file)")
    parser.add_argument("target", help="Path to transfer-target.json (normalized variables from target file)")
    parser.add_argument(
        "--mode",
        choices=["overwrite", "merge", "add"],
        required=True,
        help="Conflict resolution mode: overwrite | merge | add",
    )
    parser.add_argument(
        "--collection-id",
        default="TARGET_COLLECTION_ID",
        help="Target collection ID (from figma_create_variable_collection or figma_get_variables)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Max variables per batch call (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument("--out", help="Directory to write payload files (omit to print JSON to stdout)")
    parser.add_argument("--summary", action="store_true", help="Print summary only, no payload output")
    args = parser.parse_args()

    for path_str in (args.source, args.target):
        if not Path(path_str).exists():
            print(f"Error: file not found: {path_str}", file=sys.stderr)
            sys.exit(1)

    source_data = json.loads(Path(args.source).read_text())
    target_data = json.loads(Path(args.target).read_text())

    # Validate basic structure
    for label, data in (("source", source_data), ("target", target_data)):
        if "collection" not in data or "variables" not in data:
            print(f"Error: {label} file must have 'collection' and 'variables' keys.", file=sys.stderr)
            print(f"  Ensure aliases are resolved to targetName before running this script.", file=sys.stderr)
            sys.exit(1)

    plan = analyze(source_data, target_data, args.mode)
    payloads = build_payloads(plan, source_data, target_data, args.collection_id, args.chunk_size)

    print_summary(plan, payloads, args.mode)

    if args.summary:
        return

    if args.out:
        write_payloads(plan, payloads, args.mode, Path(args.out))
    else:
        output = {
            "plan": plan,
            "payloads": payloads,
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
