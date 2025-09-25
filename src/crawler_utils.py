"""Asynchronous utility functions for crawling manga chapters and extracting metadata.

This module provides high-level helpers to:
- Retrieve chapter URLs and the corresponding number of pages.
- Normalize chapter URLs depending on manga type (e.g., Manga, Manhwa).
- Extract the manga type from embedded script data.
- Fetch download links for individual chapter pages.
- Collect cleaned download links for multiple chapters.

Intended to be used in combination with download utilities to provide a complete
pipeline for scraping and downloading manga content.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from .config import (
    FIRST_PAGE_SUFFIX_REGEX,
    MANGA_LIKE,
    MANGA_TYPE_REGEX,
    MAX_RETRIES,
    TIMEOUT,
    WAIT_TIME_RETRIES,
)
from .general_utils import check_real_page


async def fetch_chapter_data(chapter_url: str, session: ClientSession) -> tuple:
    """Fetch the number of pages for a given chapter URL, retrying if necessary."""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(chapter_url, timeout=TIMEOUT) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                validated_soup = await check_real_page(soup, session, TIMEOUT)
                page_item = validated_soup.find(
                    "select", {"class": "page custom-select"},
                )
                if page_item:
                    option_text = page_item.find("option").get_text()
                    num_pages = option_text.rstrip("/").split("/")[-1]
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
) -> tuple:
    """Extract chapter URLs and the corresponding number of pages."""
    chapter_items = soup.find_all("a", {"class": "chap", "title": True})
    tasks = []

    # Create a list of tasks only for chapters that contain the match
    for chapter_item in chapter_items:
        chapter_url = chapter_item["href"]
        if "/read/" in chapter_url:
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


def generate_chapter_url(chapter_url: str, manga_type: str) -> str | None:
    """Return the normalized chapter URL based on manga type, or None if unsupported."""
    if manga_type in MANGA_LIKE:
        return f"{chapter_url}/1"

    # Manhwa are paginated differently by default. The URL below adjusts it to behave
    # like a Manga, displaying one image per page.
    if manga_type == "Manhwa":
        return chapter_url.replace("?style=list", "/1?style=pages")

    log_message = f"Manga type '{manga_type}' is not supported."
    logging.warning(log_message)
    return None


async def fetch_download_link(
    chapter_url: str,
    session: ClientSession,
    manga_type: str | None = None,
) -> str | None:
    """Fetch the download link for the first image in a chapter page."""
    if manga_type is None:
        logging.warning("Manga type not found.")
        return None

    url_to_fetch = generate_chapter_url(chapter_url, manga_type)

    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(url_to_fetch, timeout=TIMEOUT) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                validated_soup = await check_real_page(soup, session, TIMEOUT)
                img_items = validated_soup.find_all("img", {"class": "img-fluid"})

                # Download link found
                if img_items:
                    return img_items[-1]["src"]

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
    manga_type: str,
) -> list[str]:
    """Extract the download links for a list of chapter URLs."""
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_download_link(chapter_url, session, manga_type=manga_type)
            for chapter_url in chapter_urls
        ]

        # Wait for all tasks to complete and filter out None values
        download_links = await asyncio.gather(*tasks)

        # Remove the suffix from each download link
        return [
            re.sub(FIRST_PAGE_SUFFIX_REGEX, "", download_link)
            for download_link in download_links[start_index:end_index]
            if download_link
        ]


def extract_manga_type(soup: BeautifulSoup, manga_slug: str) -> str | None:
    """Extract the type of manga (e.g., "Manga") from the page's script content."""
    script_items = soup.find_all("script")
    script_text = script_items[-1].get_text()

    # Build the regex pattern to find the manga data based on its slug
    manga_slug_pattern = rf'"slug":"{manga_slug}".*?"typeT":\s*"[^"]*"'
    slug_match = re.search(manga_slug_pattern, script_text)

    # If the manga_slug is found, extract the part containing the typeT
    if slug_match:
        manga_slug_text = slug_match.group(0)
        type_match = re.search(MANGA_TYPE_REGEX, manga_slug_text)

        # Return the manga type if found, otherwise return None
        if type_match:
            return type_match.group(1)

    return None

def extract_volume_info(soup):
    """
    Extracts the volume list and relative list of chapter URLs.
    If a page doesn't contain volumes, it'll retrieve a volume with all chapters.
    Output:
        [
            {"name": "Volume 1", "chapters": [{"title": ..., "url": ...}, ...]},
            ...
        ]

    """
    volumes = []
    volume_elements = soup.find_all("div", class_="volume-element")
    if volume_elements:
        for vol in volume_elements:
            # Volume name
            name_tag = vol.find("p", class_="volume-name")
            volume_name = name_tag.get_text(strip=True) if name_tag else "Volume"
            # Volume chapters
            chapters = []
            chapters_container = vol.find("div", class_="volume-chapters")
            if chapters_container:
                chapter_divs = chapters_container.find_all("div", class_="chapter")
                for chap in chapter_divs:
                    a_tag = chap.find("a", class_="chap", title=True)
                    if a_tag:
                        chapters.append({
                            "title": a_tag["title"],
                            "url": a_tag["href"]
                        })
            if chapters:
                volumes.append({
                    "name":
                        volume_name,
                    "chapters":
                        sorted(chapters,
                               key=lambda c: c['title'])})
                
    else:
        # No available volumes
        logging.error("The selected link doesn't have available volumes.")
        return None
    return sorted(volumes, key=lambda v: v['name'])