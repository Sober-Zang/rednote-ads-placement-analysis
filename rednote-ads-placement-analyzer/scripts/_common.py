from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = PRODUCT_ROOT / "vendor" / "mediacrawler_xhs"
RUNS_ROOT = PRODUCT_ROOT / "runs"
ASSETS_ROOT = PRODUCT_ROOT / "assets"
REFERENCES_ROOT = PRODUCT_ROOT / "references"


def ensure_vendor_on_path() -> None:
    vendor = str(VENDOR_ROOT)
    if vendor not in sys.path:
        sys.path.insert(0, vendor)


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
