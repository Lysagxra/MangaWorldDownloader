"""Utilities for fetching web pages, managing directories, and clearing the terminal.

This module includes functions to handle common tasks such as sending HTTP requests,
parsing HTML, creating download directories, and clearing the terminal, making it
reusable across projects.
"""

import asyncio
import logging
import os
import re
import sys

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup


async def check_real_page(
    initial_response: BeautifulSoup,
    session: ClientSession,
    timeout: int = 10,
) -> BeautifulSoup:
    """Check if the provided response contains a redirect to a real page."""
    parsed_response = initial_response
    if (
        initial_response.body
        and initial_response.body.script
        and "document.cookie" in initial_response.body.script.text
    ):
        # Extract the cookie
        cookie_regex = r'document\.cookie="([^;]+)'
        match = re.search(cookie_regex, initial_response.body.script.text)

        if match:
            cookie = match.group(1)
            cookie = cookie.strip().split("=")
        else:
            return initial_response

        # Extract the link
        link_regex = r'location\.href="([^"]+)"'
        match = re.search(link_regex, initial_response.body.script.text)

        if match:
            link = match.group(1)  # Extracted link
        else:
            return initial_response

        # Perform the request
        async with session.get(
            link,
            timeout=timeout,
            cookies={cookie[0]: cookie[1]},
        ) as response:
            response.raise_for_status()
            parsed_response = BeautifulSoup(await response.text(), "html.parser")

    return parsed_response


async def fetch_page(url: str, timeout: int = 10) -> BeautifulSoup:
    """Fetch the HTML content of a webpage."""
    # Create a new session per worker
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                parsed_response = BeautifulSoup(await response.text(), "html.parser")

            return await check_real_page(parsed_response, session, timeout)

        except (aiohttp.ClientError, asyncio.TimeoutError) as req_err:
            message = f"Error fetching page {url}: {req_err}"
            logging.exception(message)
            sys.exit(1)


def validate_chapter_range(
    start_chapter: int, end_chapter: int, num_chapters: int,
) -> tuple:
    """Validate the chapter range provided by the user."""

    def log_and_exit(message: str) -> None:
        logging.warning(message)
        sys.exit(1)

    if start_chapter:
        if start_chapter < 1 or start_chapter > num_chapters:
            log_and_exit(f"Start chapter must be between 1 and {num_chapters}.")

    if start_chapter and end_chapter:
        if start_chapter > end_chapter:
            log_and_exit("Start chapter cannot be greater than end episode.")

        if start_chapter > num_chapters:
            log_and_exit(f"End chapter must be between 1 and {num_chapters}.")

    start_index = start_chapter - 1 if start_chapter else 0
    end_index = end_chapter if end_chapter else num_chapters
    return start_index, end_index


def clear_terminal() -> None:
    """Clear the terminal screen based on the operating system."""
    commands = {
        "nt": "cls",       # Windows
        "posix": "clear",  # macOS and Linux
    }

    command = commands.get(os.name)
    if command:
        os.system(command)  # noqa: S605
