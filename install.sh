#!/usr/bin/env bash
set -e

# install.sh — Install ds-token-skills into Claude Code
#
# This script links the skills directory into ~/.claude/skills/ and optionally
# copies the shared scripts into your project so Claude can run them.
#
# Usage:
#   ./install.sh                     # install skills only
#   ./install.sh --scripts ./path    # install skills + copy scripts to a project directory

SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAMES=(token-foundation token-figma-scaffold token-generate token-push token-audit token-migrate token-apply)

# Parse args
SCRIPTS_DEST=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scripts)
      SCRIPTS_DEST="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--scripts <project-dir>]"
      exit 1
      ;;
  esac
done

echo "Installing ds-token-skills..."
echo

# Create skills directory if needed
mkdir -p "$SKILLS_DIR"

# Symlink each skill directory into ~/.claude/skills/
for skill in "${SKILL_NAMES[@]}"; do
  TARGET="$SKILLS_DIR/$skill"
  if [ -L "$TARGET" ]; then
    echo "  Updating symlink: $skill"
    rm "$TARGET"
  elif [ -d "$TARGET" ]; then
    echo "  Warning: $TARGET already exists as a real directory — skipping."
    echo "           Remove it manually if you want to replace it with a symlink."
    continue
  else
    echo "  Linking: $skill"
  fi
  ln -s "$REPO_DIR/$skill" "$TARGET"
done

echo
echo "Skills installed to $SKILLS_DIR"
echo "  $(ls "$SKILLS_DIR" | grep "^token-" | wc -l | tr -d ' ') skills available"

# Optionally copy scripts to a project directory
if [ -n "$SCRIPTS_DEST" ]; then
  echo
  if [ ! -d "$SCRIPTS_DEST" ]; then
    echo "Error: --scripts destination does not exist: $SCRIPTS_DEST"
    exit 1
  fi
  DEST_SCRIPTS="$SCRIPTS_DEST/scripts"
  mkdir -p "$DEST_SCRIPTS"
  cp "$REPO_DIR"/scripts/*.py "$DEST_SCRIPTS/"
  echo "Scripts copied to $DEST_SCRIPTS"
  echo "  $(ls "$DEST_SCRIPTS"/*.py | wc -l | tr -d ' ') scripts available"
fi

echo
echo "Next steps:"
echo "  1. Reload Claude Code (or restart) to pick up the new skills"
if [ -z "$SCRIPTS_DEST" ]; then
  echo "  2. Copy scripts to your design system project:"
  echo "       ./install.sh --scripts /path/to/your/project"
  echo "     Or manually: cp -r scripts/ /path/to/your/project/scripts"
fi
echo "  3. Add a CLAUDE.md to your project pointing to your foundation.md"
echo
echo "Skills installed:"
for skill in "${SKILL_NAMES[@]}"; do
  echo "  /$skill"
done
