from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path

from ..core.models import Message


class Exporter(ABC):
    @property
    @abstractmethod
    def extension(self) -> str: ...

    @abstractmethod
    def export(self, messages: list[Message], output_path: Path) -> None: ...


class CSVExporter(Exporter):
    FIELDNAMES = [
        "id",
        "timestamp",
        "edited_timestamp",
        "author_id",
        "author_username",
        "author_display_name",
        "content",
        "type",
        "pinned",
        "attachments",
        "embeds_count",
        "mention_everyone",
        "mentions",
        "referenced_message_id",
    ]

    @property
    def extension(self) -> str:
        return ".csv"

    def export(self, messages: list[Message], output_path: Path) -> None:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()

            for msg in messages:
                raw = msg.raw
                author = raw.get("author", {})
                attachments = raw.get("attachments", [])
                attachment_urls = ", ".join(a.get("url", "") for a in attachments)
                mention_list = raw.get("mentions", [])
                mention_names = ", ".join(
                    m.get("username", "") for m in mention_list
                )
                ref = raw.get("referenced_message")

                writer.writerow(
                    {
                        "id": msg.id,
                        "timestamp": msg.timestamp,
                        "edited_timestamp": raw.get("edited_timestamp", ""),
                        "author_id": msg.author_id,
                        "author_username": msg.author_username,
                        "author_display_name": msg.author_display_name,
                        "content": msg.content,
                        "type": msg.type,
                        "pinned": msg.pinned,
                        "attachments": attachment_urls,
                        "embeds_count": msg.embeds_count,
                        "mention_everyone": raw.get("mention_everyone", False),
                        "mentions": mention_names,
                        "referenced_message_id": msg.referenced_message_id or "",
                    }
                )


class JSONLExporter(Exporter):
    @property
    def extension(self) -> str:
        return ".jsonl"

    def export(self, messages: list[Message], output_path: Path) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg.raw, ensure_ascii=False) + "\n")


EXPORTERS: dict[str, type[Exporter]] = {
    "csv": CSVExporter,
    "jsonl": JSONLExporter,
}


def get_exporter(format: str) -> Exporter:
    cls = EXPORTERS.get(format)
    if cls is None:
        raise ValueError(f"Unknown format: {format}. Available: {', '.join(EXPORTERS)}")
    return cls()
