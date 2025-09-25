"""Configuration module for managing constants used across the project.

These configurations aim to improve modularity and readability by consolidating settings
into a single location.
"""

from argparse import ArgumentParser, Namespace

import requests
from PIL import ImageFile

# ============================
# Paths and Files
# ============================
DOWNLOAD_FOLDER = "Downloads"  # The folder where downloaded files will be stored.
URLS_FILE = "URLs.txt"         # The file containing the list of URLs to process.
SESSION_LOG = "session.log"    # The file used to log errors.

# ============================
# Regex Patterns
# ============================
FIRST_PAGE_SUFFIX_REGEX = r"1\.(png|gif|jpg)$"
MANGA_TYPE_REGEX = r'"typeT":\s*"([^"]*)"'
COOKIE_REGEX = r'document\.cookie="([^;]+)'
LINK_REGEX = r'location\.href="([^"]+)"'

# ============================
# Download Settings
# ============================
TASK_COLOR = "cyan"     # Color used for task-related output in the terminal.
MAX_WORKERS = 4         # Maximum number of concurrent workers.
CHUNK_SIZE = 16 * 1024  # Size of data chunks (bytes) to be processed at a time.
TIMEOUT = 20            # Timeout value (seconds) for HTTP requests.
MAX_RETRIES = 30        # Maximum number of retries for failed HTTP requests.
WAIT_TIME_RETRIES = 10  # Number of seconds to wait between retries.
NUM_URL_PATH_PARTS = 3  # Number of path segments to validate the initial URL.

# Manga types that behave like classic Manga (same pagination).
MANGA_LIKE = {"Manga", "Oneshot", "Doujinshi", "Manhua"}

# ============================
# Image Download Settings
# ============================
# List of supported image extensions for download.
PAGE_EXTENSIONS = [".jpg", ".png", ".gif", ".webp"]

# List of supported image extensions for PDF generation.
IMAGE_FORMATS_FOR_PDF = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Allow loading of truncated images.
ImageFile.LOAD_TRUNCATED_IMAGES = True

# ============================
# HTTP / Network
# ============================
# Create a new session object to persist across requests
SESSION = requests.Session()

# HTTP status codes
HTTP_STATUS_OK = 200

# Headers used for general HTTP requests, mimicking a browser user agent
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"
    ),
    "Connection": "keep-alive",
}

# ============================
# Argument Parsing
# ============================
def add_common_arguments(parser: ArgumentParser) -> None:
    """Add arguments shared across parsers."""
    parser.add_argument(
        "-p",
        "--pdf",
        action="store_true",
        help="Generate PDF after downloading the manga.",
    )
    parser.add_argument(
        "-v",
        "--volume",
        action="store_true",
        help="Specify a volume to download (use 'all' to get all volumes).",
    )


def setup_parser(
        *, include_url: bool = False, include_filters: bool = False,
    ) -> ArgumentParser:
    """Set up parser with optional argument groups."""
    parser = ArgumentParser(description="Command-line arguments.")

    if include_url:
        parser.add_argument("url", type=str, help="The URL to process")

    if include_filters:
        parser.add_argument(
            "--start",
            type=int,
            default=None,
            help="The starting chapter number.",
        )
        parser.add_argument(
            "--end",
            type=int,
            default=None,
            help="The ending chapter number.",
        )

    add_common_arguments(parser)
    return parser


def parse_arguments(*, common_only: bool = False) -> Namespace:
    """Full argument parser (including URL, filters, and common)."""
    parser = (
        setup_parser() if common_only
        else setup_parser(include_url=True, include_filters=True)
    )
    return parser.parse_args()
