#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from _common import (
    ASSETS_ROOT,
    PRODUCT_ROOT,
    RUNS_ROOT,
    VENDOR_ROOT,
    ensure_vendor_on_path,
    read_json,
    sanitize_fs_component,
    slugify,
    write_json,
    write_text,
)

URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


def clean_url(url: str) -> str:
    return url.rstrip("，。！？、；：)]}>\"'")


def extract_urls(raw_text: str) -> list[str]:
    return [clean_url(match.group(0)) for match in URL_PATTERN.finditer(raw_text)]


def is_xhs_short_link(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower() == "xhslink.com"


async def resolve_url(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return str(response.url)


def create_run_id(task_slug: str) -> str:
    return f"run_{datetime.now().strftime('%Y%m%d-%H%M%S')}_{task_slug}"


def render_invalid_links(entries: list[dict[str, Any]]) -> str:
    invalid = [entry for entry in entries if not entry["is_valid_xhs"]]
    if not invalid:
        return "本次输入中未发现非小红书链接。\n"
    lines = ["以下链接未纳入分析：", ""]
    for entry in invalid:
        lines.append(f"- {entry['raw_url']} ({entry['exclude_reason']})")
    lines.append("")
    return "\n".join(lines)


def load_prompt_text(custom_prompt_file: str | None) -> tuple[str, str]:
    if custom_prompt_file:
        prompt_path = Path(custom_prompt_file)
        return "run-specific", prompt_path.read_text(encoding="utf-8")
    return "standard", (ASSETS_ROOT / "standard_analysis_prompt.md").read_text(encoding="utf-8")


def init_run_dirs(run_dir: Path) -> None:
    for relative in [
        "manifests",
        "prompt",
        "inputs",
        "notes",
        "aggregate",
        "logs",
    ]:
        (run_dir / relative).mkdir(parents=True, exist_ok=True)


def prepare_run(input_file: str, run_root: str | None, custom_prompt_file: str | None, task_slug: str | None) -> dict[str, Any]:
    raw_text = Path(input_file).read_text(encoding="utf-8")
    urls = extract_urls(raw_text)
    entries = []
    for index, url in enumerate(urls, start=1):
        is_valid = is_xhs_short_link(url)
        entries.append(
            {
                "order": index,
                "raw_text_fragment": url,
                "raw_url": url,
                "normalized_url": url,
                "resolved_url": "",
                "platform": "xhs" if is_valid else urlparse(url).netloc.lower(),
                "is_valid_xhs": is_valid,
                "exclude_reason": "" if is_valid else "非 xhslink.com 链接",
            }
        )

    valid_entries = [entry for entry in entries if entry["is_valid_xhs"]]
    mode, prompt_text = load_prompt_text(custom_prompt_file)
    derived_slug = task_slug or slugify(raw_text)
    run_id = create_run_id(derived_slug)
    run_dir = Path(run_root or RUNS_ROOT) / run_id
    init_run_dirs(run_dir)

    write_text(run_dir / "inputs" / "raw_user_input.md", raw_text.rstrip() + "\n")
    write_text(run_dir / "inputs" / "invalid_links.md", render_invalid_links(entries))
    write_text(run_dir / "prompt" / "used_prompt.md", prompt_text.rstrip() + "\n")
    write_json(run_dir / "prompt" / "prompt_mode.json", {"mode": mode, "source": custom_prompt_file or "assets/standard_analysis_prompt.md"})
    write_json(run_dir / "manifests" / "link_manifest.json", entries)

    run_manifest = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_slug": derived_slug,
        "source_prompt_mode": mode,
        "valid_links": [entry["raw_url"] for entry in valid_entries],
        "invalid_links": [entry["raw_url"] for entry in entries if not entry["is_valid_xhs"]],
        "note_folders": [],
        "outputs": [],
        "status": "prepared" if valid_entries else "failed_validation",
    }
    write_json(run_dir / "manifests" / "run_manifest.json", run_manifest)
    return {"run_dir": str(run_dir), "run_id": run_id, "valid_links": len(valid_entries), "invalid_links": len(entries) - len(valid_entries)}


def extract_note_id(url: str) -> str:
    if "/explore/" in url:
        return url.split("/explore/")[-1].split("?")[0]
    if "/discovery/item/" in url:
        return url.split("/discovery/item/")[-1].split("?")[0]
    return ""


async def crawl_run(run_dir: str) -> dict[str, Any]:
    run_path = Path(run_dir)
    link_manifest_path = run_path / "manifests" / "link_manifest.json"
    run_manifest_path = run_path / "manifests" / "run_manifest.json"
    entries = read_json(link_manifest_path)
    valid_entries = [entry for entry in entries if entry["is_valid_xhs"]]
    if not valid_entries:
        raise SystemExit("No valid Xiaohongshu links found in this run.")

    for entry in valid_entries:
        resolved = await resolve_url(entry["raw_url"])
        entry["resolved_url"] = resolved
        entry["normalized_url"] = resolved
        entry["note_id"] = extract_note_id(resolved)

    write_json(link_manifest_path, entries)

    ensure_vendor_on_path()
    import config  # type: ignore
    from media_platform.xhs.core import XiaoHongShuCrawler  # type: ignore
    from store.xhs import export_note_summaries, initialize_runtime_store  # type: ignore

    config.apply_runtime_config(
        {
            "PRODUCT_ROOT": PRODUCT_ROOT,
            "RUN_OUTPUT_DIR": str(run_path),
            "RUN_ID": run_path.name,
            "TASK_SLUG": read_json(run_manifest_path).get("task_slug", ""),
            "CRAWLER_TYPE": "detail",
            "XHS_SPECIFIED_NOTE_URL_LIST": [entry["resolved_url"] for entry in valid_entries],
            "ENABLE_GET_MEIDAS": True,
            "ENABLE_GET_COMMENTS": True,
            "ENABLE_GET_SUB_COMMENTS": True,
            "ENABLE_GET_WORDCLOUD": True,
            "SAVE_LOGIN_STATE": True,
            "ENABLE_CDP_MODE": False,
            "REQUIRE_LOGIN": False,
            "ALLOW_ANONYMOUS_HTML_FALLBACK": True,
            "MAX_CONCURRENCY_NUM": 1,
            "CRAWLER_MAX_SLEEP_SEC": 1,
            "STOP_WORDS_FILE": str(VENDOR_ROOT / "docs" / "hit_stopwords.txt"),
            "FONT_PATH": str(VENDOR_ROOT / "docs" / "STZHONGS.TTF"),
        }
    )
    initialize_runtime_store(run_path, valid_entries)
    crawler = XiaoHongShuCrawler()
    await crawler.start()
    await crawler.close()

    summaries = export_note_summaries()
    run_manifest = read_json(run_manifest_path)
    run_manifest["status"] = "crawled"
    run_manifest["note_folders"] = [item["folder_path"] for item in summaries]
    run_manifest["note_summaries"] = summaries
    write_json(run_manifest_path, run_manifest)
    return {"run_dir": str(run_path), "notes": len(summaries), "status": run_manifest["status"]}


def find_reports(run_path: Path) -> tuple[list[Path], list[Path]]:
    single_reports = sorted(run_path.glob("notes/*/analysis/*_分析报告.md"))
    aggregate_reports = sorted(run_path.glob("aggregate/*_综合分析报告.md"))
    return single_reports, aggregate_reports


def finalize_broadcast(run_dir: str) -> dict[str, Any]:
    run_path = Path(run_dir)
    link_entries = read_json(run_path / "manifests" / "link_manifest.json")
    invalid_links = [entry["raw_url"] for entry in link_entries if not entry["is_valid_xhs"]]
    single_reports, aggregate_reports = find_reports(run_path)

    for report in single_reports:
        note_dir = report.parents[1]
        manifest_path = note_dir / "manifests" / "note_manifest.json"
        if manifest_path.exists():
            note_manifest = read_json(manifest_path)
            note_manifest["analysis_report_path"] = str(report)
            primary_files = note_manifest.setdefault("primary_files", {})
            primary_files["analysis_report"] = str(report)
            write_json(manifest_path, note_manifest)

    lines = [
        "✅ 小红书广告投放分析完成！",
        "",
        f"📁 输出目录: {run_path.resolve()}",
        "",
        "📄 生成文件:",
    ]
    if single_reports:
        for report in single_reports:
            lines.append(f"- {report.name}")
    else:
        lines.append("- 暂无单篇分析报告")

    if aggregate_reports:
        for report in aggregate_reports:
            lines.append(f"- {report.name}")
    else:
        lines.append("- 暂无综合分析报告")

    lines.extend(["", "⚠️ 未纳入分析的链接:"])
    if invalid_links:
        for url in invalid_links:
            lines.append(f"- {url}")
    else:
        lines.append("- 无")

    write_text(run_path / "logs" / "final_broadcast.md", "\n".join(lines).rstrip() + "\n")

    run_manifest_path = run_path / "manifests" / "run_manifest.json"
    run_manifest = read_json(run_manifest_path)
    run_manifest["outputs"] = [str(path) for path in single_reports + aggregate_reports + [run_path / "logs" / "final_broadcast.md"]]
    summaries = run_manifest.get("note_summaries", [])
    for summary in summaries:
        folder_path = summary.get("folder_path")
        if not folder_path:
            continue
        manifest_path = Path(folder_path) / "manifests" / "note_manifest.json"
        if not manifest_path.exists():
            continue
        note_manifest = read_json(manifest_path)
        summary["analysis_report_path"] = note_manifest.get("analysis_report_path", "")
        summary["primary_files"] = note_manifest.get("primary_files", summary.get("primary_files", {}))
    run_manifest["note_summaries"] = summaries
    if single_reports:
        run_manifest["status"] = "reports_ready"
    write_json(run_manifest_path, run_manifest)
    return {"run_dir": str(run_path), "single_reports": len(single_reports), "aggregate_reports": len(aggregate_reports)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run-scoped pipeline for rednote ads placement analysis.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-run")
    prepare.add_argument("--input-file", required=True)
    prepare.add_argument("--run-root", default=str(RUNS_ROOT))
    prepare.add_argument("--custom-prompt-file")
    prepare.add_argument("--task-slug")

    crawl = subparsers.add_parser("crawl")
    crawl.add_argument("--run-dir", required=True)

    finalize = subparsers.add_parser("finalize-broadcast")
    finalize.add_argument("--run-dir", required=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "prepare-run":
        summary = prepare_run(args.input_file, args.run_root, args.custom_prompt_file, args.task_slug)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["valid_links"] > 0 else 2
    if args.command == "crawl":
        summary = asyncio.run(crawl_run(args.run_dir))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "finalize-broadcast":
        summary = finalize_broadcast(args.run_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
