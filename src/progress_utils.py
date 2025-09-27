"""Utility functions for tracking download progress using the Rich library.

It includes features for creating a progress bar and a formatted progress table
specifically designed for monitoring the download status of the current taks.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.prompt import Prompt
from rich.table import Table


def create_progress_bar() -> Progress:
    """Create a progress bar for tracking download progress."""
    return Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        "•",
        TimeRemainingColumn(),
    )


def create_progress_table(title: str, job_progress: Progress) -> Table:
    """Create a formatted progress table for tracking the download status."""
    progress_table = Table.grid()
    progress_table.add_row(
        Panel.fit(
            job_progress,
            title=f"[b]{title}",
            border_style="red",
            padding=(1, 1),
        ),
    )
    return progress_table


def create_select_items_list(items: list[str]) -> list[int]:
    """Show a numbered list of items and allow the user to select one or more indexes.

    Return the list of selected 0-based indexes

    If there are more than 15 volumes,
        return the list in a compact format like this:
        [1] Volume 01
        ...
        [15] Volume 05
    """
    console = Console()
    console.print("[bold]Please select volume(s) to download[/bold]")

    # compact list format
    if len(items) > 15:
        console.print(f"[cyan][1][/cyan] {items[0]}\n...\n[cyan][{len(items)}][/cyan] {items[-1]}")
    else:
        for indx, item in enumerate(items):
            console.print(f"[cyan][{indx + 1}][/cyan] {item}")

    prompt_text = "Enter the numbers separated by commas (e.g. 1,3,5) or 'all' for all:"
    choice = Prompt.ask(f"\n{prompt_text}", default="all")

    if choice.strip().lower() == "all":
        return list(range(len(items)))

    # Parse user input safely without raising exceptions
    raw_indexes = [int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()]
    valid_indexes = [indx for indx in raw_indexes if 0 <= indx < len(items)]

    if not valid_indexes:
        console.print("[red]No valid selections made.[/red]")

    return valid_indexes
