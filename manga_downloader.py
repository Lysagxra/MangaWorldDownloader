"""A manga downloader and PDF generator for MangaWorld.

This module allows you to download manga chapters from a given manga URL, process each
chapter, and generate PDF files for the downloaded images.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
from rich.live import Live

from src.config import DOWNLOAD_FOLDER, parse_arguments
from src.crawler_utils import (
    extract_chapters_info,
    extract_download_links,
    extract_manga_type,
    extract_volume_info,
    fetch_chapter_data,
)
from src.download_utils import download_chapter, run_in_parallel
from src.format_utils import extract_manga_info
from src.general_utils import clear_terminal, fetch_page, validate_chapter_range
from src.pdf_generator import generate_pdf_files
from src.progress_utils import (
    create_progress_bar,
    create_progress_table,
    create_select_items_list,
)

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from rich.progress import Progress


def process_pdf_generation(
    manga_name: str,
    job_progress: Progress,
    *,
    single_pdf: bool = False,
) -> None:
    """Process the generation of PDF files for a specific manga."""
    manga_parent_folder = Path(DOWNLOAD_FOLDER) / manga_name
    generate_pdf_files(str(manga_parent_folder), job_progress, single_pdf=single_pdf)


def download_chapter_with_progress(
    manga_name: str,
    download_links: list[str],
    pages_per_chapter: list[int],
    *,
    generate_pdf: bool = False,
    volume_name: str | None = None,
) -> None:
    """Download the chapters of a manga and displays a progress bar.

    Optionally generate a PDF of the manga chapters if requested.
    """
    task_description = (
        manga_name if volume_name is None else f"{manga_name} - {volume_name}"
    )
    working_path = manga_name if volume_name is None else f"{manga_name}/{volume_name}"

    job_progress = create_progress_bar()
    progress_table = create_progress_table(task_description, job_progress)

    with Live(progress_table, refresh_per_second=10):
        run_in_parallel(
            download_chapter,
            download_links,
            job_progress,
            pages_per_chapter,
            working_path,
        )
        if generate_pdf:
            single_pdf = volume_name is not None
            process_pdf_generation(working_path, job_progress, single_pdf=single_pdf)


async def process_volumes_download(
    soup: BeautifulSoup,
    manga_name: str,
    manga_type: str,
    *,
    generate_pdf: bool = False,
) -> None:
    """Process selected manga volumes and downloads their chapters."""
    volumes = extract_volume_info(soup)
    volume_names = [volume["name"] for volume in volumes]
    selected_indexes = create_select_items_list(volume_names)

    for indx in selected_indexes:
        volume = volumes[indx]
        chapter_urls = [chapter["url"] for chapter in volume["chapters"]]
        pages_per_chapter = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_chapter_data(chapter_url, session) for chapter_url in chapter_urls
            ]
            results = await asyncio.gather(*tasks)
            pages_per_chapter = [
                result[1] if result and result[1] else None for result in results
            ]
            download_links = await extract_download_links(
                chapter_urls,
                0,
                len(chapter_urls),
                manga_type,
            )
            download_chapter_with_progress(
                manga_name,
                download_links,
                pages_per_chapter,
                generate_pdf=generate_pdf,
                volume_name=volume["name"],
            )


async def process_manga_download(
    url: str,
    start_chapter: int | None = None,
    end_chapter: int | None = None,
    *,
    generate_pdf: bool = False,
    volume_mode: bool = False,
) -> None:
    """Process the complete download and PDF generation workflow for a manga."""
    _, manga_name, manga_slug = extract_manga_info(url)
    soup = await fetch_page(url)
    manga_type = extract_manga_type(soup, manga_slug)

    if volume_mode:
        await process_volumes_download(
            soup,
            manga_name,
            manga_type,
            generate_pdf=generate_pdf,
        )

    else:
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
            manga_type,
        )
        download_chapter_with_progress(
            manga_name,
            download_links,
            pages_per_chapter[start_index:end_index],
            generate_pdf=generate_pdf,
        )


async def main() -> None:
    """Initiate the manga download process from a given URL."""
    clear_terminal()
    args = parse_arguments()
    await process_manga_download(
        args.url,
        start_chapter=args.start,
        end_chapter=args.end,
        generate_pdf=args.pdf,
        volume_mode=args.volume,
    )


if __name__ == "__main__":
    asyncio.run(main())
