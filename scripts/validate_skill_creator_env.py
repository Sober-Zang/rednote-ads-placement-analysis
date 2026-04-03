#!/usr/bin/env python3
"""Project-level gate for anthropics/skills skill-creator deployment."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def read_state(state_file: Path) -> str:
    if not state_file.exists():
        return "enabled"
    value = state_file.read_text(encoding="utf-8").strip().lower()
    if value not in {"enabled", "disabled"}:
        fail(f"Invalid state '{value}' in {state_file}. Use enabled or disabled.")
    return value


def must_exist(path: Path) -> None:
    if not path.exists():
        fail(f"Missing required file: {path}")


def validate_skill_folder(root: Path) -> None:
    skill_dir = root / "skills" / "skill-creator"
    must_exist(skill_dir / "SKILL.md")
    must_exist(skill_dir / "scripts" / "quick_validate.py")
    must_exist(skill_dir / "scripts" / "run_loop.py")
    must_exist(skill_dir / "references" / "schemas.md")
    must_exist(skill_dir / "eval-viewer" / "generate_review.py")

    cmd = [
        sys.executable,
        str(skill_dir / "scripts" / "quick_validate.py"),
        str(skill_dir),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout, file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        fail("skills/skill-creator quick_validate failed.")
    print("[OK] skills/skill-creator quick_validate passed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()

    state_file = root / ".skill-control" / "skill-creator.state"
    state = read_state(state_file)
    if state == "disabled":
        print("[INFO] skill-creator enforcement is explicitly disabled.")
        return

    validate_skill_folder(root)
    print("[OK] skill-creator is enabled and validated.")


if __name__ == "__main__":
    main()
