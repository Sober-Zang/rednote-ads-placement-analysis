#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
import select
import sys
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
LOGIN_YES_EXAMPLES = (
    "需要登录",
    "要登录小红书",
    "我先去登录",
    "登录后继续",
    "1",
)
LOGIN_NO_EXAMPLES = (
    "不需要登录",
    "不用登录",
    "直接继续",
    "无登录继续",
    "2",
)
SHARE_NOISE_PATTERNS = (
    "复制后打开【小红书】查看笔记",
    "复制后直接打开【小红书】",
    "前往【小红书】看看这篇分享吧",
    "前往【小红书】看看详情吧",
    "存好这段口令，去【小红书】逛逛吧",
    "存好这段，去【小红书】逛逛笔记",
    "复制文字→打开【小红书】→立即查看笔记详情",
    "笔记即刻可见",
)


def clean_url(url: str) -> str:
    return url.rstrip("，。！？、；：)]}>\"'")


def extract_urls(raw_text: str) -> list[str]:
    return [clean_url(match.group(0)) for match in URL_PATTERN.finditer(raw_text)]


def is_xhs_short_link(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower() == "xhslink.com"


async def resolve_url(url: str) -> str:
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )
    }
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, headers=headers) as client:
                response = await client.get(url)
                response.raise_for_status()
                return str(response.url)
        except httpx.HTTPError as exc:
            last_error = exc
            await asyncio.sleep(attempt + 1)
    raise last_error or RuntimeError(f"Failed to resolve url: {url}")


def read_line_with_timeout(timeout_seconds: int) -> str | None:
    ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
    if not ready:
        return None
    line = sys.stdin.readline()
    if not line:
        return None
    return line.strip()


def interpret_login_intent(user_text: str | None) -> str | None:
    if not user_text:
        return None
    normalized = user_text.strip().lower()
    if not normalized:
        return None

    yes_tokens = (
        "1",
        "y",
        "yes",
        "要登录",
        "需要登录",
        "登录后继续",
        "我先去登录",
        "希望登录",
        "想登录",
        "去登录",
        "登录",
    )
    no_tokens = (
        "2",
        "n",
        "no",
        "不用登录",
        "不需要登录",
        "无登录继续",
        "直接继续",
        "继续",
        "先不登录",
        "不登录",
        "不用",
    )

    if normalized in yes_tokens or any(token in normalized for token in yes_tokens if len(token) > 1):
        return "login"
    if normalized in no_tokens or any(token in normalized for token in no_tokens if len(token) > 1):
        return "anonymous"
    return None


def normalize_instruction_text(text: str) -> str:
    normalized = text
    for phrase in SHARE_NOISE_PATTERNS:
        normalized = normalized.replace(phrase, " ")
    normalized = re.sub(r"[→~…·]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip(" \n\t:：，。！？!、；;")


def extract_explicit_instruction(raw_text: str) -> str:
    candidate_lines: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        urls = extract_urls(line)
        if any(is_xhs_short_link(url) or urlparse(url).scheme in {"http", "https"} for url in urls):
            continue
        normalized = normalize_instruction_text(line)
        if normalized:
            candidate_lines.append(normalized)
    return "\n".join(candidate_lines).strip()


def build_run_specific_prompt(instruction_text: str) -> str:
    return (
        "# 本次 run 专属 Prompt\n\n"
        "## 用户额外任务目标\n\n"
        f"{instruction_text.strip()}\n\n"
        "## 执行约束\n\n"
        "- 本次 run 以用户额外要求为最高任务目标。\n"
        "- 若本次 run 同时包含小红书链接，先完成下载、归档与证据整理，再按本 Prompt 执行。\n"
        "- 若本次 run 不包含小红书链接，则无需执行下载抓取，直接围绕本 Prompt 回答。\n"
        "- 本 Prompt 只属于当前 run，不得写回全局 `assets/`。\n"
    )


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


def load_prompt_text(custom_prompt_file: str | None, raw_text: str) -> tuple[str, str, str]:
    if custom_prompt_file:
        prompt_path = Path(custom_prompt_file)
        return "run-specific", prompt_path.read_text(encoding="utf-8"), prompt_path.read_text(encoding="utf-8").strip()
    explicit_instruction = extract_explicit_instruction(raw_text)
    if explicit_instruction:
        return "run-specific", build_run_specific_prompt(explicit_instruction), explicit_instruction
    return "standard", (ASSETS_ROOT / "standard_analysis_prompt.md").read_text(encoding="utf-8"), ""


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
    mode, prompt_text, explicit_instruction = load_prompt_text(custom_prompt_file, raw_text)
    derived_slug = task_slug or slugify(raw_text)
    run_id = create_run_id(derived_slug)
    run_dir = Path(run_root or RUNS_ROOT) / run_id
    init_run_dirs(run_dir)

    write_text(run_dir / "inputs" / "raw_user_input.md", raw_text.rstrip() + "\n")
    write_text(run_dir / "inputs" / "invalid_links.md", render_invalid_links(entries))
    write_text(run_dir / "prompt" / "used_prompt.md", prompt_text.rstrip() + "\n")
    write_json(
        run_dir / "prompt" / "prompt_mode.json",
        {
            "mode": mode,
            "source": custom_prompt_file or ("run-generated" if mode == "run-specific" else "assets/standard_analysis_prompt.md"),
            "explicit_instruction": explicit_instruction,
        },
    )
    write_json(run_dir / "manifests" / "link_manifest.json", entries)

    status = "prepared"
    if not valid_entries and mode == "run-specific":
        status = "prompt_only"
    elif not valid_entries:
        status = "failed_validation"
    run_manifest = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_slug": derived_slug,
        "source_prompt_mode": mode,
        "explicit_instruction": explicit_instruction,
        "chat_output_mode": "strict_final_broadcast_match" if mode == "standard" else "contextual_response",
        "valid_links": [entry["raw_url"] for entry in valid_entries],
        "invalid_links": [entry["raw_url"] for entry in entries if not entry["is_valid_xhs"]],
        "note_folders": [],
        "outputs": [],
        "status": status,
        "should_crawl": bool(valid_entries),
    }
    write_json(run_dir / "manifests" / "run_manifest.json", run_manifest)
    return {
        "run_dir": str(run_dir),
        "run_id": run_id,
        "valid_links": len(valid_entries),
        "invalid_links": len(entries) - len(valid_entries),
        "status": status,
        "prompt_mode": mode,
    }


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
    login_mode, login_reason = await determine_login_mode(config)
    config.apply_runtime_config({"REQUIRE_LOGIN": False})
    run_manifest = read_json(run_manifest_path)
    run_manifest["login_mode"] = login_mode
    run_manifest["login_mode_reason"] = login_reason
    run_manifest["status"] = "crawling"
    write_json(run_manifest_path, run_manifest)
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
    apply_login_mode_to_note_manifests(run_path, login_mode)
    return {"run_dir": str(run_path), "notes": len(summaries), "status": run_manifest["status"]}


async def check_login_state_once(config_module) -> bool:
    from playwright.async_api import async_playwright  # type: ignore
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError  # type: ignore
    from media_platform.xhs.core import XiaoHongShuCrawler  # type: ignore

    crawler = XiaoHongShuCrawler()
    try:
        async with async_playwright() as playwright:
            browser_context = await crawler.launch_browser(
                playwright.chromium,
                None,
                crawler.user_agent,
                headless=config_module.HEADLESS,
            )
            crawler.browser_context = browser_context
            await browser_context.add_init_script(path=str(VENDOR_ROOT / "libs" / "stealth.min.js"))
            crawler.context_page = await browser_context.new_page()
            try:
                await crawler.context_page.goto(crawler.index_url)
                crawler.xhs_client = await crawler.create_xhs_client(None)
                return await crawler.xhs_client.pong()
            except PlaywrightTimeoutError:
                # Treat homepage timeout as "login not confirmed" so the run can fall back.
                return False
    finally:
        try:
            await crawler.close()
        except Exception:
            pass


async def launch_login_probe_browser(wait_seconds: int = 300, allow_wait: bool = False) -> tuple[bool, str]:
    from playwright.async_api import async_playwright  # type: ignore
    from media_platform.xhs.core import XiaoHongShuCrawler  # type: ignore

    crawler = XiaoHongShuCrawler()
    try:
        async with async_playwright() as playwright:
            browser_context = await crawler.launch_browser(
                playwright.chromium,
                None,
                crawler.user_agent,
                headless=False,
            )
            crawler.browser_context = browser_context
            await browser_context.add_init_script(path=str(VENDOR_ROOT / "libs" / "stealth.min.js"))
            crawler.context_page = await browser_context.new_page()
            await crawler.context_page.goto(crawler.index_url, wait_until="domcontentloaded", timeout=120000)
            crawler.xhs_client = await crawler.create_xhs_client(None)
            await crawler.xhs_client.update_cookies(browser_context)
            if await crawler.xhs_client.pong():
                return True, "auto_detected_existing_login"
            if not allow_wait:
                return False, "not_logged_in"
            print(
                "已打开机器控制的 Chrome，请在 300 秒内完成小红书登录。\n"
                "若 300 秒内未完成，或你主动关闭了浏览器，将自动按无登录流程继续。\n"
                "示例回复：无需再回复，完成登录后等待自动继续。",
                flush=True,
            )
            deadline = asyncio.get_running_loop().time() + wait_seconds
            while asyncio.get_running_loop().time() < deadline:
                if crawler.context_page.is_closed():
                    return False, "browser_closed"
                await crawler.xhs_client.update_cookies(browser_context)
                if await crawler.xhs_client.pong():
                    return True, "login_confirmed"
                await asyncio.sleep(3)
            return False, "timeout"
    except Exception as exc:
        return False, f"login_window_error:{exc}"
    finally:
        try:
            await crawler.close()
        except Exception:
            pass


async def determine_login_mode(config_module) -> tuple[str, str]:
    existing_login, reason = await launch_login_probe_browser(allow_wait=False)
    if existing_login:
        return "authenticated", reason

    prompt = (
        "当前未检测到已完成的小红书登录。你可以选择现在登录小红书账号，以提高评论区抓取完整度。\n"
        "若不登录，后续仍会继续执行，但评论区、二级评论和评论图片可能不完整。\n"
        "30 秒内请用自然语言回复是否登录。\n"
        f"可参考示例（需要登录）：{', '.join(LOGIN_YES_EXAMPLES)}\n"
        f"可参考示例（不登录）：{', '.join(LOGIN_NO_EXAMPLES)}\n"
        "若 30 秒内无回复，将默认继续无登录流程。\n> "
    )
    print(prompt, end="", flush=True)
    response = await asyncio.to_thread(read_line_with_timeout, 30)
    intent = interpret_login_intent(response)
    if intent != "login":
        return "anonymous", "user_declined_or_no_response"

    login_confirmed, reason = await launch_login_probe_browser(wait_seconds=300, allow_wait=True)
    if login_confirmed:
        return "authenticated", reason
    print("未在 300 秒内确认登录成功，或登录窗口已关闭，将继续无登录流程。", flush=True)
    return "anonymous", reason


def apply_login_mode_to_note_manifests(run_path: Path, login_mode: str) -> None:
    login_note = (
        "未登录执行：评论区、二级评论和评论图片可能不完整，报告与最终播报必须显式标注该影响。"
        if login_mode != "authenticated"
        else "已登录执行：评论抓取按当前设备保存的登录态完成。"
    )
    for manifest_path in run_path.glob("notes/*/manifests/note_manifest.json"):
        note_manifest = read_json(manifest_path)
        note_manifest["login_mode"] = login_mode
        note_manifest["login_mode_note"] = login_note
        write_json(manifest_path, note_manifest)


def find_reports(run_path: Path) -> tuple[list[Path], list[Path]]:
    single_reports = sorted(run_path.glob("notes/*/analysis/*_分析报告.md"))
    aggregate_reports = sorted(run_path.glob("aggregate/*_综合分析报告.md"))
    return single_reports, aggregate_reports


def finalize_broadcast(run_dir: str) -> dict[str, Any]:
    run_path = Path(run_dir)
    link_entries = read_json(run_path / "manifests" / "link_manifest.json")
    run_manifest_path = run_path / "manifests" / "run_manifest.json"
    run_manifest = read_json(run_manifest_path)
    invalid_links = [entry["raw_url"] for entry in link_entries if not entry["is_valid_xhs"]]
    single_reports, aggregate_reports = find_reports(run_path)
    login_mode = run_manifest.get("login_mode", "anonymous")
    has_reports = bool(single_reports or aggregate_reports)

    for report in single_reports:
        note_dir = report.parents[1]
        manifest_path = note_dir / "manifests" / "note_manifest.json"
        if manifest_path.exists():
            note_manifest = read_json(manifest_path)
            note_manifest["analysis_report_path"] = str(report)
            primary_files = note_manifest.setdefault("primary_files", {})
            primary_files["analysis_report"] = str(report)
            write_json(manifest_path, note_manifest)

    header = "✅ 小红书广告投放分析完成！" if has_reports else "⚠️ 小红书抓取已完成，但分析报告尚未生成。"
    lines = [header, "", "📁 输出目录", f"* 新 run: {run_path.name}"]
    if aggregate_reports:
        lines.append(f"* 综合报告: {aggregate_reports[0].name}")
    else:
        lines.append("* 综合报告: 无")
    lines.append("* 最终播报: final_broadcast.md")
    lines.extend(["", "📄 生成文件"])
    if single_reports:
        for report in single_reports:
            lines.append(f"* {report.name}")
    else:
        lines.append("* 暂无单篇分析报告")

    lines.extend(["", "💡核心结论"])
    if has_reports:
        lines.append("* 本次样本已经完成结构化归档，可从单篇报告和综合报告继续下钻。")
        lines.append("* 高价值结论优先以报告正文与引用证据为准。")
    else:
        lines.append("* 当前 run 仅完成抓取与结构化归档，尚未进入报告产出阶段。")
        lines.append("* 报告未生成前，不应把本次结果视为最终交付。")

    lines.extend(["", "⚠️注意"])
    if login_mode != "authenticated":
        lines.append("* 本次为未登录执行，评论区、二级评论和评论图片区可能不完整。")
    if invalid_links:
        for url in invalid_links:
            lines.append(f"* 你这次混入的非小红书链接被正确排除了：{url}")
    else:
        lines.append("* 本次输入中未发现非小红书链接。")

    write_text(run_path / "logs" / "final_broadcast.md", "\n".join(lines).rstrip() + "\n")
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
    if has_reports:
        run_manifest["status"] = "reports_ready"
    else:
        run_manifest["status"] = "awaiting_reports"
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
        return 0 if summary["valid_links"] > 0 or summary.get("status") == "prompt_only" else 2
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
