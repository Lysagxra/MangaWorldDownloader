"""Module that provides functionality to convert image files to PDF files.

It processes directories recursively and generates PDFs for each directory's images.
"""

import logging
import os
from pathlib import Path

from PIL import Image
from rich.progress import Progress

from .config import DOWNLOAD_FOLDER


def count_subsubfolders(main_folder: str) -> int:
    """Count the total number of subsubfolders in a given main folder."""
    total_subsubfolders = 0
    for root, dirs, _ in os.walk(main_folder):
        if root.count(os.sep) == main_folder.count(os.sep) + 1:
            total_subsubfolders += len(dirs)

    return total_subsubfolders


def convert2pdf(main_path: str, output_path: str, pdf_name: str) -> None:
    """Convert all image files in the specified directory to a single PDF file."""
    filenames = next(os.walk(main_path), (None, None, []))[2]
    filenames.sort(key=lambda filename: int("".join(filter(str.isdigit, filename))))

    if not filenames:
        message = f"No images found in {main_path}."
        logging.error(message)
        return

    path_to_pdf = Path.cwd() / Path(output_path) / f"{pdf_name}.pdf"
    pics = [Image.open(Path(main_path) / filename) for filename in filenames]

    if pics:
        pics[0].save(
            path_to_pdf,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=pics[1:],
        )
    else:
        message = f"No valid images to convert in {main_path}."
        logging.error(message)


def get_num_folders(current_directory: str) -> int:
    """Count the number of directories in the specified directory."""
    return sum(1 for entry in os.scandir(current_directory) if entry.is_dir())


def generate_pdf_files(
    parent_folder: str,
    job_progress: Progress,
    *,
    is_module: bool = False,
) -> None:
    """Generate PDF files from images in each subfolder of the parent folder."""
    num_folders = (
        count_subsubfolders(DOWNLOAD_FOLDER)
        if is_module
        else get_num_folders(parent_folder)
    )
    task = job_progress.add_task("[cyan]Generating PDFs", total=num_folders)

    for path, _, _ in os.walk(parent_folder):
        manga_name = Path(path).parent.name

        if manga_name != DOWNLOAD_FOLDER:
            filename = Path(path).name
            pdf_path = Path(path).parent
            convert2pdf(path, pdf_path, filename)
            job_progress.advance(task)


def main() -> None:
    """Generate PDFs from images in a specific folder."""
    with Progress() as job_progress:
        generate_pdf_files(f"{DOWNLOAD_FOLDER}/", job_progress, is_module=True)


if __name__ == "__main__":
    main()
