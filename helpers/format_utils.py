"""Module for parsing a URL to extract the manga ID and manga name."""

import logging
import re
import sys
from urllib.parse import urlparse

from .config import NUM_URL_PATH_PARTS


def conv2uppercase(string: str) -> str:
    """Convert the first letter of each word in the string to uppercase."""
    return string.group(1) + string.group(2).upper()


def extract_manga_info(url: str) -> tuple:
    """Extract manga ID and manga name from a given URL."""
    parsed_url = urlparse(url)

    # Check if the URL path contains the expected structure
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) < NUM_URL_PATH_PARTS or path_parts[0] != "manga":
        logging.error("Invalid URL format: Expected '/manga/<id>/<name>'")
        return None

    manga_id = path_parts[1]
    manga_name = path_parts[2]

    try:
        formatted_manga_name = re.sub(
            r"(^|\s)(\S)",
            conv2uppercase,
            manga_name.replace("-", " "),
        )

    except IndexError:
        logging.exception("Invalid URL format.")
        sys.exit(1)

    return manga_id, formatted_manga_name
