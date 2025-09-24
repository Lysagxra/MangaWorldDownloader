"""A manga downloader and PDF generator for MangaWorld.

This module allows you to download manga chapters from a given manga URL, process each
chapter, and generate PDF files for the downloaded images. It utilizes `requests` for
HTTP requests, `BeautifulSoup` for HTML parsing, and `rich` for displaying a progress
bar during the download and conversion process.
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
)
from src.download_utils import download_chapter, run_in_parallel
from src.crawler_utils import fetch_chapter_data
from src.format_utils import extract_manga_info
from src.general_utils import clear_terminal, fetch_page, validate_chapter_range
from src.pdf_generator import generate_pdf_files
from src.progress_utils import create_progress_bar, create_progress_table, create_select_items_list

if TYPE_CHECKING:
    from rich.progress import Progress


def process_pdf_generation(manga_name: str, job_progress: Progress, single_pdf=False) -> None:
    """Process the generation of PDF files for a specific manga."""
    manga_parent_folder = Path(DOWNLOAD_FOLDER) / manga_name
    generate_pdf_files(str(manga_parent_folder), job_progress, single_pdf=single_pdf)


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
        volumes = extract_volume_info(soup)
        volume_names = [v['name'] for v in volumes]
        selected_indices = create_select_items_list(volume_names)
        for idx in selected_indices:
            volume = volumes[idx]
            chapter_urls = [c['url'] for c in volume['chapters']]
            pages_per_chapter = []
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_chapter_data(url, session) for url in chapter_urls]
                results = await asyncio.gather(*tasks)
                for result in results:
                    pages_per_chapter.append(result[1] if result and result[1] else None)

            download_links = await extract_download_links(
                chapter_urls,
                0,
                len(chapter_urls),
                manga_type,
            )
            job_progress = create_progress_bar()
            progress_table = create_progress_table(f"{manga_name} - {volume['name']}", job_progress)

            with Live(progress_table, refresh_per_second=10):
                run_in_parallel(
                    download_chapter,
                    download_links,
                    job_progress,
                    pages_per_chapter,
                    f"{manga_name}/{volume['name']}"
                )
                if generate_pdf:
                    process_pdf_generation(f"{manga_name}/{volume['name']}", job_progress, single_pdf=True)
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


async def main() -> None:
    """Initiate the manga download process from a given URL."""
    clear_terminal()
    args = parse_arguments()
    await process_manga_download(
        args.url, start_chapter=args.start, end_chapter=args.end, generate_pdf=args.pdf, volume_mode=args.volume
    )


if __name__ == "__main__":
    asyncio.run(main())
