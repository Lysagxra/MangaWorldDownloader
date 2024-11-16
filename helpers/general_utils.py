"""
This module provides utilities for fetching web pages, managing directories, 
and clearing the terminal screen. It includes functions to handle common tasks 
such as sending HTTP requests, parsing HTML, creating download directories, and 
clearing the terminal, making it reusable across projects.
"""

import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DOWNLOAD_FOLDER = "Downloads"

def fetch_page(url, timeout=10):
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
    session = requests.Session()

    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    except requests.RequestException as req_err:
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
