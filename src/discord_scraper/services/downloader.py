from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

import httpx


@dataclass
class DownloadTask:
    url: str
    filepath: Path
    channel_label: str


@dataclass
class DownloadStats:
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0

    @property
    def total_processed(self) -> int:
        return self.downloaded + self.skipped + self.failed


@dataclass
class ChannelDownloadStats:
    label: str
    total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0


class DownloaderService:
    def __init__(
        self,
        *,
        max_workers: int = 8,
        timeout: int = 60,
        on_progress: Callable[[str, str], None] | None = None,
    ) -> None:
        self._max_workers = max_workers
        self._timeout = timeout
        self._on_progress = on_progress

    def collect_tasks(self, message_files: list[Path]) -> list[DownloadTask]:
        tasks: list[DownloadTask] = []
        for json_path in sorted(message_files):
            with open(json_path, "r", encoding="utf-8") as f:
                messages = json.load(f)

            channel_dir = json_path.parent
            label = f"{channel_dir.parent.name}/{channel_dir.name}"
            attachments_dir = channel_dir / "attachments"

            has_attachments = False
            for msg in messages:
                for att in msg.get("attachments", []):
                    has_attachments = True
                    att_id = att["id"]
                    filename = att.get("filename", att_id)
                    safe_name = f"{att_id}_{filename}"
                    tasks.append(
                        DownloadTask(
                            url=att["url"],
                            filepath=attachments_dir / safe_name,
                            channel_label=label,
                        )
                    )

            if has_attachments:
                attachments_dir.mkdir(parents=True, exist_ok=True)

        return tasks

    def download(
        self, tasks: list[DownloadTask]
    ) -> tuple[DownloadStats, dict[str, ChannelDownloadStats]]:
        stats = DownloadStats()
        channel_stats: dict[str, ChannelDownloadStats] = {}
        lock = Lock()

        for task in tasks:
            if task.channel_label not in channel_stats:
                channel_stats[task.channel_label] = ChannelDownloadStats(
                    label=task.channel_label
                )
            channel_stats[task.channel_label].total += 1

        if not tasks:
            return stats, channel_stats

        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = {
                    executor.submit(self._download_one, task, client): task
                    for task in tasks
                }

                for future in as_completed(futures):
                    task = futures[future]
                    result = future.result()

                    with lock:
                        setattr(stats, result, getattr(stats, result) + 1)
                        cs = channel_stats[task.channel_label]
                        setattr(cs, result, getattr(cs, result) + 1)

                    if self._on_progress:
                        self._on_progress(result, task.channel_label)

        return stats, channel_stats

    def _download_one(self, task: DownloadTask, client: httpx.Client) -> str:
        if task.filepath.exists():
            return "skipped"

        try:
            response = client.get(task.url)

            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", "5"))
                time.sleep(retry_after + 0.5)
                response = client.get(task.url)

            if response.status_code != 200:
                return "failed"

            task.filepath.write_bytes(response.content)
            return "downloaded"

        except (httpx.TimeoutException, httpx.ConnectError):
            return "failed"
