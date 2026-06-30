from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..core.models import Channel, Guild, Message, ScrapeMeta


class StorageBackend(ABC):
    @abstractmethod
    def channel_dir(self, guild: Guild, channel: Channel) -> Path: ...

    @abstractmethod
    def load_messages(self, guild: Guild, channel: Channel) -> list[Message]: ...

    @abstractmethod
    def save_messages(
        self, guild: Guild, channel: Channel, messages: list[Message]
    ) -> Path: ...

    @abstractmethod
    def load_raw_messages(self, guild: Guild, channel: Channel) -> list[dict]: ...

    @abstractmethod
    def save_raw_messages(
        self, guild: Guild, channel: Channel, messages: list[dict]
    ) -> Path: ...

    @abstractmethod
    def get_metadata(self, guild: Guild, channel: Channel) -> ScrapeMeta | None: ...

    @abstractmethod
    def save_metadata(
        self, guild: Guild, channel: Channel, meta: ScrapeMeta
    ) -> None: ...

    @abstractmethod
    def find_all_message_files(self) -> list[Path]: ...
