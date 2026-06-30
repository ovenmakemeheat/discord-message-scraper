from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

CONFIG_FILENAME = "config.toml"
DEFAULT_DATA_DIR = "data"
DEFAULT_MAX_WORKERS = 8
DEFAULT_TIMEOUT = 60
DEFAULT_EXPORT_FORMAT = "csv"

CONFIG_TEMPLATE = """\
[scraper]
channels = []
data_dir = "data"

[downloader]
max_workers = 8
timeout = 60

[export]
default_format = "csv"
"""


@dataclass
class Config:
    channels: list[str] = field(default_factory=list)
    data_dir: Path = field(default_factory=lambda: Path(DEFAULT_DATA_DIR))
    max_workers: int = DEFAULT_MAX_WORKERS
    download_timeout: int = DEFAULT_TIMEOUT
    export_format: str = DEFAULT_EXPORT_FORMAT
    token: str = ""

    @classmethod
    def load(cls, project_root: Path | None = None) -> Config:
        if project_root is None:
            project_root = Path.cwd()

        load_dotenv(project_root / ".env")

        config = cls()
        config_path = project_root / CONFIG_FILENAME

        if config_path.exists():
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

            scraper = data.get("scraper", {})
            config.channels = scraper.get("channels", [])
            if "data_dir" in scraper:
                config.data_dir = project_root / scraper["data_dir"]
            else:
                config.data_dir = project_root / DEFAULT_DATA_DIR

            downloader = data.get("downloader", {})
            config.max_workers = downloader.get("max_workers", DEFAULT_MAX_WORKERS)
            config.download_timeout = downloader.get("timeout", DEFAULT_TIMEOUT)

            export = data.get("export", {})
            config.export_format = export.get("default_format", DEFAULT_EXPORT_FORMAT)
        else:
            config.data_dir = project_root / DEFAULT_DATA_DIR

        config.token = os.getenv("DISCORD_TOKEN", "")

        return config

    @staticmethod
    def init_config(project_root: Path | None = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        path = project_root / CONFIG_FILENAME
        path.write_text(CONFIG_TEMPLATE)
        return path

    def resolve_data_dir(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir
