from __future__ import annotations

import sys
import time

import click

from ...core.client import AuthenticationError, DiscordClient
from ...core.config import Config
from ...core.rate_limiter import RateLimiter
from ...services.scraper import ScraperService
from ...storage.json_storage import JSONStorage
from ...ui import console as ui
from ...ui.progress import scrape_progress
from ...ui.tables import scrape_summary


@click.command()
@click.option(
    "--channel",
    "channels",
    multiple=True,
    help="Channel ID to scrape (repeatable, overrides config).",
)
@click.option("--full", is_flag=True, help="Force full re-scrape.")
@click.option("--limit", type=int, default=None, help="Max messages per channel.")
@click.option("--quiet", is_flag=True, help="Suppress output except errors.")
def scrape(
    channels: tuple[str, ...],
    full: bool,
    limit: int | None,
    quiet: bool,
) -> None:
    """Fetch messages from configured Discord channels."""
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
    rate_limiter = RateLimiter()
    results = []
    start = time.time()

    with DiscordClient(config.token, rate_limiter) as client:
        progress = scrape_progress()

        with progress:
            for channel_id in channel_ids:
                task = progress.add_task(
                    f"#{channel_id}", count="0"
                )

                def on_progress(count: int) -> None:
                    progress.update(task, count=str(count))

                service = ScraperService(
                    client, storage, on_progress=on_progress
                )

                try:
                    result = service.scrape_channel(
                        channel_id, full=full, limit=limit
                    )
                except AuthenticationError as e:
                    ui.error(str(e))
                    sys.exit(1)

                if result.channel.name != channel_id:
                    progress.update(
                        task, description=f"#{result.channel.name}"
                    )
                progress.update(
                    task, count=str(result.total_messages), completed=True
                )
                progress.remove_task(task)
                results.append(result)

    if not quiet:
        scrape_summary(results, time.time() - start)

    return results  # type: ignore[return-value]
