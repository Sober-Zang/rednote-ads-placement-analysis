#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from _common import (
    FORBIDDEN_RUN_FILENAMES,
    OFFICIAL_RUN_TOPLEVEL,
    OUTPUT_ROOT,
    REQUIRED_RUN_FILES,
    RUNTIME_ROOT,
    WORKSPACE_ROOT,
    ensure_contract_roots,
    is_within,
)

WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")


def is_url(value: str) -> bool:
    scheme = urlparse(value).scheme.lower()
    return scheme in {"http", "https"}


def is_absolute_path_string(value: str) -> bool:
    if is_url(value):
        return False
    return value.startswith("/") or bool(WINDOWS_ABS_RE.match(value))


def iter_json_values(payload: Any):
    if isinstance(payload, dict):
        for value in payload.values():
            yield from iter_json_values(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from iter_json_values(value)
    elif isinstance(payload, str):
        yield payload


def validate_run_dir(run_dir: Path, output_root: Path, workspace_root: Path) -> list[str]:
    errors: list[str] = []
    if not run_dir.exists():
        return [f"Run directory does not exist: {run_dir}"]
    if not is_within(run_dir, output_root):
        errors.append(f"Run directory is not under OUTPUT_DIR: {run_dir}")

    top_level_names = {path.name for path in run_dir.iterdir()}
    unexpected = sorted(top_level_names.difference(OFFICIAL_RUN_TOPLEVEL))
    if unexpected:
        errors.append(f"Unexpected run-level directories/files: {unexpected}")

    for relpath in REQUIRED_RUN_FILES:
        if not (run_dir / relpath).exists():
            errors.append(f"Missing required file: {relpath}")

    for forbidden in FORBIDDEN_RUN_FILENAMES:
        matches = sorted(str(path.relative_to(run_dir)) for path in run_dir.rglob(forbidden))
        if matches:
            errors.append(f"Forbidden filename present: {forbidden} -> {matches}")

    json_paths = list(run_dir.glob("manifests/*.json")) + list(run_dir.glob("notes/*/manifests/*.json"))
    for json_path in json_paths:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        for value in iter_json_values(payload):
            if workspace_root.as_posix() in value:
                errors.append(f"Workspace absolute path leaked into JSON: {json_path}")
                break
            if is_absolute_path_string(value):
                errors.append(f"Absolute path string found in JSON: {json_path}")
                break

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate execution-only output and runtime contracts.")
    parser.add_argument("--run-dir", required=True, help="Absolute path to a generated run directory under OUTPUT_DIR.")
    args = parser.parse_args()

    output_root, runtime_root = ensure_contract_roots()
    errors: list[str] = []
    if is_within(runtime_root, WORKSPACE_ROOT):
        errors.append(f"RUNTIME_DIR must be outside workspace source tree: {runtime_root}")
    errors.extend(validate_run_dir(Path(args.run_dir).expanduser().resolve(), output_root, WORKSPACE_ROOT.resolve()))

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "run_dir": str(Path(args.run_dir).expanduser().resolve()),
                "output_dir": str(output_root),
                "runtime_dir": str(runtime_root),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
