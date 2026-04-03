#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="$ROOT_DIR/.skill-control/skill-creator.state"

case "${1:-}" in
  enable)
    echo "enabled" > "$STATE_FILE"
    echo "[OK] skill-creator enabled."
    ;;
  disable)
    echo "disabled" > "$STATE_FILE"
    echo "[OK] skill-creator disabled."
    ;;
  status)
    if [[ -f "$STATE_FILE" ]]; then
      echo "[INFO] $(cat "$STATE_FILE")"
    else
      echo "[INFO] enabled"
    fi
    ;;
  *)
    echo "Usage: $0 {enable|disable|status}" >&2
    exit 1
    ;;
esac
