from __future__ import annotations

import sys
import time

import click

from ...core.config import Config
from ...services.downloader import DownloaderService
from ...storage.json_storage import JSONStorage
from ...ui import console as ui
from ...ui.progress import download_progress
from ...ui.tables import download_summary


@click.command()
@click.option("--workers", type=int, default=None, help="Thread count (default: 8).")
@click.option("--quiet", is_flag=True, help="Suppress output except errors.")
def download(workers: int | None, quiet: bool) -> None:
    """Download attachments from scraped messages."""
    config = Config.load()
    storage = JSONStorage(config.resolve_data_dir())

    message_files = storage.find_all_message_files()
    if not message_files:
        ui.error(f"No messages.json files found in {config.data_dir}. Run scrape first.")
        sys.exit(1)

    max_workers = workers or config.max_workers
    service = DownloaderService(
        max_workers=max_workers, timeout=config.download_timeout
    )
    tasks = service.collect_tasks(message_files)

    if not tasks:
        if not quiet:
            ui.info("No attachments to download.")
        return

    if not quiet:
        ui.console.print(
            f"Downloading [bold]{len(tasks)}[/bold] attachments "
            f"with [bold]{max_workers}[/bold] threads..."
        )

    start = time.time()
    progress = download_progress(len(tasks))

    with progress:
        task_id = progress.add_task("Downloading", total=len(tasks))

        def on_progress(result: str, channel: str) -> None:
            progress.advance(task_id)

        service._on_progress = on_progress
        stats, channel_stats = service.download(tasks)

    if not quiet:
        download_summary(stats, channel_stats, time.time() - start)
