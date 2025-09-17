"""Utilities for handling file downloads with progress tracking."""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from requests import Response
from rich.progress import Progress

from .config import (
    CHUNK_SIZE,
    HEADERS,
    HTTP_STATUS_OK,
    MAX_WORKERS,
    PAGE_EXTENSIONS,
    SESSION,
    SESSION_LOG,
    TASK_COLOR,
    TIMEOUT,
)
from .file_utils import create_download_directory, write_file


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
            task_info = job_progress, task, overall_task
            item_info = indx, item
            future = executor.submit(func, item_info, *args, task_info)
            futures[future] = task
            manage_running_tasks(futures, job_progress)


def download_page(
    response: Response,
    page: int,
    extension: str,
    download_path: str,
) -> None:
    """Download a single page of a chapter."""
    filename = f"{page}{extension}"
    final_path = Path(download_path) / filename

    try:
        with Path(final_path).open("wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk is not None:
                    file.write(chunk)

    except requests.exceptions.RequestException as req_err:
        log_message = f"Failed to download page {page}: {req_err}"
        logging.warning(log_message)
        write_file(SESSION_LOG, mode="a", content=log_message)


def attempt_download_page(
    page: int,
    base_download_link: str,
    download_path: str,
) -> bool:
    """Attempt downloading a page by testing all possible extensions.

    Returns True if download succeeded, False otherwise.
    """
    for extension in PAGE_EXTENSIONS:
        test_download_link = f"{base_download_link}{page}{extension}"

        try:
            response = SESSION.get(
                test_download_link,
                stream=True,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if response.status_code == HTTP_STATUS_OK:
                download_page(
                    response,
                    page,
                    extension,
                    download_path,
                )
                return True

        except requests.exceptions.RequestException as req_err:
            log_message = f"Failed attempt with {test_download_link}: {req_err}"
            logging.warning(log_message)
            continue

    # Every possible extension failed
    return False


def download_chapter(
    item_info: tuple,
    pages_per_chapter: list[str],
    manga_name: str,
    task_info: tuple,
) -> None:
    """Download all pages for a specific manga chapter and updates the progress."""
    job_progress, task, overall_task = task_info
    indx_chapter, base_download_link = item_info

    download_path = create_download_directory(manga_name, indx_chapter)
    num_pages = int(pages_per_chapter[indx_chapter])

    for page in range(1, num_pages + 1):
        success = attempt_download_page(page, base_download_link, download_path)
        if not success:
            log_message = f"Page {page} could not be downloaded with any extension."
            logging.error(log_message)

        progress_percentage = (page / num_pages) * 100
        job_progress.update(task, completed=progress_percentage)

    job_progress.update(task, completed=100, visible=False)
    job_progress.advance(overall_task)
