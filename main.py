"""Main module of the project.

This module facilitates the downloading of manga from a list of URLs and optionally
generates PDFs after the download.
"""

import argparse
import asyncio
from argparse import ArgumentParser

from helpers.config import URLS_FILE
from helpers.file_utils import read_file, write_file
from helpers.general_utils import clear_terminal
from manga_downloader import process_manga_download


async def process_urls(urls: list[str], *, generate_pdf: bool = False) -> None:
    """Validate and downloads items for a list of URLs."""
    for url in urls:
        await process_manga_download(url, generate_pdf=generate_pdf)


def setup_parser() -> ArgumentParser:
    """Set up and return the argument parser for the manga download process."""
    parser = argparse.ArgumentParser(
        description="Download manga and optionally generate a PDF.",
    )
    parser.add_argument(
        "-p",
        "--pdf",
        action="store_true",
        help="Generate PDF after downloading the manga.",
    )
    return parser


async def main() -> None:
    """Run the script.

    Reads URLs from a file, processes the downloads for each URL, and clears
    the file after the processing is complete.
    """
    parser = setup_parser()
    args = parser.parse_args()

    clear_terminal()
    urls = read_file(URLS_FILE)
    await process_urls(urls, generate_pdf=args.pdf)
    write_file(URLS_FILE)


if __name__ == "__main__":
    asyncio.run(main())
