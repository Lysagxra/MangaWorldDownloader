"""Utilities for handling file downloads with progress tracking."""

from concurrent.futures import ThreadPoolExecutor

from rich.progress import Progress

from .config import (
    MAX_WORKERS,
    TASK_COLOR,
)


def manage_running_tasks(futures: dict, job_progress: Progress) -> None:
    """Manage the status of running tasks and update their progress."""
    while futures:
        for future in list(futures.keys()):
            if future.running():
                task = futures.pop(future)
                job_progress.update(task, visible=True)


def run_in_parallel(
    func: callable,
    items: list,
    job_progress: Progress,
    *args: tuple,
) -> None:
    """Execute a function in parallel for a list of items, updating progress."""
    num_items = len(items)
    futures = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        overall_task = job_progress.add_task(
            f"[{TASK_COLOR}]Progress",
            total=num_items,
            visible=True,
        )

        for indx, item in enumerate(items):
            task = job_progress.add_task(
                f"[{TASK_COLOR}]Chapter {indx + 1}/{num_items}",
                total=100,
                visible=False,
            )
            task_info = (job_progress, task, overall_task)
            item_info = (indx, item)
            future = executor.submit(func, item_info, *args, task_info)
            futures[future] = task
            manage_running_tasks(futures, job_progress)
