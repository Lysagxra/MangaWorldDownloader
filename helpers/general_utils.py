"""
This module provides utilities for fetching web pages, managing directories, 
and clearing the terminal screen. It includes functions to handle common tasks 
such as sending HTTP requests, parsing HTML, creating download directories, and 
clearing the terminal, making it reusable across projects.
"""

import asyncio
import os
import re
import sys
from pathlib import Path

import aiohttp
import requests
from bs4 import BeautifulSoup

DOWNLOAD_FOLDER = "Downloads"

# def check_real_page(res, session, timeout=10, is_async=False):
#     if "document.cookie" in res.body.script.text:
#             print("Found not final page, trying to fetch real one again...")

#             cookie_regex = r'document\.cookie="([^;]+)'
#             match = re.search(cookie_regex, res.body.script.text)

#             if match:
#                 cookie = match.group(1)  # Extracted cookie value
#                 print("Extracted Cookie:", cookie)
#                 cookie = cookie.strip().split("=")
#             else:
#                 print("No cookie found")
#                 return res
            
#             # Regex to extract the URL from location.href
#             link_regex = r'location\.href="([^"]+)"'
#             match = re.search(link_regex, res.body.script.text)

#             if match:
#                 link = match.group(1)  # Extracted link
#                 print("Extracted Link:", link)
#             else:
#                 print("No link found")
#                 return res

#             response = session.get(link, timeout=timeout, cookies={cookie[0]: cookie[1]})
#             response.raise_for_status()
#             res =  BeautifulSoup(response.text, 'html.parser')

#     return res

async def check_real_page(res, session, timeout=10):
    if "document.cookie" in res.body.script.text:
        # print("Found not final page, trying to fetch real one again...")

        # Extract the cookie
        cookie_regex = r'document\.cookie="([^;]+)'
        match = re.search(cookie_regex, res.body.script.text)

        if match:
            cookie = match.group(1)  # Extracted cookie value
            # print("Extracted Cookie:", cookie)
            cookie = cookie.strip().split("=")
        else:
            # print("No cookie found")
            return res

        # Extract the link
        link_regex = r'location\.href="([^"]+)"'
        match = re.search(link_regex, res.body.script.text)

        if match:
            link = match.group(1)  # Extracted link
            # print("Extracted Link:", link)
        else:
            print("No link found")
            return res

        # Perform the request
        async with session.get(link, timeout=timeout, cookies={cookie[0]: cookie[1]}) as response:
            response.raise_for_status()

            res = BeautifulSoup(await response.text(), 'html.parser')

    return res

async def fetch_page(url, timeout=10):
    """
    Fetches the HTML content of a webpage and parses it into a BeautifulSoup
    object.

    Args:
        url (str): The URL of the webpage to fetch.
        timeout (int, optional): The maximum time (in seconds) to wait for a
                                 response. Defaults to 10.

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the HTML content of
                       the page.

    Raises:
        SystemExit: If an error occurs during the HTTP request, the program
                    exits after printing the error message.
    """
    # Create a new session per worker
    async with aiohttp.ClientSession() as session:

        try:
            async with session.get(url, timeout=timeout) as response:
                res =  BeautifulSoup(await response.text(), 'html.parser')
            res = await check_real_page(res, session, timeout)

            return res

        except (aiohttp.ClientError, asyncio.TimeoutError) as req_err:
            print(f"Error fetching page {url}: {req_err}")
            sys.exit(1)

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
