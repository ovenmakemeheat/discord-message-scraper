from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from ..services.downloader import ChannelDownloadStats, DownloadStats
from ..services.scraper import ChannelResult
from .console import console


def scrape_summary(results: list[ChannelResult], duration: float) -> None:
    table = Table(show_lines=False)
    table.add_column("Channel", style="cyan")
    table.add_column("New", justify="right", style="green")
    table.add_column("Total", justify="right", style="blue")
    table.add_column("Status", justify="right")

    total_new = 0
    total_all = 0

    for r in results:
        label = f"{r.guild.slug}/{r.channel.slug}" if not r.skipped else r.channel.id
        if r.error:
            status = f"[red]{r.error}[/red]"
        elif r.skipped:
            status = "[yellow]skipped[/yellow]"
        else:
            status = "[green]ok[/green]"

        table.add_row(
            label,
            str(r.messages_fetched),
            str(r.total_messages),
            status,
        )
        total_new += r.messages_fetched
        total_all += r.total_messages

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total_new}[/bold]",
        f"[bold]{total_all}[/bold]",
        "",
    )

    console.print()
    console.print(Panel(table, title="Scrape Summary", border_style="blue"))
    console.print(f"  Duration: {_fmt_duration(duration)}")
    console.print()


def download_summary(
    stats: DownloadStats,
    channel_stats: dict[str, ChannelDownloadStats],
    duration: float,
) -> None:
    table = Table(show_lines=False)
    table.add_column("Channel", style="cyan")
    table.add_column("Downloaded", justify="right", style="green")
    table.add_column("Skipped", justify="right", style="yellow")
    table.add_column("Failed", justify="right", style="red")

    for cs in channel_stats.values():
        if cs.total == 0:
            continue
        table.add_row(cs.label, str(cs.downloaded), str(cs.skipped), str(cs.failed))

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{stats.downloaded}[/bold]",
        f"[bold]{stats.skipped}[/bold]",
        f"[bold]{stats.failed}[/bold]",
    )

    console.print()
    console.print(Panel(table, title="Download Summary", border_style="blue"))
    console.print(f"  Duration: {_fmt_duration(duration)}")
    console.print()


def export_summary(results: list[tuple[str, int, str]], duration: float) -> None:
    table = Table(show_lines=False)
    table.add_column("File", style="cyan")
    table.add_column("Messages", justify="right", style="green")
    table.add_column("Output", style="dim")

    total = 0
    for label, count, output in results:
        table.add_row(label, str(count), output)
        total += count

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "")

    console.print()
    console.print(Panel(table, title="Export Summary", border_style="blue"))
    console.print(f"  Duration: {_fmt_duration(duration)}")
    console.print()


def pipeline_status(
    scrape_done: bool,
    download_done: bool,
    export_done: bool,
    scrape_info: str = "",
    download_info: str = "",
    export_info: str = "",
) -> None:
    def icon(done: bool) -> str:
        return "[green]done[/green]" if done else "[dim]waiting[/dim]"

    table = Table(show_header=False, show_lines=False, box=None)
    table.add_column("Stage", style="bold")
    table.add_column("Status")
    table.add_column("Info", style="dim")

    table.add_row("Scrape", icon(scrape_done), scrape_info)
    table.add_row("Download", icon(download_done), download_info)
    table.add_row("Export", icon(export_done), export_info)

    console.print()
    console.print(Panel(table, title="Pipeline", border_style="blue"))
    console.print()


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"
