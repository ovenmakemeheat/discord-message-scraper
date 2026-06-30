from __future__ import annotations

import sys
import time

import click

from ...core.client import AuthenticationError, DiscordClient
from ...core.config import Config
from ...core.rate_limiter import RateLimiter
from ...services.downloader import DownloaderService
from ...services.exporter import get_exporter
from ...services.scraper import ScraperService
from ...storage.json_storage import JSONStorage
from ...ui import console as ui
from ...ui.tables import pipeline_status, scrape_summary, download_summary, export_summary
from ...core.models import Message


@click.command()
@click.option(
    "--channel",
    "channels",
    multiple=True,
    help="Channel ID to scrape (repeatable).",
)
@click.option("--full", is_flag=True, help="Force full re-scrape.")
@click.option("--limit", type=int, default=None, help="Max messages per channel.")
@click.option("--skip-download", is_flag=True, help="Skip attachment downloads.")
@click.option("--skip-export", is_flag=True, help="Skip CSV export.")
@click.option("--quiet", is_flag=True, help="Suppress output except errors.")
def run(
    channels: tuple[str, ...],
    full: bool,
    limit: int | None,
    skip_download: bool,
    skip_export: bool,
    quiet: bool,
) -> None:
    """Full pipeline: scrape -> download -> export."""
    config = Config.load()

    if not config.token:
        ui.error(
            "DISCORD_TOKEN not set. Copy .env.example to .env and fill in your token."
        )
        sys.exit(1)

    channel_ids = list(channels) if channels else config.channels
    if not channel_ids:
        ui.error(
            "No channels configured. Use --channel or add channels to config.toml."
        )
        sys.exit(1)

    storage = JSONStorage(config.resolve_data_dir())
    total_start = time.time()

    # --- Stage 1: Scrape ---
    if not quiet:
        ui.console.print("\n[bold blue]Stage 1/3:[/bold blue] Scraping messages...")

    rate_limiter = RateLimiter()
    scrape_results = []
    start = time.time()

    with DiscordClient(config.token, rate_limiter) as client:
        for channel_id in channel_ids:
            service = ScraperService(client, storage)
            try:
                result = service.scrape_channel(channel_id, full=full, limit=limit)
            except AuthenticationError as e:
                ui.error(str(e))
                sys.exit(1)
            scrape_results.append(result)
            if not quiet:
                status = "skipped" if result.skipped else f"{result.messages_fetched} new"
                name = result.channel.name if not result.skipped else channel_id
                ui.console.print(f"  #{name}: {status}")

    if not quiet:
        scrape_summary(scrape_results, time.time() - start)

    # --- Stage 2: Download ---
    if not skip_download:
        if not quiet:
            ui.console.print("[bold blue]Stage 2/3:[/bold blue] Downloading attachments...")

        start = time.time()
        downloader = DownloaderService(
            max_workers=config.max_workers,
            timeout=config.download_timeout,
        )
        message_files = storage.find_all_message_files()
        tasks = downloader.collect_tasks(message_files)

        if tasks:
            dl_stats, dl_channel_stats = downloader.download(tasks)
            if not quiet:
                download_summary(dl_stats, dl_channel_stats, time.time() - start)
        elif not quiet:
            ui.info("No attachments to download.")
    elif not quiet:
        ui.info("Skipping downloads.")

    # --- Stage 3: Export ---
    if not skip_export:
        if not quiet:
            ui.console.print("[bold blue]Stage 3/3:[/bold blue] Exporting...")

        start = time.time()
        exporter = get_exporter(config.export_format)
        message_files = storage.find_all_message_files()
        export_results: list[tuple[str, int, str]] = []

        for json_path in message_files:
            import json

            channel_dir = json_path.parent
            label = f"{channel_dir.parent.name}/{channel_dir.name}"
            with open(json_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            messages = [Message.from_api(m) for m in raw]
            output_path = json_path.with_suffix(exporter.extension)
            exporter.export(messages, output_path)
            export_results.append((label, len(messages), str(output_path)))

        if not quiet:
            export_summary(export_results, time.time() - start)
    elif not quiet:
        ui.info("Skipping export.")

    if not quiet:
        total_duration = time.time() - total_start
        total_msgs = sum(r.total_messages for r in scrape_results)
        ui.console.print(
            f"\n[bold green]Pipeline complete.[/bold green] "
            f"{total_msgs} messages across {len(channel_ids)} channels "
            f"in {total_duration:.1f}s\n"
        )
