"""Module that provides functionality to generate comic files from images.

It processes directories recursively and generates comic files such as PDF and CBZ from
image collections found in each directory.
"""

import logging
import os
import re
import zipfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rich.progress import Progress

from .config import DOWNLOAD_FOLDER, IMAGE_FORMATS_FOR_PDF


def count_subsubfolders(main_folder: str) -> int:
    """Count the total number of subsubfolders in a given main folder."""
    total_subsubfolders = 0
    for root, dirs, _ in os.walk(main_folder):
        if root.count(os.sep) == main_folder.count(os.sep) + 1:
            total_subsubfolders += len(dirs)

    return total_subsubfolders


def convert2cbz(image_paths: list[Path], output_cbz_path: str) -> None:
    """Convert a list of image paths into a CBZ archive."""
    if not image_paths:
        logging.warning("No images provided to convert into CBZ")
        return

    output_cbz = Path(output_cbz_path)

    with zipfile.ZipFile(
        output_cbz,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as cbz_file:
        for image_path in image_paths:
            cbz_file.write(
                image_path,
                arcname=image_path.name,
            )

    logging.info("CBZ created: %s", output_cbz)


def convert2pdf(image_paths: list, output_pdf_path: str) -> None:
    """Convert a list of image paths into a PDF file."""
    if not image_paths:
        logging.warning("No images provided to convert into PDF")
        return

    pics = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            pics.append(img.convert("RGB"))

        except UnidentifiedImageError:
            logging.warning("Unrecognized image format: %s", img_path)

        except OSError as os_err:
            logging.warning("OS error when processing %s: %s", img_path, os_err)

    if pics:
        output_pdf = Path(output_pdf_path)
        pics[0].save(
            output_pdf,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=pics[1:],
        )
        logging.info("PDF created: %s", output_pdf)

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
    """Collect and sort all supported image paths from a folder."""
    # Use rglob to recursively search for all images with valid extensions
    image_paths = [
        file for file in Path(folder).rglob("*")
        if file.suffix.lower() in IMAGE_FORMATS_FOR_PDF
    ]

    image_paths.sort(
        key=lambda path: (extract_number(str(path.parent)), extract_number(path.name)),
    )
    return image_paths


def generate_file_from_folder(folder_path: str, *, output_format: str) -> None:
    """Generate a comic file from all images contained in a folder.

    The output format can be either PDF or CBZ.
    """
    image_paths = collect_image_paths(folder_path)

    if not image_paths:
        return

    folder = Path(folder_path)
    output_path = Path.cwd() / folder.parent / f"{folder.name}.{output_format}"

    converters = {
        "pdf": convert2pdf,
        "cbz": convert2cbz,
    }

    converter = converters.get(output_format.lower())

    if converter is None:
        log_message = f"Unsupported output format: {output_format}"
        raise ValueError(log_message)

    converter(image_paths, str(output_path))


def generate_comic_files(
    parent_folder: str,
    job_progress: Progress,
    *,
    is_module: bool = False,
    single_file: bool = False,
    output_format: str = "pdf",
) -> None:
    """Generate comic files from images in each subfolder of the parent folder."""
    num_folders = (
        count_subsubfolders(DOWNLOAD_FOLDER)
        if is_module
        else get_num_folders(parent_folder)
    )
    task = job_progress.add_task(
        f"[cyan]Generating {output_format.upper()} files",
        total=num_folders,
    )

    if single_file:
        generate_file_from_folder(parent_folder, output_format=output_format)
        job_progress.advance(task, num_folders)

    else:
        for path, _, _ in os.walk(parent_folder):
            manga_name = Path(path).parent.name
            if manga_name != DOWNLOAD_FOLDER:
                generate_file_from_folder(path, output_format=output_format)
                job_progress.advance(task)


def main() -> None:
    """Generate comic files from images in the download folder."""
    with Progress() as job_progress:
        generate_comic_files(f"{DOWNLOAD_FOLDER}/", job_progress, is_module=True)


if __name__ == "__main__":
    main()
