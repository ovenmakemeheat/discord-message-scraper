import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob
from threading import Lock

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tqdm import tqdm

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ATTACHMENTS_DIRNAME = "attachments"
MAX_WORKERS = 8

console = Console()
stats_lock = Lock()


def download_one(
    url: str, filepath: str, client: httpx.Client
) -> str:
    """Download a single file. Returns 'downloaded', 'skipped', or 'failed'."""
    if os.path.exists(filepath):
        return "skipped"

    try:
        response = client.get(url)

        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "5"))
            time.sleep(retry_after + 0.5)
            response = client.get(url)

        if response.status_code != 200:
            return "failed"

        with open(filepath, "wb") as f:
            f.write(response.content)

        return "downloaded"

    except (httpx.TimeoutException, httpx.ConnectError):
        return "failed"


def collect_attachments(json_path: str) -> list[tuple[str, str]]:
    """Collect all (url, filepath) pairs from a messages.json file."""
    with open(json_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    channel_dir = os.path.dirname(json_path)
    attachments_dir = os.path.join(channel_dir, ATTACHMENTS_DIRNAME)

    items = []
    for msg in messages:
        for att in msg.get("attachments", []):
            att_id = att["id"]
            filename = att.get("filename", att_id)
            safe_name = f"{att_id}_{filename}"
            items.append((att["url"], os.path.join(attachments_dir, safe_name)))

    if items:
        os.makedirs(attachments_dir, exist_ok=True)

    return items


def main():
    json_files = glob(os.path.join(DATA_DIR, "**", "messages.json"), recursive=True)

    if not json_files:
        console.print(
            f"[red]Error:[/red] No messages.json files found in {DATA_DIR}/. Run main.py first."
        )
        sys.exit(1)

    # Collect all attachments across all channels
    channel_stats = {}
    all_tasks = []

    for json_path in sorted(json_files):
        channel_dir = os.path.dirname(json_path)
        channel_name = os.path.join(*channel_dir.split(os.sep)[-2:])
        items = collect_attachments(json_path)
        channel_stats[channel_name] = {"total": len(items), "downloaded": 0, "skipped": 0, "failed": 0}
        for url, filepath in items:
            all_tasks.append((url, filepath, channel_name))

    # Summary table
    summary = Table(title="Channels", show_lines=False)
    summary.add_column("Channel", style="cyan")
    summary.add_column("Attachments", justify="right", style="green")
    for name, stats in channel_stats.items():
        summary.add_row(name, str(stats["total"]))
    summary.add_section()
    summary.add_row("[bold]Total[/bold]", f"[bold]{len(all_tasks)}[/bold]")
    console.print(Panel(summary, title="Attachment Downloader", border_style="blue"))

    if not all_tasks:
        console.print("[yellow]No attachments to download.[/yellow]")
        return

    console.print(f"\nDownloading with [bold]{MAX_WORKERS}[/bold] threads...\n")

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        with tqdm(total=len(all_tasks), unit="file", ncols=80, colour="green") as pbar:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(download_one, url, filepath, client): channel_name
                    for url, filepath, channel_name in all_tasks
                }

                for future in as_completed(futures):
                    channel_name = futures[future]
                    result = future.result()
                    with stats_lock:
                        channel_stats[channel_name][result] += 1
                    pbar.update(1)

    # Results table
    console.print()
    results = Table(title="Results", show_lines=False)
    results.add_column("Channel", style="cyan")
    results.add_column("Downloaded", justify="right", style="green")
    results.add_column("Skipped", justify="right", style="yellow")
    results.add_column("Failed", justify="right", style="red")

    totals = {"downloaded": 0, "skipped": 0, "failed": 0}
    for name, stats in channel_stats.items():
        if stats["total"] == 0:
            continue
        results.add_row(name, str(stats["downloaded"]), str(stats["skipped"]), str(stats["failed"]))
        for k in totals:
            totals[k] += stats[k]

    results.add_section()
    results.add_row(
        "[bold]Total[/bold]",
        f"[bold]{totals['downloaded']}[/bold]",
        f"[bold]{totals['skipped']}[/bold]",
        f"[bold]{totals['failed']}[/bold]",
    )
    console.print(Panel(results, border_style="blue"))


if __name__ == "__main__":
    main()
