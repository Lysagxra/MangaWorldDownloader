"""Main module of the project.

This module facilitates the downloading of manga from a list of URLs and optionally
generates PDFs after the download.
"""

import argparse
import asyncio
from argparse import Namespace

from helpers.config import ERROR_LOG, URLS_FILE
from helpers.file_utils import read_file, write_file
from helpers.general_utils import clear_terminal
from manga_downloader import process_manga_download


async def process_urls(urls: list[str], args: Namespace) -> None:
    """Validate and downloads items for a list of URLs."""
    for url in urls:
        await process_manga_download(url, generate_pdf=args.pdf)


def parse_arguments() -> Namespace:
    """Parse only the --pdf argument."""
    parser = argparse.ArgumentParser(
        description="Download manga and optionally generate a PDF.",
    )
    parser.add_argument(
        "-p",
        "--pdf",
        action="store_true",
        help="Generate PDF after downloading the manga.",
    )
    return parser.parse_args()


async def main() -> None:
    """Run the script."""
    # Clear the terminal and session log file
    clear_terminal()
    write_file(ERROR_LOG)

    # Parse arguments
    args = parse_arguments()

    # Read and process URLs, ignoring empty lines
    urls = [url.strip() for url in read_file(URLS_FILE) if url.strip()]
    await process_urls(urls, args=args)

    # Clear URLs file
    write_file(URLS_FILE)


if __name__ == "__main__":
    asyncio.run(main())
