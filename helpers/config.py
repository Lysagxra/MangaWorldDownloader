"""
Centralized configuration module for managing constants and settings used
across the project. These configurations aim to improve modularity and
readability by consolidating settings into a single location.
"""

DOWNLOAD_FOLDER = "Downloads"  # The folder where downloaded files will be
                               # stored.
URLS_FILE = "URLs.txt"         # The name of the file containing the list of
                               # URLs to process.

MAX_WORKERS = 5         # Maximum number of concurrent workers.
TASK_COLOR = "cyan"     # Color used for task-related output in the terminal.
CHUNK_SIZE = 16 * 1024  # Size of data chunks (bytes) to be processed at a time.
TIMEOUT = 20            # Timeout value (in seconds) for HTTP requests.
MAX_RETRIES = 30         # Maximum number of retries for failed HTTP requests.
SECONDS = 10            # Number of seconds to wait between retries.

# Headers used for general HTTP requests, mimicking a browser user agent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) "
        "Gecko/20100101 Firefox/117.0"
    ),
    "Connection": "keep-alive",
}
