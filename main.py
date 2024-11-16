"""
This module facilitates the downloading of manga from a list of URLs and
optionally generates PDFs after the download.

Command-Line Arguments:
    - -p, --pdf (optional): If provided, the script will generate a PDF for
                            each manga after downloading.
    - The script expects a file named URLs.txt to exist, containing a list of 
      manga URLs to process.

Usage:
To run the script, execute it from the command line. The available options are:
    1. To download manga without generating PDFs:
       python3 main.py
    2. To download manga and generate PDFs:
       python3 main.py -p
"""

import asyncio
import argparse

from helpers.general_utils import clear_terminal
from helpers.file_utils import read_file, write_file
from manga_downloader import process_manga_download

FILE = 'URLs.txt'

async def process_urls(urls, generate_pdf_flag=False):
    """
    Validates and downloads items for a list of URLs.

    Args:
        urls (list): A list of URLs to process.
        generate_pdf_flag (bool): Whether to generate PDFs after downloading.
    """
    for url in urls:
        await process_manga_download(url, generate_pdf_flag=generate_pdf_flag)

def setup_parser():
    """
    Set up and return the argument parser for the manga download process.

    Returns:
        argparse.ArgumentParser: The configured argument parser instance.

    Arguments parsed:
        - `-p` or `--pdf`: Optional flag to indicate that a PDF should be
                           generated after downloading the manga.
    """
    parser = argparse.ArgumentParser(
        description="Download manga and optionally generate a PDF."
    )
    parser.add_argument(
        '-p', '--pdf', action='store_true',
        help="Generate PDF after downloading the manga."
    )
    return parser

async def main():
    """
    Main function to execute the script.

    Reads URLs from a file, processes the downloads for each URL, and clears
    the file after the processing is complete.
    """
    parser = setup_parser()
    args = parser.parse_args()

    clear_terminal()
    urls = read_file(FILE)
    await process_urls(urls, generate_pdf_flag=args.pdf)
    write_file(FILE)

if __name__ == '__main__':
    asyncio.run(main())
