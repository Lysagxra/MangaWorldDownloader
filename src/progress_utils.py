from rich.console import Console
from rich.prompt import Prompt

from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

"""Utility functions for tracking download progress using the Rich library.

It includes features for creating a progress bar and a formatted progress table
specifically designed for monitoring the download status of the current taks.
"""

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

def create_select_items_list(items: list[str], title: str = "Please select volume(s) to download") -> list[int]:
    """
    Shows a numbered list of items with Rich and allows the user to select one or more indices.
    Returns the list of selected indices (0-based).
    """
    console = Console()
    console.print(f"\n[bold]{title}[/bold]")
    for idx, _ in enumerate(items):
        console.print(f"  [cyan][{idx+1}][/cyan]")
    prompt_text = "\nEnter the numbers separated by comma (e.g. 1,3,5) or 'all' for all:"
    choice = Prompt.ask(prompt_text, default="all")
    if choice.strip().lower() == 'all':
        return list(range(len(items)))
    try:
        indices = [int(x.strip())-1 for x in choice.split(',') if x.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < len(items)]
        return indices
    except Exception:
        console.print("[red]Invalid selection.[/red]")
        return []