from __future__ import annotations

import sys
import time

import click

from ...core.config import Config
from ...core.models import Message
from ...services.exporter import EXPORTERS, get_exporter
from ...storage.json_storage import JSONStorage
from ...ui import console as ui
from ...ui.tables import export_summary


@click.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(list(EXPORTERS.keys())),
    default=None,
    help="Export format (default: from config or csv).",
)
@click.option("--quiet", is_flag=True, help="Suppress output except errors.")
def export(fmt: str | None, quiet: bool) -> None:
    """Export scraped messages to CSV or other formats."""
    config = Config.load()
    storage = JSONStorage(config.resolve_data_dir())

    message_files = storage.find_all_message_files()
    if not message_files:
        ui.error(f"No messages.json files found in {config.data_dir}. Run scrape first.")
        sys.exit(1)

    format_name = fmt or config.export_format
    exporter = get_exporter(format_name)

    start = time.time()
    results: list[tuple[str, int, str]] = []

    for json_path in message_files:
        channel_dir = json_path.parent
        label = f"{channel_dir.parent.name}/{channel_dir.name}"

        messages = [Message.from_api(m) for m in _load_json(json_path)]
        output_path = json_path.with_suffix(exporter.extension)
        exporter.export(messages, output_path)
        results.append((label, len(messages), str(output_path)))

    if not quiet:
        export_summary(results, time.time() - start)


def _load_json(path) -> list[dict]:
    import json

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
