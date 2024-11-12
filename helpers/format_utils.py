"""
This module provides functionality for parsing a URL to extract the manga ID
and manga name, then formatting the manga name by capitalizing the first letter
of each word. The module includes the following functions:
"""

import re
from urllib.parse import urlparse

def conv2uppercase(string):
    """
    Converts the first letter of each word in the string to uppercase.

    Args:
        string (re.Match): A regex match object.

    Returns:
        str: The string with the first letter of each word in uppercase.
    """
    return string.group(1) + string.group(2).upper()

def extract_manga_info(url):
    """
    Extract manga ID and manga name from a given URL.

    Args:
        url (str): The URL from which to extract manga information.

    Returns:
        tuple: A tuple containing:
            - manga_id (str): The extracted manga ID, which is the
                              second-to-last segment of the URL path.
            - formatted_manga_name (str): The formatted manga name, with
                                          hyphens replaced by spaces and each
                                          word capitalized.

    Raises:
        ValueError: If the URL is not in the expected format and cannot be
                    parsed properly, an exception is raised.
        IndexError: A specific error is caught and re-raised as a `ValueError`
                    if the URL path does not contain the expected segments.
    """
    try:
        parsed_url = urlparse(url)
        manga_id = parsed_url.path.split('/')[-2]
        manga_name = parsed_url.path.split('/')[-1]
        formatted_manga_name = re.sub(
            r"(^|\s)(\S)",
            conv2uppercase,
            manga_name.replace('-', ' ')
        )
        return manga_id, formatted_manga_name

    except IndexError as indx_err:
        raise ValueError("Invalid URL format.") from indx_err
