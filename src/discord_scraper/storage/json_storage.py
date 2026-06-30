from __future__ import annotations

import json
from pathlib import Path

from ..core.models import Channel, Guild, Message, ScrapeMeta
from .base import StorageBackend

META_FILENAME = ".scrape-meta.json"
MESSAGES_FILENAME = "messages.json"


class JSONStorage(StorageBackend):
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def channel_dir(self, guild: Guild, channel: Channel) -> Path:
        return self._data_dir / guild.slug / channel.slug

    def load_messages(self, guild: Guild, channel: Channel) -> list[Message]:
        raw = self.load_raw_messages(guild, channel)
        return [Message.from_api(m) for m in raw]

    def save_messages(
        self, guild: Guild, channel: Channel, messages: list[Message]
    ) -> Path:
        raw = [m.raw for m in messages]
        return self.save_raw_messages(guild, channel, raw)

    def load_raw_messages(self, guild: Guild, channel: Channel) -> list[dict]:
        path = self.channel_dir(guild, channel) / MESSAGES_FILENAME
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_raw_messages(
        self, guild: Guild, channel: Channel, messages: list[dict]
    ) -> Path:
        directory = self.channel_dir(guild, channel)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / MESSAGES_FILENAME
        messages.sort(key=lambda m: m["timestamp"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        return path

    def get_metadata(self, guild: Guild, channel: Channel) -> ScrapeMeta | None:
        path = self.channel_dir(guild, channel) / META_FILENAME
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ScrapeMeta(**data)

    def save_metadata(
        self, guild: Guild, channel: Channel, meta: ScrapeMeta
    ) -> None:
        directory = self.channel_dir(guild, channel)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / META_FILENAME
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "last_scraped": meta.last_scraped,
                    "newest_message_id": meta.newest_message_id,
                    "oldest_message_id": meta.oldest_message_id,
                    "total_messages": meta.total_messages,
                },
                f,
                indent=2,
            )

    def find_all_message_files(self) -> list[Path]:
        return sorted(self._data_dir.glob(f"**/{MESSAGES_FILENAME}"))
