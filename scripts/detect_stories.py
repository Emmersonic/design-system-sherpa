#!/usr/bin/env python3
"""
detect_stories.py
-----------------
Environment detection for spec-generator and doc-generator (Frame phase).

Scans a component's directory for a co-located Storybook stories file and
extracts its named story exports. The result is the `storybookContext` the
render phase needs to decide between plain-markdown and MDX output and to embed
live `<Canvas of={...}>` blocks against real exports.

Detection is non-blocking by design: if no stories file is found or it can't be
parsed, the tool reports `detected: false` and the caller falls back to `.md`.

Usage:
    python detect_stories.py Page.tsx
    python detect_stories.py src/components/Page/
    python detect_stories.py Page.tsx --json

Output (JSON):
    {
      "detected": true,
      "storiesFile": "src/components/Page/Page.stories.tsx",
      "exports": ["Default", "WithToolbar", "Disabled"]
    }
"""

import argparse
import json
import re
import sys
from pathlib import Path

STORY_EXTENSIONS = (".stories.tsx", ".stories.ts", ".stories.jsx", ".stories.js")

# Top-level `export const/let/var/function/class Name`
_NAMED_DECL = re.compile(
    r"^export\s+(?:async\s+)?(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
# `export { A, B as C }`  — capture the exported name (after `as` when present)
_NAMED_LIST = re.compile(r"^export\s*\{([^}]*)\}", re.MULTILINE)


def _strip_block_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


def extract_exports(source: str) -> list[str]:
    """Return named exports (story candidates), excluding the default export."""
    text = _strip_block_comments(source)
    names: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        name = name.strip()
        if name and name != "default" and name not in seen:
            seen.add(name)
            names.append(name)

    for m in _NAMED_DECL.finditer(text):
        add(m.group(1))

    for block in _NAMED_LIST.finditer(text):
        for entry in block.group(1).split(","):
            entry = entry.strip()
            if not entry or entry.startswith("type "):
                continue
            # `Foo as Bar` exports as `Bar`; default re-exports are skipped.
            parts = re.split(r"\s+as\s+", entry)
            add(parts[-1])

    return names


def find_stories_file(target: Path) -> Path | None:
    """Locate a co-located stories file for the given component path."""
    if target.is_file():
        if target.name.endswith(STORY_EXTENSIONS):
            return target
        directory = target.parent
        # Strip the longest known suffix (e.g. ".module.css" → keep "Page").
        stem = target.name.split(".", 1)[0]
        for ext in STORY_EXTENSIONS:
            candidate = directory / f"{stem}{ext}"
            if candidate.exists():
                return candidate
        # Fall back to any stories file in the directory.
        target = directory

    if target.is_dir():
        for ext in STORY_EXTENSIONS:
            matches = sorted(target.glob(f"*{ext}"))
            if matches:
                return matches[0]
    return None


def detect(target: Path) -> dict:
    stories = find_stories_file(target)
    if stories is None:
        return {"detected": False}
    try:
        source = stories.read_text(encoding="utf-8")
    except OSError:
        return {"detected": False}
    return {
        "detected": True,
        "storiesFile": str(stories),
        "exports": extract_exports(source),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="Component file or directory to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON (default)")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(json.dumps({"detected": False, "error": f"path not found: {target}"}))
        return 0  # non-blocking: detection failure is not an error

    print(json.dumps(detect(target), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
