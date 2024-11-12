"""
This module provides functionality to convert image files within directories to
PDF files. It processes directories recursively and generates PDFs for each
directory's images.
"""

import os

from PIL import Image
from rich.progress import Progress

DOWNLOAD_FOLDER = "Downloads"
#FOLDER_CONTENT = list(os.walk(DOWNLOAD_FOLDER))
#NUM_TASKS = len(FOLDER_CONTENT) - len(FOLDER_CONTENT[0][1]) - 1

def count_subsubfolders(main_folder):
    """
    Count the total number of subsubfolders (i.e., directories inside
    second-level subfolders) in a given main folder.

    Args:
        main_folder (str): The path to the main folder (root directory) where
                           the subfolders and their subsubfolders will be
                           counted.

    Returns:
        int: The total number of subsubfolders in all direct subfolders of the
             `main_folder`.
    """
    total_subsubfolders = 0
    for root, dirs, _ in os.walk(main_folder):
        if root.count(os.sep) == main_folder.count(os.sep) + 1:
            total_subsubfolders += len(dirs)

    return total_subsubfolders

def convert2pdf(main_path, output_path, pdf_name):
    """
    Convert all image files in the specified directory to a single PDF file.

    Args:
        main_path (str): The path to the directory containing the image files
                         to be converted into a PDF.
        output_path (str): The path where the resulting PDF file will be saved.
        pdf_name (str): The name of the resulting PDF file (without extension).
    """
    filenames = next(os.walk(main_path), (None, None, []))[2]
    filenames.sort(
        key=lambda filename: int(''.join(filter(str.isdigit, filename)))
    )

    path_to_pdf = os.path.join(os.getcwd(), output_path, f"{pdf_name}.pdf")
    pics = [
        Image.open(os.path.join(main_path, filename))
        for filename in filenames
    ]

    pics[0].save(
        path_to_pdf, "PDF", resolution=100.0, save_all=True,
        append_images=pics[1:]
    )

def get_num_folders(current_directory):
    """
    Count the number of directories in the specified directory.

    Args:
        current_directory (str): The path to the directory where folders
                                 should be counted.

    Returns:
        int: The number of directories within the specified directory.
    """
    return sum(1 for entry in os.scandir(current_directory) if entry.is_dir())

def generate_pdf_files(parent_folder, job_progress, is_module=False):
    """
    Generate PDF files from images in each subfolder of the parent folder.

    Args:
        parent_folder (str): The path to the parent directory containing
                             subdirectories with images to be converted
                             into PDFs.
        job_progress (Progress): The progress tracker object to show task
                                 progress.
        is_module (bool): If `True`, the number of folders to process will be
                          set to `NUM_TASKS`. If `False`, the function will
                          count the folders in `parent_folder`.
    """
    num_folders = (
        count_subsubfolders(DOWNLOAD_FOLDER) if is_module
        else get_num_folders(parent_folder)
    )
    task = job_progress.add_task("[cyan]Generating PDFs", total=num_folders)

    for (path, _, _) in os.walk(parent_folder):
        manga_name = os.path.basename(os.path.dirname(path))

        if manga_name != DOWNLOAD_FOLDER:
            filename = os.path.basename(path)
            pdf_path = os.path.dirname(path)
            convert2pdf(path, pdf_path, filename)
            job_progress.advance(task)

def main():
    """
    Entry point for generating PDFs from images in a specific folder.
    """
    with Progress() as job_progress:
        generate_pdf_files(f"{DOWNLOAD_FOLDER}/", job_progress, is_module=True)

if __name__ == '__main__':
    main()
