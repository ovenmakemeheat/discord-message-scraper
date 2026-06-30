from __future__ import annotations

import re
from dataclasses import dataclass, field


def slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "-", name)
    return name


@dataclass(frozen=True)
class Guild:
    id: str
    name: str

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @classmethod
    def from_api(cls, data: dict) -> Guild:
        return cls(id=data["id"], name=data.get("name", data["id"]))

    @classmethod
    def unknown(cls, guild_id: str) -> Guild:
        return cls(id=guild_id, name=guild_id)


@dataclass(frozen=True)
class Channel:
    id: str
    name: str
    guild_id: str

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @classmethod
    def from_api(cls, data: dict) -> Channel:
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            guild_id=data.get("guild_id", "unknown"),
        )


@dataclass(frozen=True)
class Attachment:
    id: str
    url: str
    filename: str
    size: int = 0

    @classmethod
    def from_api(cls, data: dict) -> Attachment:
        return cls(
            id=data["id"],
            url=data["url"],
            filename=data.get("filename", data["id"]),
            size=data.get("size", 0),
        )


@dataclass(frozen=True)
class Message:
    id: str
    timestamp: str
    author_id: str
    author_username: str
    author_display_name: str
    content: str
    type: int
    pinned: bool
    attachments: tuple[Attachment, ...]
    embeds_count: int
    mentions: tuple[str, ...]
    referenced_message_id: str | None
    raw: dict = field(repr=False)

    @classmethod
    def from_api(cls, data: dict) -> Message:
        author = data.get("author", {})
        attachments = tuple(
            Attachment.from_api(a) for a in data.get("attachments", [])
        )
        mentions = tuple(m.get("username", "") for m in data.get("mentions", []))
        ref = data.get("referenced_message")
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            author_id=author.get("id", ""),
            author_username=author.get("username", ""),
            author_display_name=author.get("global_name", ""),
            content=data.get("content", ""),
            type=data.get("type", 0),
            pinned=data.get("pinned", False),
            attachments=attachments,
            embeds_count=len(data.get("embeds", [])),
            mentions=mentions,
            referenced_message_id=ref["id"] if ref else None,
            raw=data,
        )


@dataclass
class ScrapeMeta:
    last_scraped: str
    newest_message_id: str | None
    oldest_message_id: str | None
    total_messages: int
