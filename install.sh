#!/usr/bin/env bash
set -e

# install.sh — Install ds-skills into Claude Code
#
# Symlinks all skills into ~/.claude/skills/ and copies shared token scripts
# and references to ~/.claude/skills/_shared/.
#
# Usage:
#   ./install.sh

SKILLS_DIR="$HOME/.claude/skills"
SHARED_DIR="$SKILLS_DIR/_shared"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

TOKEN_SKILLS=(token-foundation token-figma-scaffold token-generate token-push token-audit token-migrate token-apply token-bridge token-repair-aliases token-transfer)
DOC_SKILLS=(ds-doc-generator ds-spec-generator)
ALL_SKILLS=("${TOKEN_SKILLS[@]}" "${DOC_SKILLS[@]}")

echo "Installing ds-skills..."
echo

# Create skills directory if needed
mkdir -p "$SKILLS_DIR"

# Symlink each skill directory into ~/.claude/skills/
for skill in "${ALL_SKILLS[@]}"; do
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
echo "  ${#ALL_SKILLS[@]} skills available"

# Install shared scripts and references to ~/.claude/skills/_shared/
echo
echo "Installing shared token resources to $SHARED_DIR..."

mkdir -p "$SHARED_DIR/scripts"
mkdir -p "$SHARED_DIR/references"
cp "$REPO_DIR"/scripts/*.py "$SHARED_DIR/scripts/"
cp "$REPO_DIR"/references/* "$SHARED_DIR/references/"

echo "  $(ls "$SHARED_DIR/scripts/"*.py | wc -l | tr -d ' ') scripts available"
echo "  $(ls "$SHARED_DIR/references/" | wc -l | tr -d ' ') reference files available"

echo
echo "Done. Reload Claude Code to pick up the new skills."
echo
echo "Token skills:"
for skill in "${TOKEN_SKILLS[@]}"; do
  echo "  /$skill"
done
echo
echo "Documentation skills:"
for skill in "${DOC_SKILLS[@]}"; do
  echo "  /$skill"
done
