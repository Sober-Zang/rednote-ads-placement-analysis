#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path

from _common import OUTPUT_ROOT, PRODUCT_ROOT, RUNTIME_ROOT, VENDOR_ROOT, ensure_contract_roots, is_within, WORKSPACE_ROOT


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    required = [
        ("httpx", "httpx"),
        ("aiofiles", "aiofiles"),
        ("playwright", "playwright"),
        ("tenacity", "tenacity"),
        ("humps", "pyhumps"),
        ("PIL", "Pillow"),
        ("jieba", "jieba"),
        ("wordcloud", "wordcloud"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("cv2", "opencv-python"),
        ("pydantic", "pydantic"),
    ]
    print(f"Product root: {PRODUCT_ROOT}")
    print(f"Vendor root:  {VENDOR_ROOT}")
    print(f"Python:       {sys.executable}")
    print(f"Version:      {platform.python_version()}")
    print(f"Workspace:    {WORKSPACE_ROOT}")
    print(f"OUTPUT_DIR:   {OUTPUT_ROOT}")
    print(f"RUNTIME_DIR:  {RUNTIME_ROOT}")
    print("")
    expected_venv = (WORKSPACE_ROOT / ".venv").resolve()
    executable_path = Path(sys.executable).resolve()
    active_prefix = Path(sys.prefix).resolve()
    venv_ready = expected_venv.exists() and active_prefix == expected_venv
    missing = [package for module, package in required if not has_module(module)]
    for module, package in required:
        print(f"{module:<12} {'OK' if package not in missing else 'MISSING'}")
    print(f"{'.venv':<12} {'OK' if venv_ready else 'MISSING'}")
    print("")
    contract_error = False
    if is_within(OUTPUT_ROOT, WORKSPACE_ROOT):
        print("OUTPUT_DIR is inside the workspace source tree, which violates execution-only mode.")
        contract_error = True
    if OUTPUT_ROOT != RUNTIME_ROOT and is_within(RUNTIME_ROOT, WORKSPACE_ROOT):
        print("RUNTIME_DIR is inside the workspace source tree, which violates execution-only mode.")
        contract_error = True
    if missing or not venv_ready:
        print("Missing modules detected.")
        print("请先严格按 README.machine.md 中的唯一安装方式准备环境，然后重新执行 check-env：")
        print("")
        print("macOS / Linux:")
        print("  python3 -m venv .venv")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements-execution.txt")
        print("  python -m playwright install chromium")
        print("")
        print("Windows PowerShell:")
        print("  py -m venv .venv")
        print("  .venv\\Scripts\\Activate.ps1")
        print("  pip install -r requirements-execution.txt")
        print("  python -m playwright install chromium")
        return 1
    if contract_error:
        return 1
    ensure_contract_roots()
    print("")
    print("Default external roots (when environment variables are not set):")
    print(f"  OUTPUT_DIR  -> {WORKSPACE_ROOT.parent / (WORKSPACE_ROOT.name + '-output')}")
    print("  RUNTIME_DIR -> follows OUTPUT_DIR by default; no separate sibling runtime directory is created")
    print("  LOGIN_STATE -> xhs_user_data_dir (the sole in-repo write-back exception)")
    print("Environment looks ready. Only after this passes may prepare-run, crawl, finalize-broadcast, or login-only continue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
