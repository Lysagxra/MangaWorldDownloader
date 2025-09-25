"""Module that provides functionality to convert image files to PDF files.

It processes directories recursively and generates PDFs for each directory's images.
"""

import logging
import os
import re
from pathlib import Path

from PIL import Image
from rich.progress import Progress

from .config import DOWNLOAD_FOLDER, IMAGE_FORMATS_FOR_PDF


def count_subsubfolders(main_folder: str) -> int:
    """Count the total number of subsubfolders in a given main folder."""
    total_subsubfolders = 0
    for root, dirs, _ in os.walk(main_folder):
        if root.count(os.sep) == main_folder.count(os.sep) + 1:
            total_subsubfolders += len(dirs)

    return total_subsubfolders


def convert2pdf(image_paths: list, output_pdf_path: str) -> None:
    """Convert a list of image paths to a single PDF file."""
    if not image_paths:
        logging.error("No images provided to convert.")
        return

    pics = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            pics.append(img.convert("RGB"))

        except Exception as e:
            log_message = f"Could not open image {img_path}: {e}"
            logging.warning(log_message)

    if pics:
        output_pdf = Path(output_pdf_path)
        pics[0].save(
            output_pdf,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=pics[1:],
        )
        log_message = f"PDF created: {output_pdf}"
        logging.info(log_message)

    else:
        logging.error("No valid images to convert.")


def get_num_folders(current_directory: str) -> int:
    """Count the number of directories in the specified directory."""
    return sum(1 for entry in os.scandir(current_directory) if entry.is_dir())

def extract_number(file_path: str) -> tuple:
    """Extract the number of the images by path name and file name."""
    nums = re.findall(r"\d+", file_path)
    return tuple(int(n) for n in nums) if nums else (0,)

def collect_image_paths(folder: str) -> list[str]:
    """Collect all image paths from a folder."""
    # Use rglob to recursively search for all images with valid extensions
    image_paths = [
        file for file in Path(folder).rglob("*")
        if file.suffix.lower() in IMAGE_FORMATS_FOR_PDF
    ]

    image_paths.sort(
        key=lambda path: (extract_number(str(path.parent)), extract_number(path.name)),
    )
    return image_paths

def generate_pdf_files(
    parent_folder: str,
    job_progress: Progress,
    *,
    is_module: bool = False,
    single_pdf: bool = False,
) -> None:
    """Generate PDF files from images in each subfolder of the parent folder."""
    num_folders = (
        count_subsubfolders(DOWNLOAD_FOLDER)
        if is_module
        else get_num_folders(parent_folder)
    )
    task = job_progress.add_task("[cyan]Generating PDFs", total=num_folders)

    if single_pdf:
        image_paths = collect_image_paths(parent_folder)

        if image_paths:
            pdf_name = Path(parent_folder).name
            pdf_path = Path(parent_folder).parent
            output_pdf = Path.cwd() / pdf_path / f"{pdf_name}.pdf"
            convert2pdf(image_paths, str(output_pdf))

        job_progress.advance(task, num_folders)

    else:
        for path, _, _ in os.walk(parent_folder):
            manga_name = Path(path).parent.name
            if manga_name != DOWNLOAD_FOLDER:
                image_paths = collect_image_paths(path)

                if image_paths:
                    pdf_name = Path(path).name
                    pdf_path = Path(path).parent
                    output_pdf = Path.cwd() / pdf_path / f"{pdf_name}.pdf"
                    convert2pdf(image_paths, str(output_pdf))

                job_progress.advance(task)


def main() -> None:
    """Generate PDFs from images in a specific folder."""
    with Progress() as job_progress:
        generate_pdf_files(f"{DOWNLOAD_FOLDER}/", job_progress, is_module=True)


if __name__ == "__main__":
    main()
