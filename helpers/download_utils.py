"""
This module provides utilities for handling file downloads with progress
tracking and concurrent execution.
"""

from concurrent.futures import ThreadPoolExecutor

MAX_WORKERS = 5
TASK_COLOR = 'cyan'

def manage_running_tasks(futures, job_progress):
    """
    Manage the status of running tasks and update their progress.

    Args:
        futures (dict): A dictionary where keys are futures representing the
                        tasks that have been submitted for execution, and
                        values are the associated task identifiers in the
                        job progress tracking system.
        job_progress: An object responsible for tracking the progress of tasks,
                      providing methods to update and manage task visibility.
    """
    while futures:
        for future in list(futures.keys()):
            if future.running():
                task = futures.pop(future)
                job_progress.update(task, visible=True)

def run_in_parallel(func, items, job_progress, *args):
    """
    Execute a function in parallel for a list of items, updating progress in a
    job tracker.

    Args:
        func (callable): The function to be executed for each item in the
                         `items` list.
        items (iterable): A list of items to be processed by the `func`.
        job_progress: An object responsible for managing and displaying the
                      progress of tasks.
        *args: Additional positional arguments to be passed to the `func`.
    """
    num_items = len(items)
    futures = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        overall_task = job_progress.add_task(
            f"[{TASK_COLOR}]Progress", total=num_items, visible=True
        )

        for indx, item in enumerate(items):
            task = job_progress.add_task(
                f"[{TASK_COLOR}]Chapter {indx + 1}/{num_items}",
                total=100, visible=False
            )
            task_info = (job_progress, task, overall_task)
            item_info = (indx, item)
            future = executor.submit(func, item_info, *args, task_info)
            futures[future] = task
            manage_running_tasks(futures, job_progress)
