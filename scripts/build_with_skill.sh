#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATOR="$ROOT_DIR/scripts/validate_skill_creator_env.py"

python3 "$VALIDATOR" --project-root "$ROOT_DIR"

if [[ "${1:-}" != "" ]]; then
  /bin/zsh -lc "$1"
  exit 0
fi

if [[ "${BUILD_CMD:-}" != "" ]]; then
  /bin/zsh -lc "$BUILD_CMD"
  exit 0
fi

echo "[INFO] No build command provided. Skill enforcement and validation completed."
