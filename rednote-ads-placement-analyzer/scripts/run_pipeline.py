#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from _common import (
    ASSETS_ROOT,
    CONTRACT_VERSION,
    OUTPUT_ROOT,
    RUNTIME_ROOT,
    PRODUCT_ROOT,
    RUNS_ROOT,
    VENDOR_ROOT,
    WORKSPACE_ROOT,
    ensure_contract_roots,
    ensure_unique_path,
    ensure_vendor_on_path,
    is_within,
    read_json,
    sanitize_fs_component,
    slugify,
    to_run_relative,
    write_json,
    write_text,
)

URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
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
NON_INSTRUCTION_HINTS = (
    "打开【小红书】",
    "打开「今日头条APP」",
    "打开「今日头条极速版APP」",
    "就能看到内容",
    "快去瞧瞧",
    "点击链接打开",
    "复制此条消息",
    "复制一下这行字",
)


def clean_url(url: str) -> str:
    return url.rstrip("，。！？、；：)]}>\"'")


def extract_urls(raw_text: str) -> list[str]:
    return [clean_url(match.group(0)) for match in URL_PATTERN.finditer(raw_text)]


def is_xhs_short_link(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.lower() == "xhslink.com"


def unwrap_xhs_login_redirect(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "www.xiaohongshu.com" or parsed.path != "/login":
        return url
    redirect_values = parse_qs(parsed.query).get("redirectPath", [])
    if not redirect_values:
        return url
    redirect_url = unquote(redirect_values[0]).strip()
    if redirect_url.startswith("http://") or redirect_url.startswith("https://"):
        return redirect_url
    if redirect_url.startswith("/"):
        return f"https://www.xiaohongshu.com{redirect_url}"
    return url


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
                return unwrap_xhs_login_redirect(str(response.url))
        except httpx.HTTPError as exc:
            last_error = exc
            await asyncio.sleep(attempt + 1)
    raise last_error or RuntimeError(f"Failed to resolve url: {url}")


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
        if any(hint in normalized for hint in NON_INSTRUCTION_HINTS):
            continue
        if "今日头条" in normalized or "小红书" in normalized:
            continue
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


def load_input_text(input_file: str | None, input_text: str | None) -> str:
    if input_text is not None:
        return input_text
    if input_file:
        return Path(input_file).read_text(encoding="utf-8")
    raise SystemExit("Either --input-file or --input-text is required.")


def login_state_dir() -> Path:
    return WORKSPACE_ROOT / "xhs_user_data_dir"


def legacy_login_state_dir() -> Path:
    return WORKSPACE_ROOT / "browser_data" / "xhs_user_data_dir"


def normalize_login_state_dir() -> Path:
    primary = login_state_dir()
    legacy = legacy_login_state_dir()
    if legacy.exists():
        if primary.exists():
            shutil.rmtree(legacy, ignore_errors=True)
        else:
            legacy.rename(primary)
    primary.mkdir(parents=True, exist_ok=True)
    return primary


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


def prepare_run(
    input_file: str | None,
    input_text: str | None,
    run_root: str | None,
    custom_prompt_file: str | None,
    task_slug: str | None,
) -> dict[str, Any]:
    output_root, _ = ensure_contract_roots()
    raw_text = load_input_text(input_file, input_text)
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
    selected_root = Path(run_root or RUNS_ROOT).expanduser().resolve()
    if not is_within(selected_root, output_root):
        raise SystemExit(f"run-root must live under OUTPUT_DIR: {output_root}")
    run_dir = ensure_unique_path(selected_root / run_id)
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
        "contract_version": CONTRACT_VERSION,
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
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return (params.get("noteId") or [""])[0]


def canonicalize_xhs_note_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc not in {"www.xiaohongshu.com", "xiaohongshu.com"}:
        return url
    if parsed.path != "/404":
        return url

    params = parse_qs(parsed.query, keep_blank_values=True)
    note_id = (params.get("noteId") or [""])[0]
    if not note_id:
        return url

    rebuilt_params: list[tuple[str, str]] = []
    for key in ("xsec_token", "xsec_source", "app_platform", "app_version", "share_from_user_hidden", "type",
                "author_share", "xhsshare", "shareRedId", "apptime", "share_id"):
        for value in params.get(key, []):
            rebuilt_params.append((key, value))
    from urllib.parse import urlencode

    query = urlencode(rebuilt_params, doseq=True)
    rebuilt = parsed._replace(path=f"/discovery/item/{note_id}", query=query)
    return rebuilt.geturl()


async def crawl_run(run_dir: str) -> dict[str, Any]:
    output_root, runtime_root = ensure_contract_roots()
    run_path = Path(run_dir)
    if not is_within(run_path, output_root):
        raise SystemExit(f"run-dir must live under OUTPUT_DIR: {output_root}")
    link_manifest_path = run_path / "manifests" / "link_manifest.json"
    run_manifest_path = run_path / "manifests" / "run_manifest.json"
    entries = read_json(link_manifest_path)
    valid_entries = [entry for entry in entries if entry["is_valid_xhs"]]
    if not valid_entries:
        raise SystemExit("No valid Xiaohongshu links found in this run.")

    for entry in valid_entries:
        resolved = await resolve_url(entry["raw_url"])
        resolved = canonicalize_xhs_note_url(resolved)
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
            "RUNTIME_DIR": str(runtime_root),
            "LOGIN_STATE_DIR": str(normalize_login_state_dir()),
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
            "CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES": 500,
            "MAX_CONCURRENCY_NUM": 1,
            "CRAWLER_MAX_SLEEP_SEC": 1,
            "STOP_WORDS_FILE": str(VENDOR_ROOT / "docs" / "hit_stopwords.txt"),
            "FONT_PATH": str(VENDOR_ROOT / "docs" / "STZHONGS.TTF"),
            "LOGIN_STATE_CONFIRMED": False,
        }
    )
    login_mode, login_reason = await determine_login_mode(config)
    config.apply_runtime_config(
        {
            "REQUIRE_LOGIN": False,
            "LOGIN_STATE_CONFIRMED": login_mode == "authenticated",
        }
    )
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
    ensure_vendor_on_path()
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


def clear_login_state_dir() -> None:
    for candidate in (login_state_dir(), legacy_login_state_dir()):
        if candidate.exists():
            shutil.rmtree(candidate, ignore_errors=True)
    login_state_dir().mkdir(parents=True, exist_ok=True)


async def launch_login_probe_browser(wait_seconds: int = 300, allow_wait: bool = False) -> tuple[bool, str]:
    ensure_vendor_on_path()
    from playwright.async_api import async_playwright  # type: ignore
    from media_platform.xhs.core import XiaoHongShuCrawler  # type: ignore
    import config  # type: ignore

    crawler: Any = None
    try:
        normalized_login_state_dir = normalize_login_state_dir()
        config.apply_runtime_config(
            {
                "LOGIN_STATE_DIR": str(normalized_login_state_dir),
                "RUNTIME_DIR": str(OUTPUT_ROOT),
                "SAVE_LOGIN_STATE": True,
                "LOGIN_STATE_CONFIRMED": False,
            }
        )
        async with async_playwright() as playwright:
            async def open_probe_context() -> tuple[Any, Any]:
                current = XiaoHongShuCrawler()
                browser_context = await current.launch_browser(
                    playwright.chromium,
                    None,
                    current.user_agent,
                    headless=False,
                )
                current.browser_context = browser_context
                await browser_context.add_init_script(path=str(VENDOR_ROOT / "libs" / "stealth.min.js"))
                current.context_page = await browser_context.new_page()
                await current.context_page.goto(current.index_url, wait_until="domcontentloaded", timeout=120000)
                current.xhs_client = await current.create_xhs_client(None)
                return current, browser_context

            crawler, browser_context = await open_probe_context()
            initial_probe_attempts = 4 if allow_wait else 1
            for attempt in range(initial_probe_attempts):
                await crawler.xhs_client.update_cookies(browser_context)
                if await crawler.xhs_client.pong():
                    return True, "auto_detected_existing_login"
                if attempt < initial_probe_attempts - 1:
                    await asyncio.sleep(2)
            if not allow_wait:
                return False, "not_logged_in"
            try:
                clear_login_state_dir()
                await browser_context.clear_cookies()
                await crawler.context_page.evaluate(
                    "() => { try { localStorage.clear(); } catch (e) {} try { sessionStorage.clear(); } catch (e) {} }"
                )
                await crawler.context_page.goto(crawler.index_url, wait_until="domcontentloaded", timeout=120000)
            except Exception:
                pass
            print(
                "当前未检测到已完成的小红书登录，已打开机器控制的 Chrome 并进入小红书。\n"
                "请在 300 秒内完成登录；若不需要登录，直接关闭浏览器即可，系统会按无登录流程继续。\n"
                "登录成功后无需额外回复，系统会自动继续后续任务。",
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
            if crawler is not None:
                await crawler.close()
        except Exception:
            pass


async def determine_login_mode(config_module) -> tuple[str, str]:
    login_confirmed, reason = await launch_login_probe_browser(wait_seconds=300, allow_wait=True)
    if login_confirmed:
        return "authenticated", reason
    print("未在 300 秒内确认登录成功，或登录窗口已关闭，将继续无登录流程。", flush=True)
    return "anonymous", reason


async def run_login_only() -> dict[str, Any]:
    login_mode, login_reason = await determine_login_mode(None)
    return {"login_mode": login_mode, "login_reason": login_reason}


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


def _strip_citation_marks(text: str) -> str:
    cleaned = re.sub(r"\[[A-Z]+\d+\]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_markdown_section(markdown: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, markdown, flags=re.M | re.S)
    if not match:
        return ""
    return _strip_citation_marks(match.group(1))


def build_core_conclusion(aggregate_report: Path | None) -> str:
    if not aggregate_report or not aggregate_report.exists():
        return "本次有效样本已经完成归档，但综合报告尚未落档；只有在综合报告可用时，才应把这次 run 视为完整交付。"

    markdown = aggregate_report.read_text(encoding="utf-8")
    parts = [
        _extract_markdown_section(markdown, "摘要概览"),
        _extract_markdown_section(markdown, "关键词"),
        _extract_markdown_section(markdown, "分析总结：作为转转广告投放专员，应该如何在小红书投广告"),
        _extract_markdown_section(markdown, "跨样本共性机制"),
        _extract_markdown_section(markdown, "可沉淀的方法论条目"),
        _extract_markdown_section(markdown, "综合结论"),
    ]
    merged = " ".join(part for part in parts if part)
    merged = re.sub(r"\s+", " ", merged).strip()
    if not merged:
        return "本次综合报告已经生成，但尚未提炼出可供最终播报直接引用的核心结论，请优先查看综合报告正文。"
    if len(merged) < 100:
        merged = (
            merged
            + " 这次综合报告的重点不是重复平台卖点，而是把用户真正会比较的变量、能建立信任的证据，以及适合转转落地投放的表达方式一起梳理清楚。"
        )
    if len(merged) > 300:
        candidate = merged[:300]
        boundary = max(
            candidate.rfind("。"),
            candidate.rfind("！"),
            candidate.rfind("？"),
            candidate.rfind("；"),
            candidate.rfind("，"),
        )
        if boundary >= 100:
            summary = candidate[: boundary + 1].strip()
        else:
            summary = candidate.rstrip("，。；、 ") + "。"
    else:
        summary = merged.rstrip("，。；、 ") + "。"
    if len(summary) < 100:
        summary = (
            summary.rstrip("。")
            + " 这次综合报告的重点，是把用户真正会拿来做比较的决策变量、最能建立信任的证据形式，以及更适合转转在小红书使用的表达方式一起收束成了可执行结论。"
        )
        summary = summary[:300].rstrip("，。；、 ") + "。"
    return summary


def finalize_broadcast(run_dir: str) -> dict[str, Any]:
    output_root, _ = ensure_contract_roots()
    run_path = Path(run_dir)
    if not is_within(run_path, output_root):
        raise SystemExit(f"run-dir must live under OUTPUT_DIR: {output_root}")
    link_entries = read_json(run_path / "manifests" / "link_manifest.json")
    run_manifest_path = run_path / "manifests" / "run_manifest.json"
    run_manifest = read_json(run_manifest_path)
    invalid_links = [entry["raw_url"] for entry in link_entries if not entry["is_valid_xhs"]]
    single_reports, aggregate_reports = find_reports(run_path)
    login_mode = run_manifest.get("login_mode", "anonymous")
    has_reports = bool(single_reports or aggregate_reports)
    aggregate_report = aggregate_reports[0] if aggregate_reports else None
    broadcast_status = "reports_ready" if has_reports else "awaiting_reports"
    sub_comment_error_happened = False
    for log_path in run_path.rglob("*.log"):
        try:
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(token in log_text for token in ("DataFetchError", "RetryError", "ConnectError")):
            sub_comment_error_happened = True
            break

    for report in single_reports:
        note_dir = report.parents[1]
        manifest_path = note_dir / "manifests" / "note_manifest.json"
        if manifest_path.exists():
            note_manifest = read_json(manifest_path)
            note_manifest["analysis_report_path"] = to_run_relative(report, run_path)
            primary_files = note_manifest.setdefault("primary_files", {})
            primary_files["analysis_report"] = to_run_relative(report, run_path)
            write_json(manifest_path, note_manifest)

    header = "✅ 小红书广告投放分析完成！" if has_reports else "⚠️ 小红书抓取已完成，但分析报告尚未生成。"
    lines = [header, "", "📁 输出目录", f"* 新 run: {run_path.name}"]
    status_label = "报告已就绪（reports_ready）" if broadcast_status == "reports_ready" else "等待报告（awaiting_reports）"
    login_label = "已登录（authenticated）" if login_mode == "authenticated" else "未登录（anonymous）"
    lines.append(f"* 状态: {status_label}")
    lines.append(f"* 登录状态: {login_label}")
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
        lines.append(f"* {build_core_conclusion(aggregate_report)}")
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
    if sub_comment_error_happened:
        lines.append("* 评论子回复抓取过程中出现多次 DataFetchError / RetryError / ConnectError，但本次口径是跳过子回复继续执行，未阻断 run。")

    write_text(run_path / "logs" / "final_broadcast.md", "\n".join(lines).rstrip() + "\n")
    run_manifest["outputs"] = [to_run_relative(path, run_path) for path in single_reports + aggregate_reports + [run_path / "logs" / "final_broadcast.md"]]
    summaries = run_manifest.get("note_summaries", [])
    for summary in summaries:
        folder_path = summary.get("folder_path")
        if not folder_path:
            continue
        manifest_path = run_path / folder_path / "manifests" / "note_manifest.json"
        if not manifest_path.exists():
            continue
        note_manifest = read_json(manifest_path)
        summary["analysis_report_path"] = note_manifest.get("analysis_report_path", "")
        summary["primary_files"] = note_manifest.get("primary_files", summary.get("primary_files", {}))
    run_manifest["note_summaries"] = summaries
    run_manifest["status"] = broadcast_status
    write_json(run_manifest_path, run_manifest)
    return {"run_dir": str(run_path), "single_reports": len(single_reports), "aggregate_reports": len(aggregate_reports)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run-scoped pipeline for rednote ads placement analysis.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("login-only")

    prepare = subparsers.add_parser("prepare-run")
    input_group = prepare.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input-file")
    input_group.add_argument("--input-text")
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
    if args.command == "login-only":
        summary = asyncio.run(run_login_only())
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "prepare-run":
        summary = prepare_run(args.input_file, args.input_text, args.run_root, args.custom_prompt_file, args.task_slug)
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
