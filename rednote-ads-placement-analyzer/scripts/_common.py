from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PRODUCT_ROOT.parent
VENDOR_ROOT = PRODUCT_ROOT / "vendor" / "mediacrawler_xhs"
ASSETS_ROOT = PRODUCT_ROOT / "assets"
REFERENCES_ROOT = PRODUCT_ROOT / "references"
DEFAULT_OUTPUT_ROOT = WORKSPACE_ROOT.parent / f"{WORKSPACE_ROOT.name}-output"
# Runtime scratch defaults to OUTPUT_DIR so normal execution no longer creates a
# separate sibling runtime directory. The only in-repo write-back exception
# remains the login-state directory at WORKSPACE_ROOT / "xhs_user_data_dir".
DEFAULT_RUNTIME_ROOT = DEFAULT_OUTPUT_ROOT
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_DIR", DEFAULT_OUTPUT_ROOT)).expanduser().resolve()
RUNTIME_ROOT = Path(os.environ.get("RUNTIME_DIR", DEFAULT_RUNTIME_ROOT)).expanduser().resolve()
RUNS_ROOT = OUTPUT_ROOT
CONTRACT_VERSION = "2026-04-08"
OFFICIAL_RUN_TOPLEVEL = ("aggregate", "creators", "inputs", "logs", "manifests", "notes", "prompt")
REQUIRED_RUN_FILES = (
    "inputs/raw_user_input.md",
    "inputs/invalid_links.md",
    "manifests/link_manifest.json",
    "manifests/run_manifest.json",
    "prompt/used_prompt.md",
    "prompt/prompt_mode.json",
)
FORBIDDEN_RUN_FILENAMES = (
    "raw_user_input.txt",
    "used_prompt.txt",
    "link_manifest.txt",
    "run_manifest.txt",
)


def ensure_vendor_on_path() -> None:
    vendor = str(VENDOR_ROOT)
    if vendor not in sys.path:
        sys.path.insert(0, vendor)


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def ensure_external_dir(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if is_within(resolved, WORKSPACE_ROOT):
        raise ValueError(f"{label} must be outside the workspace source tree: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_contract_roots() -> tuple[Path, Path]:
    return ensure_external_dir(OUTPUT_ROOT, "OUTPUT_DIR"), ensure_external_dir(RUNTIME_ROOT, "RUNTIME_DIR")


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for index in range(2, 1000):
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Unable to allocate a unique path for {path}")


def to_run_relative(path: Path, run_dir: Path) -> str:
    return str(path.resolve().relative_to(run_dir.resolve()))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sanitize_fs_component(value: str, limit: int = 80) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    value = re.sub(r'[\\\\/:*?"<>|]+', "_", value)
    return value[:limit] or "untitled"


def slugify(value: str, default: str = "multi-link-ad-analysis") -> str:
    value = value.lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:60] or default
