"""Utility functions for file input and output operations.

It includes methods to read the contents of a file and to write content to a file, with
optional support for clearing the file.
"""

from pathlib import Path

from .config import DOWNLOAD_FOLDER


def read_file(filename: str) -> list[str]:
    """Read the contents of a file and returns a list of its lines."""
    with Path(filename).open("r", encoding="utf-8") as file:
        return file.read().splitlines()


def write_file(filename: str, mode: str = "w", content: str = "") -> None:
    """Write content to a specified file.

    If content is not provided, the file is cleared.
    """
    with Path(filename).open(mode, encoding="utf-8") as file:
        file.write(f"{content}\n")


def create_download_directory(manga_name: str, indx_chapter: int) -> str:
    """Create the directory structure for downloading a specific chapter of a manga."""
    manga_path = Path(DOWNLOAD_FOLDER) / manga_name
    manga_path.mkdir(parents=True, exist_ok=True)
    chapter_path = Path(manga_name) / f"Chapter {indx_chapter + 1}"
    download_path = Path(DOWNLOAD_FOLDER) / Path(chapter_path)
    download_path.mkdir(parents=True, exist_ok=True)
    return download_path
