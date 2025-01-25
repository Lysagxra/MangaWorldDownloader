# MangaWorld Downloader

> A Python-based tool for downloading and organizing manga content from MangaWorld.

![Demo](https://github.com/Lysagxra/MangaWorldDownloader/blob/8d3a28187c1b16f541ac6df1f6c82aa0b36e9725/misc/Demo.gif)

## Features

- Downloads multiple chapters concurrently.
- Supports [batch downloading](https://github.com/Lysagxra/MangaWorldDownloader?tab=readme-ov-file#batch-download) via a list of URLs.
- Supports the [generation of PDF files](https://github.com/Lysagxra/MangaWorldDownloader?tab=readme-ov-file#pdf-generation) from the downloaded chapters.
- Track and display download progress.
- Organize and format manga chapters efficiently.

## Dependencies

- Python 3
- `aiohttp` - for asynchronous HTTP requests
- `requests` - for HTTP requests
- `beautifulsoup4` (bs4) - for HTML parsing
- `Pillow` - for image processing
- `rich` - for progress display in terminal

## Directory Structure

```
project-root/
├── helpers/
│ ├── download_utils.py  # Manages constants and settings used across the project
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
python3 manga_downloader.py <manga_url>
```

### Example

```bash
python3 manga_downloader.py https://www.mangaworld.ac/manga/2754/sayonara-eri
```

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

This tool includes a feature to generate PDFs from downloaded manga chapters. You can use the `-p` argument from the command line to enable this functionality.

### Usage

To generate PDFs for the downloaded manga, run the following command:

```bash
python3 main.py -p
```

This will create PDF files for each chapter and save them in the specified output directory. The generated PDFs maintain the original quality of the downloaded images and are optimized for readability.
