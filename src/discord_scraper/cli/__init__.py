from __future__ import annotations

import click

from .commands import config_cmd, download, export, run, scrape


@click.group()
@click.version_option(package_name="discord-scraper")
def app() -> None:
    """Discord message scraper — fetch, download, and export."""


app.add_command(scrape.scrape)
app.add_command(download.download)
app.add_command(export.export)
app.add_command(run.run)
app.add_command(config_cmd.config)
