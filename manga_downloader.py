"""A manga downloader and PDF generator for MangaWorld.

This module allows you to download manga chapters from a given manga URL,
process each chapter, and generate PDF files for the downloaded images.
It utilizes `requests` for HTTP requests, `BeautifulSoup` for HTML parsing,
and `rich` for displaying a progress bar during the download and conversion
process.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from requests import Response
from rich.live import Live

from helpers.config import (
    CHUNK_SIZE,
    DOWNLOAD_FOLDER,
    ERROR_LOG,
    HEADERS,
    HTTP_STATUS_OK,
    MAX_RETRIES,
    PAGE_EXTENSIONS,
    SESSION,
    TIMEOUT,
    WAIT_TIME_RETRIES,
)
from helpers.download_utils import run_in_parallel
from helpers.file_utils import write_file
from helpers.format_utils import extract_manga_info
from helpers.general_utils import (
    check_real_page,
    clear_terminal,
    create_download_directory,
    fetch_page,
    validate_chapter_range,
)
from helpers.pdf_generator import generate_pdf_files
from helpers.progress_utils import create_progress_bar, create_progress_table

if TYPE_CHECKING:
    from rich.progress import Progress


async def fetch_chapter_data(chapter_url: str, session: ClientSession) -> tuple:
    """Fetch the number of pages for a given chapter URL, retrying if necessary."""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(chapter_url, timeout=TIMEOUT) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                soup = await check_real_page(soup, session, TIMEOUT)

                page_item = soup.find("select", {"class": "page custom-select"})
                if page_item:
                    option_text = page_item.find("option").get_text()
                    num_pages = option_text.split("/")[-1]
                    return chapter_url, num_pages  # Page count found

        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass

        if attempt < MAX_RETRIES - 1:
            delay = random.uniform(1, WAIT_TIME_RETRIES - 1)  # noqa: S311
            await asyncio.sleep(delay)

    message = f"Failed to fetch chapter data for {chapter_url}."
    logging.error(message)
    return None, None


async def get_chapter_urls_and_pages(
    soup: BeautifulSoup,
    session: ClientSession,
    match: str = "/read/",
) -> tuple:
    """Extract chapter URLs and the corresponding number of pages."""
    chapter_items = soup.find_all("a", {"class": "chap", "title": True})
    tasks = []

    # Create a list of tasks only for chapters that contain the match
    for chapter_item in chapter_items:
        chapter_url = chapter_item["href"]
        if match in chapter_url:
            tasks.append(fetch_chapter_data(chapter_url, session))

    results = await asyncio.gather(*tasks)

    # Filter out None results (failed requests) and unpack results
    chapter_urls = []
    pages_per_chapter = []

    for result in results:
        if result[0]:
            chapter_urls.append(result[0])
            pages_per_chapter.append(result[1])

    # Return chapter URLs and pages, both in reverse order
    return chapter_urls[::-1], pages_per_chapter[::-1]


async def extract_chapters_info(soup: BeautifulSoup) -> tuple:
    """Extract chapter URLs and page numbers."""
    async with aiohttp.ClientSession() as session:
        chapter_urls, pages_per_chapter = await get_chapter_urls_and_pages(
            soup,
            session,
        )
        return chapter_urls, pages_per_chapter


async def fetch_download_link(chapter_url: str, session: ClientSession) -> str | None:
    """Fetch the download link for the first image in a chapter page."""
    for attempt in range(MAX_RETRIES):
        try:
            url_to_fetch = f"{chapter_url}/1"
            async with session.get(url_to_fetch, timeout=TIMEOUT) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                validated_soup = await check_real_page(soup, session, TIMEOUT)

                img_items = validated_soup.find_all("img", {"class": "img-fluid"})
                if img_items:
                    return img_items[-1]["src"]  # Download link found

        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass

        # Delay before retrying, but not after the last attempt
        if attempt < MAX_RETRIES - 1:
            delay = 1 + random.uniform(0, WAIT_TIME_RETRIES)  # noqa: S311
            await asyncio.sleep(delay)

    message = f"Failed to fetch download link for {chapter_url}."
    logging.error(message)
    return None


async def extract_download_links(
    chapter_urls: list[str],
    start_index: int,
    end_index: int,
) -> list[str]:
    """Extract the download links for a list of chapter URLs."""
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_download_link(chapter_url, session) for chapter_url in chapter_urls
        ]

        # Wait for all tasks to complete and filter out None values
        download_links = await asyncio.gather(*tasks)

        # Remove the suffix from each download link
        return [
            re.sub(r"1\.(png|gif|jpg)$", "", download_link)
            for download_link in download_links[start_index:end_index]
            if download_link
        ]


def download_page(
    response: Response,
    page: int,
    extension: str,
    download_link: str,
    download_path: str,
) -> None:
    """Download a single page of a chapter."""
    filename = f"{page}{extension}"
    final_path = Path(download_path) / filename

    try:
        response = SESSION.get(
            download_link,
            stream=True,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        response.raise_for_status()

    except requests.exceptions.RequestException as req_err:
        message = f"Error downloading {filename}: {req_err}"
        logging.exception(message)
        write_file(
            ERROR_LOG,
            mode="a",
            content=f"Error downloading {filename} from {download_link}: {req_err}",
        )

    else:
        with Path(final_path).open("wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk is not None:
                    file.write(chunk)


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
                    test_download_link,
                    download_path,
                )
                return True

        except requests.exceptions.RequestException as req_err:
            message = f"Failed attempt with {test_download_link}: {req_err}"
            logging.warning(message)
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
            message = f"Page {page} could not be downloaded with any extension."
            logging.error(message)

        progress_percentage = (page / num_pages) * 100
        job_progress.update(task, completed=progress_percentage)

    job_progress.update(task, completed=100, visible=False)
    job_progress.advance(overall_task)


def process_pdf_generation(manga_name: str, job_progress: Progress) -> None:
    """Process the generation of PDF files for a specific manga."""
    manga_parent_folder = Path(DOWNLOAD_FOLDER) / manga_name
    generate_pdf_files(str(manga_parent_folder), job_progress)


async def process_manga_download(
    url: str,
    start_chapter: int | None = None,
    end_chapter: int | None = None,
    *,
    generate_pdf: bool = False,
) -> None:
    """Process the complete download and PDF generation workflow for a manga."""
    soup = await fetch_page(url)

    try:
        _, manga_name = extract_manga_info(url)
        chapter_urls, pages_per_chapter = await extract_chapters_info(soup)

        start_index, end_index = validate_chapter_range(
            start_chapter,
            end_chapter,
            num_chapters=len(chapter_urls),
        )
        download_links = await extract_download_links(
            chapter_urls,
            start_index,
            end_index,
        )

    except ValueError as val_err:
        message = f"Value error: {val_err}"
        logging.exception(message)

    else:
        job_progress = create_progress_bar()
        progress_table = create_progress_table(manga_name, job_progress)

        with Live(progress_table, refresh_per_second=10):
            run_in_parallel(
                download_chapter,
                download_links,
                job_progress,
                pages_per_chapter[start_index:end_index],
                manga_name,
            )
            if generate_pdf:
                process_pdf_generation(manga_name, job_progress)


def add_pdf_argument(parser: ArgumentParser) -> None:
    """Add a command-line argument to enable PDF generation."""
    parser.add_argument(
        "-p",
        "--pdf",
        action="store_true",
        help="Generate PDF after downloading the manga.",
    )

def parse_arguments() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(
        description="Download manga and optionally generate a PDF.",
    )
    parser.add_argument("url", type=str, help="The URL of the manga to process.")
    add_pdf_argument(parser)
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="The starting chapter number.",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="The ending chapter number.",
    )
    return parser.parse_args()


async def main() -> None:
    """Initiate the manga download process from a given URL."""
    clear_terminal()
    args = parse_arguments()
    await process_manga_download(
        args.url, start_chapter=args.start, end_chapter=args.end, generate_pdf=args.pdf,
    )


if __name__ == "__main__":
    asyncio.run(main())
