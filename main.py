"""Main module of the project.

This module facilitates the downloading of manga from a list of URLs and optionally
generates PDFs after the download.
"""

import asyncio
from argparse import Namespace

from manga_downloader import process_manga_download
from src.config import SESSION_LOG, URLS_FILE, parse_arguments
from src.file_utils import read_file, write_file
from src.general_utils import clear_terminal


async def process_urls(urls: list[str], args: Namespace) -> None:
    """Validate and downloads items for a list of URLs."""
    for url in urls:
        await process_manga_download(url, generate_pdf=args.pdf)


async def main() -> None:
    """Run the script."""
    # Clear the terminal and session log file
    clear_terminal()
    write_file(SESSION_LOG)

    # Parse arguments
    args = parse_arguments(common_only=True)

    # Read and process URLs, ignoring empty lines
    urls = [url.strip() for url in read_file(URLS_FILE) if url.strip()]
    await process_urls(urls, args=args)

    # Clear URLs file
    write_file(URLS_FILE)


if __name__ == "__main__":
    asyncio.run(main())
