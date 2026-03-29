#!/usr/bin/env python3
"""
diff_tokens.py
--------------
Compares two token proposal JSON files and produces a structured diff:
added, removed, renamed (heuristic), value changed, alias changed, mode added/removed.

Outputs a diff report and a ready-to-paste changelog entry with semantic version impact.

Usage:
    python diff_tokens.py old.json new.json
    python diff_tokens.py old.json new.json --format markdown
    python diff_tokens.py old.json new.json --format json
    python diff_tokens.py old.json new.json --out changelog-entry.md
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# ---------------------------------------------------------------------------
# Change types and version impact
# ---------------------------------------------------------------------------

ChangeType = Literal[
    "added",          # new token, no existing consumers → patch
    "removed",        # token deleted → major (breaking)
    "renamed",        # name changed, value same → major (breaking)
    "value_changed",  # primitive raw value changed → patch
    "alias_changed",  # semantic/component alias changed → patch or minor
    "mode_added",     # new mode added → minor
    "mode_removed",   # mode deleted → major (breaking)
    "type_changed",   # variable type changed → major (breaking)
    "description_changed",  # doc-only → patch
]

VERSION_IMPACT: dict[ChangeType, str] = {
    "added": "patch",
    "removed": "major",
    "renamed": "major",
    "value_changed": "patch",
    "alias_changed": "patch",
    "mode_added": "minor",
    "mode_removed": "major",
    "type_changed": "major",
    "description_changed": "patch",
}

IMPACT_RANK = {"patch": 0, "minor": 1, "major": 2}


@dataclass
class Change:
    change_type: ChangeType
    token: str
    old_value: object = None
    new_value: object = None
    mode: str = ""
    notes: str = ""

    @property
    def version_impact(self) -> str:
        return VERSION_IMPACT[self.change_type]

    @property
    def is_breaking(self) -> bool:
        return self.version_impact == "major"


@dataclass
class DiffResult:
    changes: list[Change] = field(default_factory=list)

    def add(self, *args, **kwargs):
        self.changes.append(Change(*args, **kwargs))

    @property
    def aggregate_impact(self) -> str:
        if not self.changes:
            return "none"
        return max(
            (VERSION_IMPACT[c.change_type] for c in self.changes),
            key=lambda v: IMPACT_RANK[v],
        )

    def by_type(self, *types: ChangeType) -> list[Change]:
        return [c for c in self.changes if c.change_type in types]


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

def build_flat_index(proposal: dict) -> dict[str, dict]:
    """Flat name → token across all collections."""
    index = {}
    for tokens in proposal.get("collections", {}).values():
        for t in (tokens or []):
            if t.get("name"):
                index[t["name"]] = t
    return index


def get_all_modes(proposal: dict) -> set[str]:
    modes = set()
    for key in ("tokens", "components"):
        for t in proposal.get("collections", {}).get(key, []) or []:
            modes.update(t.get("modes", {}).keys())
    return modes


# ---------------------------------------------------------------------------
# Diff logic
# ---------------------------------------------------------------------------

def diff_proposals(old: dict, new: dict) -> DiffResult:
    result = DiffResult()

    old_index = build_flat_index(old)
    new_index = build_flat_index(new)

    old_names = set(old_index.keys())
    new_names = set(new_index.keys())

    added_names = new_names - old_names
    removed_names = old_names - new_names
    common_names = old_names & new_names

    # --- Detect renames (heuristic: same type + same value/aliases, different name) ---
    rename_map: dict[str, str] = {}  # old_name → new_name

    for old_name in list(removed_names):
        old_tok = old_index[old_name]
        for new_name in list(added_names):
            new_tok = new_index[new_name]
            if (
                old_tok.get("type") == new_tok.get("type")
                and _token_values_equal(old_tok, new_tok)
                and new_name not in rename_map.values()
            ):
                rename_map[old_name] = new_name
                result.add("renamed", old_name,
                           old_value=old_name, new_value=new_name,
                           notes=f"Value unchanged — consumers must update to '{new_name}'")
                break

    renamed_old = set(rename_map.keys())
    renamed_new = set(rename_map.values())

    # --- Added ---
    for name in sorted(added_names - renamed_new):
        result.add("added", name, new_value=_summarise_token(new_index[name]))

    # --- Removed ---
    for name in sorted(removed_names - renamed_old):
        result.add("removed", name, old_value=_summarise_token(old_index[name]),
                   notes="Breaking: any consumers using this token will break")

    # --- Changed (tokens in both old and new) ---
    for name in sorted(common_names):
        old_tok = old_index[name]
        new_tok = new_index[name]

        # Type changed
        if old_tok.get("type") != new_tok.get("type"):
            result.add("type_changed", name,
                       old_value=old_tok.get("type"),
                       new_value=new_tok.get("type"))
            continue  # skip further checks for this token

        # Primitive: raw value changed
        if "value" in old_tok or "value" in new_tok:
            old_val = old_tok.get("value")
            new_val = new_tok.get("value")
            if old_val != new_val:
                result.add("value_changed", name,
                           old_value=old_val, new_value=new_val)

        # Alias token: per-mode alias changes + mode additions/removals
        if "modes" in old_tok or "modes" in new_tok:
            old_modes = old_tok.get("modes") or {}
            new_modes = new_tok.get("modes") or {}

            for mode in sorted(set(old_modes) | set(new_modes)):
                if mode in old_modes and mode not in new_modes:
                    result.add("mode_removed", name, mode=mode,
                               old_value=old_modes[mode])
                elif mode not in old_modes and mode in new_modes:
                    result.add("mode_added", name, mode=mode,
                               new_value=new_modes[mode])
                elif old_modes.get(mode) != new_modes.get(mode):
                    result.add("alias_changed", name,
                               old_value=old_modes[mode],
                               new_value=new_modes[mode],
                               mode=mode)

        # Description changed
        if old_tok.get("description") != new_tok.get("description"):
            result.add("description_changed", name,
                       old_value=old_tok.get("description"),
                       new_value=new_tok.get("description"))

    return result


def _token_values_equal(a: dict, b: dict) -> bool:
    """Rough equality check — ignores name and description."""
    return (
        a.get("type") == b.get("type")
        and a.get("value") == b.get("value")
        and a.get("modes") == b.get("modes")
    )


def _summarise_token(token: dict) -> str:
    if "value" in token:
        return str(token["value"])
    modes = token.get("modes", {})
    parts = [f"{m}: {v}" for m, v in list(modes.items())[:2]]
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_markdown(result: DiffResult, old_version: str = "?", new_version: str = "?") -> str:
    lines = []
    impact = result.aggregate_impact

    lines.append(f"## Changelog — v{old_version} → v{new_version}")
    lines.append(f"**Version impact: {impact.upper()}**")
    lines.append("")

    breaking = result.by_type("removed", "renamed", "mode_removed", "type_changed")
    if breaking:
        lines.append("### ⚠️  Breaking changes")
        for c in breaking:
            if c.change_type == "removed":
                lines.append(f"- **Removed** `{c.token}` — {c.notes}")
            elif c.change_type == "renamed":
                lines.append(f"- **Renamed** `{c.old_value}` → `{c.new_value}` — {c.notes}")
            elif c.change_type == "mode_removed":
                lines.append(f"- **Mode removed** `{c.token}` lost mode `{c.mode}`")
            elif c.change_type == "type_changed":
                lines.append(f"- **Type changed** `{c.token}`: `{c.old_value}` → `{c.new_value}`")
        lines.append("")

    minor = result.by_type("mode_added")
    if minor:
        lines.append("### ✨  Added (non-breaking)")
        for c in minor:
            lines.append(f"- **New mode** `{c.token}` gained mode `{c.mode}` → `{c.new_value}`")
        lines.append("")

    added = result.by_type("added")
    if added:
        lines.append("### ➕  New tokens")
        for c in added:
            lines.append(f"- `{c.token}` ({c.new_value})")
        lines.append("")

    changed = result.by_type("value_changed", "alias_changed")
    if changed:
        lines.append("### 🔄  Changed")
        for c in changed:
            if c.mode:
                lines.append(f"- `{c.token}` [{c.mode}]: `{c.old_value}` → `{c.new_value}`")
            else:
                lines.append(f"- `{c.token}`: `{c.old_value}` → `{c.new_value}`")
        lines.append("")

    doc = result.by_type("description_changed")
    if doc:
        lines.append("### 📝  Documentation")
        for c in doc:
            lines.append(f"- `{c.token}` description updated")
        lines.append("")

    if not result.changes:
        lines.append("_No changes detected._")

    return "\n".join(lines)


def format_summary(result: DiffResult) -> str:
    lines = [
        f"\nDiff summary",
        f"{'─'*40}",
        f"  Added:           {len(result.by_type('added'))}",
        f"  Removed:         {len(result.by_type('removed'))}  {'(breaking)' if result.by_type('removed') else ''}",
        f"  Renamed:         {len(result.by_type('renamed'))}  {'(breaking)' if result.by_type('renamed') else ''}",
        f"  Value changed:   {len(result.by_type('value_changed'))}",
        f"  Alias changed:   {len(result.by_type('alias_changed'))}",
        f"  Mode added:      {len(result.by_type('mode_added'))}",
        f"  Mode removed:    {len(result.by_type('mode_removed'))}  {'(breaking)' if result.by_type('mode_removed') else ''}",
        f"  Type changed:    {len(result.by_type('type_changed'))}  {'(breaking)' if result.by_type('type_changed') else ''}",
        f"{'─'*40}",
        f"  Aggregate impact: {result.aggregate_impact.upper()}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Diff two token proposal JSON files.")
    parser.add_argument("old", help="Path to the old/previous token proposal JSON")
    parser.add_argument("new", help="Path to the new token proposal JSON")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    parser.add_argument("--out", help="Write output to this file instead of stdout")
    args = parser.parse_args()

    old_path = Path(args.old)
    new_path = Path(args.new)

    for p in (old_path, new_path):
        if not p.exists():
            print(f"Error: file not found: {p}", file=sys.stderr)
            sys.exit(1)

    old_proposal = json.loads(old_path.read_text())
    new_proposal = json.loads(new_path.read_text())

    old_version = old_proposal.get("meta", {}).get("version", "?")
    new_version = new_proposal.get("meta", {}).get("version", "?")

    result = diff_proposals(old_proposal, new_proposal)

    if args.format == "json":
        output = json.dumps([
            {"type": c.change_type, "token": c.token,
             "old": c.old_value, "new": c.new_value,
             "mode": c.mode, "impact": c.version_impact, "notes": c.notes}
            for c in result.changes
        ], indent=2)
    elif args.format == "markdown":
        output = format_markdown(result, old_version, new_version)
    else:
        output = format_summary(result)
        output += format_markdown(result, old_version, new_version)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Wrote diff to {args.out}")
        print(format_summary(result))
    else:
        print(output)

    # Exit code: 0 = no changes, 1 = patch/minor, 2 = major
    if not result.changes:
        sys.exit(0)
    elif result.aggregate_impact == "major":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
