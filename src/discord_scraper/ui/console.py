from __future__ import annotations

from rich.console import Console

console = Console()


def error(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")


def warn(msg: str) -> None:
    console.print(f"[bold yellow]Warning:[/bold yellow] {msg}")


def success(msg: str) -> None:
    console.print(f"[bold green]Done:[/bold green] {msg}")


def info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")
