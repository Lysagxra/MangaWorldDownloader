"""
A manga downloader and PDF generator for MangaWorld.

This module allows you to download manga chapters from a given manga URL,
process each chapter, and generate PDF files for the downloaded images.
It utilizes `requests` for HTTP requests, `BeautifulSoup` for HTML parsing,
and `rich` for displaying a progress bar during the download and conversion
process.

Command-line usage:
    python3 <script_name> <manga_url>

Example:
    python3 manga_downloader.py https://www.mangaworld.ac/manga/2754/sayonara-eri
"""

import os
import argparse
import asyncio
import random
import time

import aiohttp
import requests
from PIL import ImageFile
from bs4 import BeautifulSoup
from rich.live import Live

from helpers.download_utils import run_in_parallel
from helpers.format_utils import extract_manga_info
from helpers.pdf_generator import generate_pdf_files
from helpers.progress_utils import (
    create_progress_bar,
    create_progress_table
)
from helpers.general_utils import (
    check_real_page,
    fetch_page,
    create_download_directory,
    clear_terminal
)
from helpers.config import (
    DOWNLOAD_FOLDER,
    CHUNK_SIZE,
    TIMEOUT,
    HEADERS,
    MAX_RETRIES,
    SECONDS
)

ImageFile.LOAD_TRUNCATED_IMAGES = True
SESSION = requests.Session()


async def fetch_chapter_data(chapter_url, session):
    """
    Fetches the number of pages for a given chapter URL, retrying if necessary.

    Args:
        chapter_url (str): The URL of the chapter to fetch data from.
        session (aiohttp.ClientSession): The aiohttp session used for making
                                         the HTTP request.

    Returns:
        tuple: A tuple containing the chapter URL and the number of
               pages (str), or (None, None) if all attempts fail.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            async with session.get(chapter_url, timeout=TIMEOUT) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                soup = await check_real_page(soup, session, TIMEOUT)

                page_item = soup.find('select', {'class': 'page custom-select'})
                if page_item:
                    option_text = page_item.find('option').get_text()
                    num_pages = option_text.split('/')[-1]
                    return chapter_url, num_pages  # Page count found

                print(f"[Retry {attempt+1}/{MAX_RETRIES}] Page count not found for {chapter_url}")
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            print(f"[Retry {attempt+1}/{MAX_RETRIES}] Network error fetching {chapter_url}: {err}")

        attempt += 1
        if attempt < MAX_RETRIES:
            await asyncio.sleep(1 + random.uniform(0, SECONDS-1))  # Random wait between 1 and SECOND seconds

    print(f"Failed to fetch chapter data for {chapter_url} after {MAX_RETRIES} attempts.")
    return None, None


async def get_chapter_urls_and_pages(soup, session, match="/read/"):
    """
    Extracts chapter URLs and the corresponding number of pages from the
    provided HTML soup.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed
                              HTML of the page.
        session (aiohttp.ClientSession): The aiohttp session used for making
                                         asynchronous HTTP requests.
        match (str): A substring to match in chapter URLs
                     (default is "/read/").

    Returns:
        tuple: A tuple containing:
            - List of chapter URLs (str), in reverse order.
            - List of corresponding page counts (str), in reverse order.

    Raises:
        asyncio.TimeoutError: If any HTTP request times out.
        aiohttp.ClientError: If any network-related error occurs during the
                             HTTP request.
    """
    chapter_items = soup.find_all('a', {'class': 'chap', 'title': True})
    tasks = []

    for chapter_item in chapter_items:
        chapter_url = chapter_item['href']
        if match in chapter_url:
            tasks.append(
                fetch_chapter_data(chapter_url, session)
            )

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

async def extract_chapters_info(soup):
    """
    Extracts chapter URLs and page numbers.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed
                              HTML of the page.

    Returns:
        tuple: A tuple containing:
            - List of chapter URLs (str).
            - List of corresponding page counts (str).
    """
    async with aiohttp.ClientSession() as session:
        chapter_urls, pages_per_chapter = await get_chapter_urls_and_pages(soup, session)
        return chapter_urls, pages_per_chapter



async def fetch_download_link(chapter_url, session):
    """
    Fetches the download link for the first image in a chapter page,
    retrying multiple times if necessary.

    Args:
        chapter_url (str): The URL of the chapter to fetch the download link from.
        session (aiohttp.ClientSession): The aiohttp session used for making
                                         the HTTP request.

    Returns:
        str or None: The download URL for the image if found, or None if all attempts fail.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            url_to_fetch = f"{chapter_url}/1"
            async with session.get(url_to_fetch, timeout=TIMEOUT) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                validated_soup = await check_real_page(soup, session, TIMEOUT)

                img_items = validated_soup.find_all('img', {'class': 'img-fluid'})
                if img_items:
                    return img_items[-1]['src']  # Download link found

                print(f"[Retry {attempt+1}/{MAX_RETRIES}] Download link not found for {chapter_url}")
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            print(f"[Retry {attempt+1}/{MAX_RETRIES}] Network error fetching {chapter_url}: {err}")

        attempt += 1
        if attempt < MAX_RETRIES:
            await asyncio.sleep(1 + random.uniform(0, SECONDS))  # Random wait between 1 and 5 seconds
    
    print(f"Failed to fetch download link for {chapter_url} after {MAX_RETRIES} attempts.")
    return None

async def extract_download_links(chapter_urls):
    """
    Extracts the download links for a list of chapter URLs.

    Args:
        chapter_urls (list): A list of chapter URLs to fetch download links
                             from.

    Returns:
        list: A list of cleaned download links, with the "1.png" suffix
              removed.

    Raises:
        asyncio.TimeoutError: If any HTTP request times out.
        aiohttp.ClientError: If a network-related error occurs during the
                             request.
    """
    download_links = []
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_download_link(chapter_url, session)
            for chapter_url in chapter_urls
        ]

        # Wait for all tasks to complete and filter out None values
        results = await asyncio.gather(*tasks)

        # Remove the "1.png" suffix from each download link
        download_links = [
            download_link[:-len("1.png")]
            for download_link in results #if download_link
        ]

    return download_links


def download_page(response, page, base_download_link, download_path):
    """
    Downloads a single page of a chapter.

    Args:
        response (requests.Response): The HTTP response object.
        page (int): The page number.
        base_download_link (str): The base download link.
        download_path (str): The directory path to save the image.
    """
    extension_mapping = {True: ".png", False: ".jpg"}
    status_check = response.status_code == 200
    filename = str(page) + extension_mapping[status_check]

    download_link = base_download_link + filename
    final_path = os.path.join(download_path, filename)

    try:
        response = SESSION.get(
            download_link,
            stream=True,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()

        with open(final_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk is not None:
                    file.write(chunk)

    except requests.exceptions.RequestException as req_err:
        print(f"Error downloading {filename}: {req_err}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error downloading {filename} from {download_link} : {req_err}\n")

def download_chapter(item_info, pages_per_chapter, manga_name, task_info):
    """
    Downloads all pages for a specific manga chapter and updates the progress.

    Args:
        item_info (tuple): A tuple containing the chapter index (indx_chapter) 
                           and the base download link for the chapter
                           (base_download_link).
        pages_per_chapter (list): A list containing the number of pages for
                                  each chapter.
        manga_name (str): The name of the manga. This is used to determine the
                          download directory.
        task_info (tuple): A tuple containing the progress tracker
                           (`job_progress`), the task object, and the overall 
                           task object for managing progress.
    """
    (job_progress, task, overall_task) = task_info
    (indx_chapter, base_download_link) = item_info

    download_path = create_download_directory(manga_name, indx_chapter)
    num_pages = int(pages_per_chapter[indx_chapter])

    for page in range(1, num_pages + 1):
        test_download_link = f"{base_download_link}{page}.png"

        if (
            os.path.exists(test_download_link)
            or os.path.exists(os.path.join(download_path, f"{page}.jpg"))
        ):
            continue

        response = SESSION.get(
            test_download_link,
            stream=True,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        download_page(response, page, base_download_link, download_path)
        progress_percentage = (page / num_pages) * 100
        job_progress.update(task, completed=progress_percentage)

    job_progress.update(task, completed=100, visible=False)
    job_progress.advance(overall_task)

def process_pdf_generation(manga_name, job_progress):
    """
    Process the generation of PDF files for a specific manga by traversing its
    subfolders and converting image files to PDFs.

    Args:
        manga_name (str): The name of the manga for which PDF files should be 
                          generated. This is used to locate the manga's folder
                          within the `DOWNLOAD_FOLDER`.
        job_progress (Progress): A progress tracker object that monitors the 
                                 status of the PDF generation process.
    """
    manga_parent_folder = os.path.join(DOWNLOAD_FOLDER, manga_name)
    generate_pdf_files(manga_parent_folder, job_progress)

async def process_manga_download(url, generate_pdf=False):
    """
    Process the complete download and PDF generation workflow for a manga,
    given its URL.

    Args:
        url (str): The URL of the manga page. The URL should point to a page
                   that contains information about the manga and its chapters.
        generate_pdf (bool): If True, generate a PDF after download.

    Raises:
        ValueError: If there is an issue extracting the manga information from
                    the URL or fetching chapter details, a `ValueError` is
                    raised.
    """
    soup = await fetch_page(url)

    try:
        (_, manga_name) = extract_manga_info(url)
        (chapter_urls, pages_per_chapter) = await extract_chapters_info(soup)
        download_links = await extract_download_links(chapter_urls)

        job_progress = create_progress_bar()
        progress_table = create_progress_table(manga_name, job_progress)

        with Live(progress_table, refresh_per_second=10):
            run_in_parallel(
                download_chapter, download_links, job_progress,
                pages_per_chapter, manga_name
            )
            if generate_pdf:
                process_pdf_generation(manga_name, job_progress)

    except ValueError as val_err:
        print(f"Value error: {val_err}")

def setup_parser():
    """
    Set up and return the argument parser for the manga download process.

    Returns:
        argparse.ArgumentParser: The configured argument parser instance.

    Example usage:
        - `python script.py -p <manga_url>` will download the manga and
          generate a PDF.
        - `python script.py <manga_url>` will download the manga without
          generating a PDF.
    """
    parser = argparse.ArgumentParser(
        description="Download manga and optionally generate a PDF."
    )
    parser.add_argument(
        '-p', '--pdf', action='store_true',
        help="Generate PDF after downloading the manga."
    )
    parser.add_argument(
        'url', type=str, help="The URL of the manga to process."
    )
    return parser

async def main():
    """
    Main function to initiate the manga download process from a given URL.

    Arguments are processed as follows:
    - The first argument is the URL of the manga page (required).
    - The optional '-p' flag indicates that a PDF should be generated after
      downloading the manga.
    """
    clear_terminal()
    parser = setup_parser()
    args = parser.parse_args()
    await process_manga_download(args.url, generate_pdf=args.pdf)

if __name__ == '__main__':
    asyncio.run(main())
