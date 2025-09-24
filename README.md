# MangaWorld Downloader

> A Python-based tool for downloading and organizing manga content from MangaWorld.

![Demo](https://github.com/Lysagxra/MangaWorldDownloader/blob/a8dca98cb0fece9d7eab672ea30fea5ab50bcf34/assets/demo.gif)

## Features

- Downloads multiple chapters concurrently.
- Supports [batch downloading](https://github.com/Lysagxra/MangaWorldDownloader?tab=readme-ov-file#batch-download) via a list of URLs.
- Supports downloading a [specified range of chapters](https://github.com/Lysagxra/MangaWorldDownloader?tab=readme-ov-file#single-manga-download).
- Supports the [generation of PDF files](https://github.com/Lysagxra/MangaWorldDownloader?tab=readme-ov-file#pdf-generation) from the downloaded chapters.
- Track and display download progress.
- Organize and format manga chapters.

## Dependencies

- Python 3
- `aiohttp` - for asynchronous HTTP requests
- `requests` - for HTTP requests
- `beautifulsoup4` (bs4) - for HTML parsing
- `Pillow` - for image processing
- `rich` - for progress display in terminal

<details>

<summary>Show directory structure</summary>

```
project-root/
├── helpers/
│ ├── config.py          # Manages constants and settings used across the project
│ ├── download_utils.py  # Utilities for managing the download process
│ ├── file_utils.py      # Utilities for managing file operations
│ ├── format_utils.py    # Functions for formatting manga data
│ ├── general_utils.py   # Miscellaneous utility functions
│ ├── pdf_generator.py   # Tools for generating PDF files from manga chapters
│ └── progress_utils.py  # Utilities for tracking and displaying progress
├── manga_downloader.py  # Core functionality for managing manga downloads
├── main.py              # Main script to run the downloader
└── URLs.txt             # Text file containing manga URLs
```

</details>

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Lysagxra/MangaWorldDownloader.git
```
   
2. Navigate to the project directory: 

```bash
cd MangaWorldDownloader
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Single Manga Download

To download a single manga, you can use the `manga_downloader.py` script.

### Usage

Run the script followed by the manga URL you want to download:

```bash
python3 manga_downloader.py <manga_url> [--start <start_chapter>] [--end <end_chapter>]
```

- `<manga_url>`: The URL of the manga.
- `--start <start_chapter>`: The starting chapter number (optional).
- `--end <end_chapter>`: The ending chapter number (optional).

### Example

```bash
python3 manga_downloader.py https://www.mangaworld.ac/manga/2754/sayonara-eri
```

### Examples

To download all chapters:
```bash
python3 manga_downloader.py https://www.mangaworld.cx/manga/2472/soloist-of-the-prison
```

To download a specific range of chapters (e.g., chapters 5 to 10):
```bash
python3 manga_downloader.py https://www.mangaworld.cx/manga/2472/soloist-of-the-prison --start 5 --end 10
```

To download chapters starting from a specific chapter:
```bash
python3 manga_downloader.py https://www.mangaworld.cx/manga/2472/soloist-of-the-prison --start 5
```
In this case, the script will download all chapters starting from the `--start` chapter to the last chapter.

To download chapters up to a certain chapter:
```bash
python3 manga_downloader.py https://www.mangaworld.cx/manga/2472/soloist-of-the-prison --end 10
```
In this case, the script will download all chapters starting from the first chapter to the `--end` chapter.

## Batch Download

### Usage

1. Create a `URLs.txt` file in the project root and list the manga URLs you want to download.

- Example of `URLs.txt`:

```
https://www.mangaworld.ac/manga/2754/sayonara-eri
https://www.mangaworld.ac/manga/2378/bibliomania
https://www.mangaworld.ac/manga/2472/soloist-of-the-prison
```

- Ensure that each URL is on its own line without any extra spaces.
- You can add as many URLs as you need, following the same format.

2. Run the main script via the command line:

```bash
python3 main.py
```

The downloaded files will be saved in the `Downloads` directory.

## PDF Generation

This tool includes a feature to generate PDFs from downloaded manga chapters. You can use the `--pdf` argument from the command line to enable this functionality.

### Usage

To generate PDFs for the downloaded manga, run the following command:

```bash
python3 main.py --pdf
```

This will create PDF files for each chapter and save them in the specified output directory. The generated PDFs maintain the original quality of the downloaded images and are optimized for readability.

## Logging

The application logs any issues encountered during the download process in a file named `session.log`. Check this file for any URLs that may have been blocked or had errors.
