from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from ..core.client import AccessDeniedError, DiscordClient
from ..core.models import Channel, Guild, Message, ScrapeMeta
from ..storage.base import StorageBackend


@dataclass
class ChannelResult:
    guild: Guild
    channel: Channel
    messages_fetched: int
    total_messages: int
    output_path: str
    skipped: bool = False
    error: str | None = None


class ScraperService:
    def __init__(
        self,
        client: DiscordClient,
        storage: StorageBackend,
        *,
        on_progress: Callable[[int], None] | None = None,
    ) -> None:
        self._client = client
        self._storage = storage
        self._on_progress = on_progress

    def scrape_channel(
        self,
        channel_id: str,
        *,
        full: bool = False,
        limit: int | None = None,
    ) -> ChannelResult:
        channel = self._client.get_channel(channel_id)
        guild = self._client.get_guild(channel.guild_id)

        after_id: str | None = None
        existing_raw: list[dict] = []

        if not full:
            meta = self._storage.get_metadata(guild, channel)
            if meta and meta.newest_message_id:
                after_id = meta.newest_message_id
                existing_raw = self._storage.load_raw_messages(guild, channel)

        try:
            new_raw = self._fetch_all(
                channel.id, after=after_id, limit=limit
            )
        except AccessDeniedError:
            return ChannelResult(
                guild=guild,
                channel=channel,
                messages_fetched=0,
                total_messages=0,
                output_path="",
                skipped=True,
                error=f"No access to #{channel.name}",
            )

        if not new_raw and not existing_raw:
            return ChannelResult(
                guild=guild,
                channel=channel,
                messages_fetched=0,
                total_messages=0,
                output_path="",
                skipped=True,
            )

        merged = self._merge(existing_raw, new_raw)
        path = self._storage.save_raw_messages(guild, channel, merged)

        ids = [m["id"] for m in merged]
        self._storage.save_metadata(
            guild,
            channel,
            ScrapeMeta(
                last_scraped=datetime.now(timezone.utc).isoformat(),
                newest_message_id=max(ids) if ids else None,
                oldest_message_id=min(ids) if ids else None,
                total_messages=len(merged),
            ),
        )

        return ChannelResult(
            guild=guild,
            channel=channel,
            messages_fetched=len(new_raw),
            total_messages=len(merged),
            output_path=str(path),
        )

    def _fetch_all(
        self,
        channel_id: str,
        *,
        after: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        all_messages: list[dict] = []
        before_id: str | None = None

        while True:
            if after:
                batch = self._client.get_messages(
                    channel_id, after=after
                )
                # Discord returns newest first with `after`, reverse to paginate
                batch.sort(key=lambda m: m["id"])
                if batch:
                    after = batch[-1]["id"]
            else:
                batch = self._client.get_messages(
                    channel_id, before=before_id
                )
                if batch:
                    before_id = batch[-1]["id"]

            if not batch:
                break

            all_messages.extend(batch)

            if self._on_progress:
                self._on_progress(len(all_messages))

            if limit and len(all_messages) >= limit:
                all_messages = all_messages[:limit]
                break

            if len(batch) < 100:
                break

            time.sleep(0.5)

        return all_messages

    @staticmethod
    def _merge(existing: list[dict], new: list[dict]) -> list[dict]:
        seen: dict[str, dict] = {m["id"]: m for m in existing}
        for m in new:
            seen[m["id"]] = m
        return list(seen.values())
