#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
PRODUCT_ROOT = REPO_ROOT / "rednote-ads-placement-analyzer"
SCRIPTS_ROOT = PRODUCT_ROOT / "scripts"
SCRIPT_BY_COMMAND = {
    "check-env": SCRIPTS_ROOT / "check_environment.py",
    "login-only": SCRIPTS_ROOT / "run_pipeline.py",
    "prepare-run": SCRIPTS_ROOT / "run_pipeline.py",
    "crawl": SCRIPTS_ROOT / "run_pipeline.py",
    "analyze-reports": SCRIPTS_ROOT / "run_pipeline.py",
    "finalize-broadcast": SCRIPTS_ROOT / "run_pipeline.py",
    "validate-contract": SCRIPTS_ROOT / "validate_contract.py",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pipeline.py",
        description="Official execution-only entrypoint for rednote-ads-placement-analysis.",
    )
    parser.add_argument(
        "command",
        choices=tuple(SCRIPT_BY_COMMAND.keys()),
        help="Official pipeline step to execute.",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments forwarded to the selected step.")
    parsed = parser.parse_args()

    script = SCRIPT_BY_COMMAND[parsed.command]
    forwarded = list(parsed.args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    if parsed.command in {"login-only", "prepare-run", "crawl", "analyze-reports", "finalize-broadcast"}:
        preflight = subprocess.run(
            [sys.executable, str(SCRIPT_BY_COMMAND["check-env"])],
            cwd=REPO_ROOT,
        )
        if preflight.returncode != 0:
            return preflight.returncode

    command = [sys.executable, str(script)]
    if parsed.command in {"login-only", "prepare-run", "crawl", "analyze-reports", "finalize-broadcast"}:
        command.append(parsed.command)
    command.extend(forwarded)
    completed = subprocess.run(command, cwd=REPO_ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
