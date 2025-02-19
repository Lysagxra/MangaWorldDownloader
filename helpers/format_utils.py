"""Module for parsing a URL to extract the manga ID and manga name."""

import logging
import re
import sys
from urllib.parse import urlparse


def conv2uppercase(string: str) -> str:
    """Convert the first letter of each word in the string to uppercase."""
    return string.group(1) + string.group(2).upper()


def extract_manga_info(url: str) -> tuple:
    """Extract manga ID and manga name from a given URL."""
    parsed_url = urlparse(url)

    try:
        manga_id = parsed_url.path.split("/")[-2]
        manga_name = parsed_url.path.split("/")[-1]
        formatted_manga_name = re.sub(
            r"(^|\s)(\S)",
            conv2uppercase,
            manga_name.replace("-", " "),
        )
        return manga_id, formatted_manga_name

    except IndexError:
        logging.exception("Invalid URL format.")
        sys.exit(1)
