#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path

from _common import PRODUCT_ROOT, VENDOR_ROOT


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    required = ["httpx", "aiofiles", "playwright", "tenacity", "humps", "PIL", "jieba", "wordcloud"]
    print(f"Product root: {PRODUCT_ROOT}")
    print(f"Vendor root:  {VENDOR_ROOT}")
    print(f"Python:       {sys.executable}")
    print(f"Version:      {platform.python_version()}")
    print("")
    missing = [name for name in required if not has_module(name)]
    for name in required:
        print(f"{name:<12} {'OK' if name not in missing else 'MISSING'}")
    print("")
    if missing:
        print("Missing modules detected.")
        print("Use a Python environment that contains the crawler dependencies before running crawl mode.")
        return 1
    print("Environment looks ready for prepare-run and crawl.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
