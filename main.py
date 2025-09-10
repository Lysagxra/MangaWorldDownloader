"""Main module of the project.

This module facilitates the downloading of manga from a list of URLs and optionally
generates PDFs after the download.
"""

import asyncio
from argparse import ArgumentParser, Namespace

from helpers.config import ERROR_LOG, URLS_FILE
from helpers.file_utils import read_file, write_file
from helpers.general_utils import clear_terminal
from manga_downloader import add_pdf_argument, process_manga_download


def parse_arguments() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(
        description="Download manga and optionally generate a PDF.",
    )
    add_pdf_argument(parser)
    return parser.parse_args()


async def process_urls(urls: list[str], args: Namespace) -> None:
    """Validate and downloads items for a list of URLs."""
    for url in urls:
        await process_manga_download(url, generate_pdf=args.pdf)


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
