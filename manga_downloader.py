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
import sys
import argparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rich.live import Live

from helpers.download_utils import run_in_parallel
from helpers.format_utils import extract_manga_info
from helpers.progress_utils import create_progress_bar, create_progress_table
from helpers.pdf_generator import generate_pdf_files

SCRIPT_NAME = os.path.basename(__file__)
DOWNLOAD_FOLDER = "Downloads"

SESSION = requests.Session()
CHUNK_SIZE = 16 * 1024
TIMEOUT = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) "
        "Gecko/20100101 Firefox/117.0"
    ),
    "Connection": "keep-alive",
}

def extract_chapters_info(soup, match="/read/"):
    """
    Extracts the URLs of manga chapters and the number of pages for each
    chapter.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the HTML of
                              the manga's main page.
        match (str, optional): A substring that is used to filter chapter 
                               URLs. The default is "/read/".

    Returns:
        tuple: A tuple containing two lists:
            - chapter_urls (list of str): A list of URLs for each chapter that
                                          matches the `match` string.
            - pages_per_chapter (list of int): A list of integers representing
                                               the number of pages in each
                                               chapter.

    Raises:
        requests.exceptions.RequestException: If the HTTP request for a chapter 
                                              fails.
    """
    chapter_urls = []
    pages_per_chapter = []
    chapter_items = soup.find_all('a', {'class': 'chap', 'title': True})

    for chapter_item in chapter_items:
        chapter_url = chapter_item['href']
        if match in chapter_url:
            chapter_urls.append(chapter_url)

            response_chapter = SESSION.get(chapter_url, timeout=TIMEOUT)
            soup_chapter = BeautifulSoup(response_chapter.text, 'html.parser')
            page_item = soup_chapter.find(
                'select', {'class': 'page custom-select'}
            )
            num_pages = page_item.find('option').get_text().split('/')[-1]
            pages_per_chapter.append(num_pages)

    return chapter_urls[::-1], pages_per_chapter[::-1]

def extract_download_links(chapter_urls):
    """
    Extracts and formats download links for the images in each chapter.

    Args:
        chapter_urls (list): The sorted list of chapter URLs.

    Returns:
        list: A list of download links for the images.
    """
    download_links = []

    for chapter_url in chapter_urls:
        url_to_fetch = chapter_url + "/1"

        response = SESSION.get(url_to_fetch, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')

        for element in soup.find_all('img', {'class': 'img-fluid'}):
            download_links.append(element['src'])

    return [
        download_link[:-len("1.png")]
        for (indx, download_link) in enumerate(download_links)
        if indx % 2 != 0
    ]

def download_page(reqs, page, base_download_link, download_path):
    """
    Downloads a single page of a chapter.

    Args:
        reqs (requests.Response): The HTTP response object.
        page (int): The page number.
        base_download_link (str): The base download link.
        download_path (str): The directory path to save the image.
    """
    extension_mapping = {True: ".png", False: ".jpg"}
    status_check = reqs.status_code == 200
    filename = str(page) + extension_mapping[status_check]

    download_link = base_download_link + filename
    final_path = os.path.join(download_path, filename)

    try:
        response = SESSION.get(
            download_link, stream=True, headers=HEADERS, timeout=TIMEOUT
        )
        response.raise_for_status()

        with open(final_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk is not None:
                    file.write(chunk)

    except requests.exceptions.RequestException as req_err:
        print(f"Error downloading {filename}: {req_err}")

def create_download_directory(manga_name, indx_chapter):
    """
    Creates the directory structure for downloading a specific chapter of a
    manga.

    Args:
        manga_name (str): The name of the manga. This is used to create the
                          main folder where all manga chapters will be stored.
        indx_chapter (int): The index of the chapter being downloaded.

    Returns:
        str: The full path to the chapter's download folder.
    """
    path = Path(os.path.join(DOWNLOAD_FOLDER, manga_name))
    path.mkdir(parents=True, exist_ok=True)

    subdir_name = os.path.join(manga_name, f"Chapter {indx_chapter + 1}")
    download_path = os.path.join(DOWNLOAD_FOLDER, subdir_name)
    os.makedirs(download_path, exist_ok=True)
    return download_path

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
        test_download_link = base_download_link + str(page) + ".png"
        reqs = SESSION.get(
            test_download_link, stream=True, headers=HEADERS, timeout=TIMEOUT
        )
        download_page(reqs, page, base_download_link, download_path)
        progress_percentage = (page / num_pages) * 100
        job_progress.update(task, completed=progress_percentage)

    job_progress.update(task, completed=100, visible=False)
    job_progress.advance(overall_task)

def fetch_manga_page(url):
    """
    Fetches the manga page and returns its BeautifulSoup object.

    Args:
        url (str): The URL of the manga page.

    Returns:
        BeautifulSoup: The BeautifulSoup object containing the HTML.

    Raises:
        requests.RequestException: If there is an error with the HTTP request.
    """
    try:
        response = SESSION.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    except requests.RequestException as req_err:
        print(f"Error fetching the manga page: {req_err}")
        sys.exit(1)

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

def process_manga_download(url, generate_pdf_flag=False):
    """
    Process the complete download and PDF generation workflow for a manga,
    given its URL.

    Args:
        url (str): The URL of the manga page. The URL should point to a page
                   that contains information about the manga and its chapters.
        generate_pdf_flag (bool): If True, generate a PDF after download.

    Raises:
        ValueError: If there is an issue extracting the manga information from
                    the URL or fetching chapter details, a `ValueError` is
                    raised.
    """
    soup = fetch_manga_page(url)

    try:
        (_, manga_name) = extract_manga_info(url)
        (chapter_urls, pages_per_chapter) = extract_chapters_info(soup)

        download_links = extract_download_links(chapter_urls)

        job_progress = create_progress_bar()
        progress_table = create_progress_table(manga_name, job_progress)

        with Live(progress_table, refresh_per_second=10):
            run_in_parallel(
                download_chapter, download_links, job_progress,
                pages_per_chapter, manga_name
            )

            if generate_pdf_flag:
                process_pdf_generation(manga_name, job_progress)

    except ValueError as val_err:
        print(f"Value error: {val_err}")

def clear_terminal():
    """
    Clears the terminal screen based on the operating system.
    """
    commands = {
        'nt': 'cls',      # Windows
        'posix': 'clear'  # macOS and Linux
    }

    command = commands.get(os.name)
    if command:
        os.system(command)

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

def main():
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
    process_manga_download(args.url, generate_pdf_flag=args.pdf)

if __name__ == '__main__':
    main()
