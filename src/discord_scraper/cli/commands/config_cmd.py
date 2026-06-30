from __future__ import annotations

import sys
from pathlib import Path

import click

from ...core.config import CONFIG_FILENAME, Config
from ...ui import console as ui


@click.group()
def config() -> None:
    """Manage scraper configuration."""


@config.command()
def init() -> None:
    """Create a config.toml from template."""
    path = Path.cwd() / CONFIG_FILENAME
    if path.exists():
        ui.warn(f"{CONFIG_FILENAME} already exists. Delete it first to re-initialize.")
        return
    Config.init_config()
    ui.success(f"Created {path}")


@config.command()
def show() -> None:
    """Show resolved configuration."""
    cfg = Config.load()
    ui.console.print(f"[bold]Token:[/bold]       {'***' + cfg.token[-4:] if len(cfg.token) > 4 else '(not set)'}")
    ui.console.print(f"[bold]Data dir:[/bold]    {cfg.data_dir}")
    ui.console.print(f"[bold]Workers:[/bold]     {cfg.max_workers}")
    ui.console.print(f"[bold]Timeout:[/bold]     {cfg.download_timeout}s")
    ui.console.print(f"[bold]Format:[/bold]      {cfg.export_format}")
    ui.console.print(f"[bold]Channels:[/bold]    {len(cfg.channels)}")
    for ch in cfg.channels:
        ui.console.print(f"  - {ch}")


@config.command("add-channel")
@click.argument("channel_id")
def add_channel(channel_id: str) -> None:
    """Add a channel ID to config."""
    path = Path.cwd() / CONFIG_FILENAME
    if not path.exists():
        ui.error(f"{CONFIG_FILENAME} not found. Run 'discord-scraper config init' first.")
        sys.exit(1)

    cfg = Config.load()
    if channel_id in cfg.channels:
        ui.warn(f"Channel {channel_id} already in config.")
        return

    cfg.channels.append(channel_id)
    _write_channels(path, cfg.channels)
    ui.success(f"Added channel {channel_id}")


@config.command("rm-channel")
@click.argument("channel_id")
def rm_channel(channel_id: str) -> None:
    """Remove a channel ID from config."""
    path = Path.cwd() / CONFIG_FILENAME
    if not path.exists():
        ui.error(f"{CONFIG_FILENAME} not found.")
        sys.exit(1)

    cfg = Config.load()
    if channel_id not in cfg.channels:
        ui.warn(f"Channel {channel_id} not in config.")
        return

    cfg.channels.remove(channel_id)
    _write_channels(path, cfg.channels)
    ui.success(f"Removed channel {channel_id}")


def _write_channels(path: Path, channels: list[str]) -> None:
    """Rewrite config.toml preserving structure but updating channels list."""
    import tomllib

    with open(path, "rb") as f:
        data = tomllib.load(f)

    data.setdefault("scraper", {})["channels"] = channels

    lines = []
    for section_name, section in data.items():
        lines.append(f"[{section_name}]")
        for key, value in section.items():
            if isinstance(value, list):
                items = ", ".join(f'"{v}"' for v in value)
                lines.append(f"{key} = [{items}]")
            elif isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, (int, float)):
                lines.append(f"{key} = {value}")
            elif isinstance(value, bool):
                lines.append(f"{key} = {'true' if value else 'false'}")
        lines.append("")

    path.write_text("\n".join(lines))
