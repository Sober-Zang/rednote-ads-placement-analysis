# -*- coding: utf-8 -*-
"""Run-scoped JSON storage adapter for the internalized Xiaohongshu crawler."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

import config

try:
    from tools.words import AsyncWordCloudGenerator
except Exception:  # pragma: no cover - optional dependency path
    AsyncWordCloudGenerator = None  # type: ignore


@dataclass
class NoteRecord:
    order: int
    source_url: str
    resolved_url: str
    note_id: str = ""
    title: str = ""
    author_nickname: str = ""
    folder_name: str = ""
    note_dir: Optional[Path] = None
    manifest_path: Optional[Path] = None
    reference_index_path: Optional[Path] = None
    references: list[dict[str, Any]] = field(default_factory=list)
    reference_counts: dict[str, int] = field(default_factory=lambda: {
        "text": 0,
        "image": 0,
        "comment": 0,
        "data": 0,
    })
    available_assets: list[str] = field(default_factory=list)
    primary_files: dict[str, str] = field(default_factory=dict)


class RuntimeStore:
    REF_PREFIX = {
        "text": "T",
        "image": "I",
        "comment": "C",
        "data": "D",
    }

    def __init__(self) -> None:
        self.run_dir: Optional[Path] = None
        self.creators_dir: Optional[Path] = None
        self.note_records: dict[str, NoteRecord] = {}
        self.note_id_to_record: dict[str, NoteRecord] = {}
        self.wordcloud_generator = None

    def initialize(self, run_dir: Path, link_entries: List[dict[str, Any]]) -> None:
        self.run_dir = Path(run_dir)
        self.creators_dir = self.run_dir / "creators"
        self.creators_dir.mkdir(parents=True, exist_ok=True)
        self.note_records.clear()
        self.note_id_to_record.clear()
        for entry in link_entries:
            order = int(entry.get("order", 0))
            source_url = entry.get("raw_url", "")
            resolved_url = entry.get("resolved_url", "") or entry.get("normalized_url", "")
            note_id = self._extract_note_id(resolved_url)
            record = NoteRecord(order=order, source_url=source_url, resolved_url=resolved_url, note_id=note_id)
            self.note_records[str(order)] = record
            if note_id:
                self.note_id_to_record[note_id] = record
        if AsyncWordCloudGenerator and config.ENABLE_GET_WORDCLOUD:
            try:
                self.wordcloud_generator = AsyncWordCloudGenerator()
            except Exception:
                self.wordcloud_generator = None

    async def update_note(self, note_item: Dict[str, Any]) -> None:
        note_id = note_item.get("note_id", "")
        record = self._get_or_create_record(note_id, note_item)
        note_dir = self._ensure_note_dir(record, note_item)
        raw_dir = note_dir / "raw"
        manifests_dir = note_dir / "manifests"

        note_json = raw_dir / "note.json"
        note_text = raw_dir / "note_text.md"
        metrics_json = raw_dir / "metrics.json"
        meta_json = raw_dir / "meta.json"

        await self._write_json(note_json, note_item)
        await self._write_text(note_text, (note_item.get("desc") or "").strip() + "\n")
        await self._write_json(metrics_json, note_item.get("interact_info", {}))
        await self._write_json(
            meta_json,
            {
                "title": note_item.get("title") or note_item.get("desc", "")[:120],
                "author_nickname": note_item.get("user", {}).get("nickname", ""),
                "source_url": record.source_url,
                "resolved_url": record.resolved_url,
                "xsec_token": note_item.get("xsec_token"),
                "xsec_source": note_item.get("xsec_source"),
                "publish_time": note_item.get("time"),
                "tags": [tag.get("name") for tag in note_item.get("tag_list", []) if tag.get("name")],
            },
        )

        record.available_assets = sorted(set(record.available_assets + ["note.json", "note_text.md", "metrics.json", "meta.json"]))
        record.primary_files.update(
            {
                "note_json": str(note_json),
                "note_text": str(note_text),
                "metrics_json": str(metrics_json),
                "meta_json": str(meta_json),
            }
        )

        self._add_reference(record, "text", note_text, "全文", (note_item.get("desc") or "").strip()[:200])
        self._add_reference(record, "data", metrics_json, "互动数据", json.dumps(note_item.get("interact_info", {}), ensure_ascii=False)[:200])
        await self._flush_note_manifest(record)
        await self._flush_reference_index(record)

    async def update_comments(self, note_id: str, comments: List[Dict[str, Any]]) -> None:
        if not comments:
            return
        record = self.note_id_to_record.get(note_id)
        if record is None:
            record = self._get_or_create_record(note_id, {})
        note_dir = self._ensure_note_dir(record, {})
        raw_dir = note_dir / "raw"
        assets_dir = note_dir / "assets"
        comments_json = raw_dir / "comments.json"
        comments_md = raw_dir / "comments.md"
        await self._write_json(comments_json, comments)

        lines = []
        for idx, comment in enumerate(comments, start=1):
            content = (comment.get("content") or "").strip()
            nickname = comment.get("user_info", {}).get("nickname") or ""
            lines.append(f"{idx}. {nickname}: {content}".strip())
            self._add_reference(record, "comment", comments_json, f"评论 {idx}", content[:200])
        await self._write_text(comments_md, "\n".join(lines) + ("\n" if lines else ""))

        record.available_assets = sorted(set(record.available_assets + ["comments.json", "comments.md"]))
        record.primary_files.update(
            {
                "comments_json": str(comments_json),
                "comments_md": str(comments_md),
            }
        )

        if self.wordcloud_generator:
            save_prefix = assets_dir / "comments"
            try:
                await self.wordcloud_generator.generate_word_frequency_and_cloud(comments, str(save_prefix))
                freq_path = assets_dir / "comments_word_freq.json"
                cloud_path = assets_dir / "comments_word_cloud.png"
                if freq_path.exists():
                    record.available_assets.append("comments_word_freq.json")
                    record.primary_files["comments_word_freq_json"] = str(freq_path)
                if cloud_path.exists():
                    record.available_assets.append("comments_word_cloud.png")
                    record.primary_files["comments_word_cloud_png"] = str(cloud_path)
                    self._add_reference(record, "image", cloud_path, "评论词云图", "评论高频词云图")
            except Exception:
                pass

        await self._flush_note_manifest(record)
        await self._flush_reference_index(record)

    async def update_image(self, note_id: str, pic_content: bytes, extension_file_name: str) -> None:
        record = self.note_id_to_record.get(note_id)
        if record is None:
            record = self._get_or_create_record(note_id, {})
        note_dir = self._ensure_note_dir(record, {})
        image_path = note_dir / "images" / extension_file_name
        await self._write_bytes(image_path, pic_content)
        record.available_assets.append(f"images/{extension_file_name}")
        self._add_reference(record, "image", image_path, extension_file_name, extension_file_name)
        await self._flush_note_manifest(record)
        await self._flush_reference_index(record)

    async def update_video(self, note_id: str, video_content: bytes, extension_file_name: str) -> None:
        record = self.note_id_to_record.get(note_id)
        if record is None:
            record = self._get_or_create_record(note_id, {})
        note_dir = self._ensure_note_dir(record, {})
        video_path = note_dir / "assets" / "videos" / extension_file_name
        await self._write_bytes(video_path, video_content)
        record.available_assets.append(f"assets/videos/{extension_file_name}")
        await self._flush_note_manifest(record)

    async def save_creator(self, user_id: str, creator: Dict[str, Any]) -> None:
        if not self.creators_dir:
            return
        creator_path = self.creators_dir / f"{self._sanitize(user_id)}.json"
        await self._write_json(creator_path, creator)

    def export_note_summaries(self) -> List[dict[str, Any]]:
        summaries = []
        for record in sorted(self.note_records.values(), key=lambda item: item.order):
            if not record.note_dir:
                continue
            summaries.append(
                {
                    "order": record.order,
                    "note_id": record.note_id,
                    "title": record.title,
                    "author_nickname": record.author_nickname,
                    "source_url": record.source_url,
                    "resolved_url": record.resolved_url,
                    "folder_name": record.folder_name,
                    "folder_path": str(record.note_dir),
                    "analysis_report_path": record.primary_files.get("analysis_report", ""),
                    "available_assets": sorted(set(record.available_assets)),
                    "primary_files": record.primary_files,
                }
            )
        return summaries

    def _get_or_create_record(self, note_id: str, note_item: Dict[str, Any]) -> NoteRecord:
        record = self.note_id_to_record.get(note_id)
        if record:
            return record
        order = len(self.note_records) + 1
        record = NoteRecord(order=order, source_url="", resolved_url="", note_id=note_id)
        self.note_records[str(order)] = record
        self.note_id_to_record[note_id] = record
        if note_item:
            self._ensure_note_dir(record, note_item)
        return record

    def _ensure_note_dir(self, record: NoteRecord, note_item: Dict[str, Any]) -> Path:
        if record.note_dir:
            if note_item:
                record.title = record.title or (note_item.get("title") or note_item.get("desc", "")[:120])
                record.author_nickname = record.author_nickname or note_item.get("user", {}).get("nickname", "")
            return record.note_dir
        title = note_item.get("title") or note_item.get("desc", "")[:120] or record.title or f"未命名笔记_{record.order}"
        author = note_item.get("user", {}).get("nickname") or record.author_nickname or "未知作者"
        record.title = title
        record.author_nickname = author
        record.folder_name = f"{record.order:02d}_{self._sanitize(title)}__{self._sanitize(author)}"
        note_dir = self.run_dir / "notes" / record.folder_name  # type: ignore[operator]
        for sub in ["raw", "images", "assets", "assets/videos", "analysis", "manifests"]:
            (note_dir / sub).mkdir(parents=True, exist_ok=True)
        record.note_dir = note_dir
        record.manifest_path = note_dir / "manifests" / "note_manifest.json"
        record.reference_index_path = note_dir / "manifests" / "reference_index.json"
        self.note_id_to_record[record.note_id] = record
        return note_dir

    async def _flush_note_manifest(self, record: NoteRecord) -> None:
        if not record.manifest_path:
            return
        await self._write_json(
            record.manifest_path,
            {
                "note_id": record.note_id,
                "title": record.title,
                "author_nickname": record.author_nickname,
                "source_url": record.source_url,
                "resolved_url": record.resolved_url,
                "folder_name": record.folder_name,
                "available_assets": sorted(set(record.available_assets)),
                "primary_files": record.primary_files,
                "analysis_report_path": record.primary_files.get("analysis_report", ""),
            },
        )

    async def _flush_reference_index(self, record: NoteRecord) -> None:
        if not record.reference_index_path:
            return
        await self._write_json(record.reference_index_path, record.references)

    def _add_reference(self, record: NoteRecord, ref_type: str, path: Path, position: str, excerpt: str) -> None:
        if record.note_dir is None:
            return
        absolute_path = str(path.resolve())
        if any(ref["absolute_path"] == absolute_path and ref["position"] == position for ref in record.references):
            return
        record.reference_counts[ref_type] += 1
        ref_id = f"{self.REF_PREFIX[ref_type]}{record.reference_counts[ref_type]}"
        record.references.append(
            {
                "ref_id": ref_id,
                "ref_type": ref_type,
                "absolute_path": absolute_path,
                "position": position,
                "excerpt": excerpt,
            }
        )

    @staticmethod
    async def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
            await handle.write("\n")

    @staticmethod
    async def _write_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as handle:
            await handle.write(text)

    @staticmethod
    async def _write_bytes(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as handle:
            await handle.write(payload)

    @staticmethod
    def _sanitize(value: str) -> str:
        value = re.sub(r"\s+", " ", value.strip())
        value = re.sub(r'[\\\\/:*?"<>|]+', "_", value)
        value = value.replace("\n", " ")
        return value[:80] or "untitled"

    @staticmethod
    def _extract_note_id(url: str) -> str:
        if not url:
            return ""
        url = url.rstrip("/")
        if "/explore/" in url:
            return url.split("/explore/")[-1].split("?")[0]
        if "/discovery/item/" in url:
            return url.split("/discovery/item/")[-1].split("?")[0]
        return ""


_STORE = RuntimeStore()


def initialize_runtime_store(run_dir: str | Path, link_entries: List[dict[str, Any]]) -> None:
    _STORE.initialize(Path(run_dir), link_entries)


def export_note_summaries() -> List[dict[str, Any]]:
    return _STORE.export_note_summaries()


def get_video_url_arr(note_item: Dict) -> List[str]:
    if note_item.get("type") != "video":
        return []
    video_dict = note_item.get("video") or {}
    consumer = video_dict.get("consumer", {})
    origin_key = consumer.get("origin_video_key") or consumer.get("originVideoKey") or ""
    if origin_key:
        return [f"http://sns-video-bd.xhscdn.com/{origin_key}"]
    media = video_dict.get("media", {})
    stream = media.get("stream", {})
    videos = stream.get("h264") or []
    if isinstance(videos, list):
        return [video.get("master_url") for video in videos if video.get("master_url")]
    return []


async def update_xhs_note(note_item: Dict) -> None:
    await _STORE.update_note(note_item)


async def batch_update_xhs_note_comments(note_id: str, comments: List[Dict]) -> None:
    await _STORE.update_comments(note_id, comments)


async def save_creator(user_id: str, creator: Dict) -> None:
    await _STORE.save_creator(user_id, creator)


async def update_xhs_note_image(note_id: str, pic_content: bytes, extension_file_name: str) -> None:
    await _STORE.update_image(note_id, pic_content, extension_file_name)


async def update_xhs_note_video(note_id: str, video_content: bytes, extension_file_name: str) -> None:
    await _STORE.update_video(note_id, video_content, extension_file_name)
