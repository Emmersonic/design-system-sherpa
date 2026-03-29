#!/usr/bin/env python3
"""
validate_tokens.py
------------------
Validates a token proposal JSON against the 3-tier naming convention and structural rules
defined in token-foundation. Run before token-push to catch errors before they land in Figma.

Checks performed:
  1. Naming convention  — kebab-case, slash separators, no abbreviations, no raw values
  2. Tier ordering      — no component token aliasing a primitive directly
  3. Alias integrity    — every alias target exists somewhere in the proposal
  4. Mode coverage      — all alias tokens have values for every declared mode
  5. Type consistency   — alias tokens don't change type mid-chain
  6. Forbidden patterns — camelCase, PascalCase, underscores, appearance names in semantic tier

Usage:
    python validate_tokens.py proposal.json
    python validate_tokens.py proposal.json --modes light dark
    python validate_tokens.py proposal.json --strict   # fail on warnings too
    python validate_tokens.py proposal.json --fix      # auto-fix safe issues and rewrite
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

KNOWN_ABBREVIATIONS = {
    "bg", "fg", "txt", "btn", "pri", "sec", "ter", "typ", "typo",
    "clr", "col", "sz", "spc", "rad", "bdr", "brdr", "fnt", "wgt",
    "ht", "wt", "wd", "lg", "sm", "md", "xs", "xl",  # size shorthands ok only in values/primitives
    "def", "dis", "hov", "act", "foc", "vis",
    "err", "wrn", "inf", "suc",
}

# These are ok in primitive names (they describe appearance) but forbidden in semantic/component
APPEARANCE_WORDS = {
    "white", "black", "gray", "grey", "red", "blue", "green", "yellow",
    "orange", "purple", "pink", "teal", "indigo", "violet", "amber", "cyan",
    "slate", "zinc", "stone", "lime", "emerald", "sky", "rose", "fuchsia",
}

VALID_STATES = {"default", "hover", "active", "pressed", "disabled", "focus", "focus-visible", "selected", "checked", "indeterminate", "loading", "error"}
VALID_TIERS = {"color", "spacing", "font-size", "font-weight", "font-family", "line-height", "border-radius", "motion", "elevation", "opacity"}

CAMEL_CASE_RE = re.compile(r"[a-z][A-Z]")
PASCAL_CASE_RE = re.compile(r"^[A-Z]")
UNDERSCORE_RE = re.compile(r"_")
RAW_VALUE_RE = re.compile(r"(#[0-9a-fA-F]{3,8}|\d+px|\d+rem|\d+em)")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

Severity = Literal["error", "warning", "info"]


@dataclass
class Finding:
    severity: Severity
    token: str
    rule: str
    message: str
    suggestion: str = ""


@dataclass
class ValidationResult:
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: Severity, token: str, rule: str, message: str, suggestion: str = ""):
        self.findings.append(Finding(severity, token, rule, message, suggestion))

    @property
    def errors(self):
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self):
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def infos(self):
        return [f for f in self.findings if f.severity == "info"]

    @property
    def passed(self):
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def infer_tier(name: str) -> str:
    """Guess whether a token is primitive, semantic, or component based on its name."""
    parts = name.split("/")
    category = parts[0]

    # Component tokens: first segment is a component name, not a category
    if category not in VALID_TIERS and len(parts) >= 3:
        return "component"

    # Primitive tokens: short names like color/blue/500, spacing/4
    if len(parts) <= 3:
        last = parts[-1]
        # Numeric last segment = almost certainly primitive
        if re.match(r"^\d+$", last):
            return "primitive"
        # Appearance word in second segment = primitive
        if len(parts) >= 2 and parts[1].split("-")[0] in APPEARANCE_WORDS:
            return "primitive"

    return "semantic"


def build_token_index(proposal: dict) -> dict[str, dict]:
    """Build a flat name → token dict across all collections."""
    index = {}
    for collection_tokens in proposal.get("collections", {}).values():
        for token in (collection_tokens or []):
            name = token.get("name")
            if name:
                index[name] = token
    return index


def get_declared_modes(proposal: dict) -> list[str]:
    """Extract mode names from alias tokens (the keys of their modes dicts)."""
    modes = set()
    for key in ("tokens", "components"):
        for token in proposal.get("collections", {}).get(key, []) or []:
            modes.update(token.get("modes", {}).keys())
    return sorted(modes)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_naming(name: str, token_type: str, result: ValidationResult):
    parts = name.split("/")

    # Must use slashes as separators
    if "-" in name and "/" not in name:
        result.add("error", name, "naming/separator",
            "Token uses hyphens as tier separators instead of slashes",
            f"Rename to use slashes: '{name.replace('-', '/')}'")

    for i, part in enumerate(parts):
        # camelCase detection
        if CAMEL_CASE_RE.search(part):
            result.add("error", name, "naming/camel-case",
                f"Segment {i+1} '{part}' uses camelCase — use kebab-case",
                f"Rename '{part}' to '{camel_to_kebab(part)}'")

        # PascalCase detection
        if PASCAL_CASE_RE.match(part):
            result.add("error", name, "naming/pascal-case",
                f"Segment {i+1} '{part}' uses PascalCase — use kebab-case")

        # Underscores
        if UNDERSCORE_RE.search(part):
            result.add("error", name, "naming/underscore",
                f"Segment {i+1} '{part}' uses underscores — use hyphens within a segment")

        # Abbreviations (check the full part and its hyphen-split words)
        words = part.split("-")
        for word in words:
            if word.lower() in KNOWN_ABBREVIATIONS:
                result.add("warning", name, "naming/abbreviation",
                    f"Segment '{part}' contains abbreviation '{word}' — use the full word")

    # Raw values in name
    if RAW_VALUE_RE.search(name):
        result.add("error", name, "naming/raw-value",
            "Token name contains a raw value (hex, px, rem) — names must describe intent")

    # Appearance words in semantic/component tokens
    tier = infer_tier(name)
    if tier in ("semantic", "component"):
        for part in parts[1:]:  # skip category segment
            for word in part.split("-"):
                if word.lower() in APPEARANCE_WORDS:
                    result.add("warning", name, "naming/appearance-word",
                        f"Semantic/component token '{name}' contains appearance word '{word}' — use intent-based naming",
                        "E.g. 'color/blue-primary' → 'color/surface/brand'")


def check_alias_integrity(proposal: dict, token_index: dict, result: ValidationResult):
    """Every alias target must exist in the proposal (or we note it's assumed to already be in Figma)."""
    primitives = {t["name"] for t in proposal.get("collections", {}).get("primitives", []) or []}

    for key in ("tokens", "components"):
        for token in proposal.get("collections", {}).get(key, []) or []:
            name = token.get("name", "?")
            tier = infer_tier(name)

            for mode, target in (token.get("modes") or {}).items():
                if target not in token_index:
                    result.add("warning", name, "alias/target-missing",
                        f"Mode '{mode}' aliases '{target}' which is not in this proposal",
                        "If the target exists in Figma already this is fine; otherwise add it to primitives")

                # Component tokens should not alias primitives directly
                if tier == "component" and target in primitives:
                    result.add("error", name, "alias/component-to-primitive",
                        f"Component token aliases primitive '{target}' directly — should go via a semantic token",
                        "Add a semantic token as an intermediary")


def check_mode_coverage(proposal: dict, declared_modes: list[str], result: ValidationResult):
    """Every alias token must have a value for every declared mode."""
    if not declared_modes:
        return

    for key in ("tokens", "components"):
        for token in proposal.get("collections", {}).get(key, []) or []:
            name = token.get("name", "?")
            token_modes = set(token.get("modes", {}).keys())
            missing = set(declared_modes) - token_modes

            if missing:
                result.add("error", name, "modes/missing-value",
                    f"Token is missing values for mode(s): {sorted(missing)}",
                    "Add an alias for each missing mode")


def check_tier_ordering(proposal: dict, result: ValidationResult):
    """Semantic tokens should not skip over each other incorrectly. Basic check only."""
    # Mainly handled by check_alias_integrity's component-to-primitive rule.
    # This check flags semantic tokens aliasing other semantics from a different category
    # (usually harmless but worth noting).
    pass  # Extendable


def check_type_consistency(proposal: dict, token_index: dict, result: ValidationResult):
    """If a token declares type COLOR, its alias chain should only reference COLOR tokens."""
    for key in ("tokens", "components"):
        for token in proposal.get("collections", {}).get(key, []) or []:
            name = token.get("name", "?")
            declared_type = token.get("type")
            if not declared_type:
                continue

            for mode, target in (token.get("modes") or {}).items():
                target_token = token_index.get(target)
                if target_token and target_token.get("type") != declared_type:
                    result.add("error", name, "type/mismatch",
                        f"Token type '{declared_type}' but mode '{mode}' aliases '{target}' which is '{target_token['type']}'")


def check_proposal_status(proposal: dict, result: ValidationResult):
    """token-push requires status = 'approved'."""
    status = proposal.get("meta", {}).get("status", "draft")
    if status not in ("approved", "pushed"):
        result.add("warning", "meta", "status/not-approved",
            f"Proposal status is '{status}' — token-push requires 'approved'",
            "Have the designer review and set status to 'approved' before pushing")


# ---------------------------------------------------------------------------
# Auto-fix
# ---------------------------------------------------------------------------

def camel_to_kebab(name: str) -> str:
    """Convert camelCase to kebab-case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def auto_fix(proposal: dict) -> tuple[dict, list[str]]:
    """Apply safe, unambiguous fixes. Returns (updated_proposal, list of changes)."""
    changes = []

    for collection_key, tokens in proposal.get("collections", {}).items():
        if not tokens:
            continue
        for token in tokens:
            original_name = token.get("name", "")
            fixed = original_name

            # Fix camelCase → kebab-case in each segment
            segments = fixed.split("/")
            new_segments = []
            for seg in segments:
                fixed_seg = camel_to_kebab(seg)
                new_segments.append(fixed_seg)
            fixed = "/".join(new_segments)

            # Fix underscores → hyphens within segments
            fixed = fixed.replace("_", "-")

            if fixed != original_name:
                changes.append(f"  {original_name} → {fixed}")
                token["name"] = fixed

                # Also fix any alias targets that referenced the old name
                # (best-effort; cross-references in modes dicts)

    # Fix alias targets that used old names
    name_map = {}  # we'd need to build this in a two-pass; skip for now in simple fix mode

    return proposal, changes


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(result: ValidationResult, proposal_path: str = ""):
    title = f"Token validation — {proposal_path}" if proposal_path else "Token validation"
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")

    if not result.findings:
        print("✅  All checks passed — no issues found.\n")
        return

    for severity, label, symbol in [("error", "Errors", "❌"), ("warning", "Warnings", "⚠️ "), ("info", "Info", "ℹ️ ")]:
        group = [f for f in result.findings if f.severity == severity]
        if not group:
            continue
        print(f"\n{symbol}  {label} ({len(group)})")
        print("-" * 40)
        for f in group:
            print(f"  [{f.rule}]  {f.token}")
            print(f"    → {f.message}")
            if f.suggestion:
                print(f"    ✎  {f.suggestion}")

    print(f"\n{'─'*60}")
    print(f"  Errors: {len(result.errors)}   Warnings: {len(result.warnings)}   Info: {len(result.infos)}")
    status = "FAIL" if result.errors else "PASS (with warnings)" if result.warnings else "PASS"
    print(f"  Result: {status}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(proposal: dict, declared_modes: list[str] | None = None) -> ValidationResult:
    result = ValidationResult()
    token_index = build_token_index(proposal)
    modes = declared_modes or get_declared_modes(proposal)

    # Run all checks
    check_proposal_status(proposal, result)

    all_tokens = []
    for collection_tokens in proposal.get("collections", {}).values():
        all_tokens.extend(collection_tokens or [])

    for token in all_tokens:
        name = token.get("name", "")
        token_type = token.get("type", "")
        if name:
            check_naming(name, token_type, result)

    check_alias_integrity(proposal, token_index, result)
    check_mode_coverage(proposal, modes, result)
    check_type_consistency(proposal, token_index, result)

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate a token proposal JSON.")
    parser.add_argument("file", help="Path to token proposal JSON")
    parser.add_argument("--modes", nargs="+", help="Expected mode names (e.g. --modes light dark)")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    parser.add_argument("--fix", action="store_true", help="Auto-fix safe naming issues and rewrite the file")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON instead of human-readable text")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    proposal = json.loads(path.read_text())

    if args.fix:
        proposal, changes = auto_fix(proposal)
        if changes:
            print(f"Auto-fixed {len(changes)} naming issue(s):")
            for c in changes:
                print(c)
            path.write_text(json.dumps(proposal, indent=2))
            print(f"Wrote fixed proposal to {path}\n")
        else:
            print("No auto-fixable issues found.\n")

    result = validate(proposal, declared_modes=args.modes)

    if args.json:
        print(json.dumps([
            {"severity": f.severity, "token": f.token, "rule": f.rule,
             "message": f.message, "suggestion": f.suggestion}
            for f in result.findings
        ], indent=2))
    else:
        print_report(result, str(path))

    if result.errors:
        sys.exit(1)
    if args.strict and result.warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
