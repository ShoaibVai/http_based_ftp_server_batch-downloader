1# FTP Batch Downloader

FTP Batch Downloader is a cross-platform desktop application built with Python and PyQt5 that allows you to browse and batch download files from both HTTP and FTP servers. It features a modern GUI, robust error handling, and flexible configuration.

## Features

* **Modern GUI:** Clean, responsive interface built with PyQt5.
* **Batch Downloading:** Download multiple files and entire folders concurrently.
* **HTTP and FTP Support:** Browse and download from both HTTP and FTP directories.
* **Concurrent Operations:** User-configurable number of parallel downloads and directory listings.
* **Download Control:** Pause, resume, and cancel downloads (globally and individually).
* **Accurate Progress Tracking:** View overall and per-file progress, including total bytes.
* **Directory Tree View:** Recursively lists files and folders from the server.
* **User-Friendly:** Drag-and-drop for URLs, clear notifications, and a centralized error log.
* **Configurable:** Performance and behavior parameters are set via a JSON config file.
* **Robust:** Handles network errors gracefully and logs all issues to a file.

## Project Structure

- `main.py`: Entry point. Initializes the application and main window.
- `ui/main_window.py`: Implements the main PyQt5 window, including the UI, event handling, and user interactions.
- `core/downloader.py`: Contains the download manager and worker threads for HTTP/FTP downloads, with support for pause/resume/cancel and progress reporting.
- `core/lister.py`: Implements directory listing for HTTP/FTP servers, supporting recursive listing and emitting results to the UI.
- `core/utils.py`: Utility threads, including file size calculation for download progress.
- `config/manager.py`: Loads, saves, and manages application settings from `config.json`.
- `utils/logger.py`: Sets up centralized logging to both file and console.
- `config.json`: Stores user and app configuration (download path, concurrency, timeouts, etc).
- `logs/app.log`: Application log file (auto-created).

## Configuration

The application uses `config.json` for settings such as:
- `default_download_path`: Default folder for downloads
- `max_concurrent_downloads`: Number of parallel downloads
- `max_concurrent_listings`: Number of parallel directory listings
- `listing_depth`: Recursion depth for directory listings
- `chunk_size`: Download chunk size (bytes)
- `request_timeout`: Timeout for network requests (seconds)
- `retry_attempts`: Number of retry attempts for failed downloads
- `retry_delay`: Delay between retries (seconds)

You can edit `config.json` manually or change some settings via the UI (e.g., download path, concurrency).

## Logging

All errors and important events are logged to `logs/app.log`. You can view the log from the application ("View Log" action) or open the file directly.

## Setup and Installation

1. **Create the directory structure** and save each file from this repository into its correct location.
2. **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```
3. **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Run the application:**
    ```bash
    python main.py
    ```

## Usage

- Enter or drag-and-drop an HTTP/FTP URL into the input field.
- Click "Fetch" to list files and folders.
- Select files/folders to download (checkboxes).
- Choose the download directory (default is set in config or via the UI).
- Click "Download" to start batch downloading.
- Use the toolbar to pause, resume, or cancel downloads. View logs for errors.

## Requirements

- Python 3.7+
- PyQt5
- requests
- beautifulsoup4

See `requirements.txt` for exact versions.

---

For questions or issues, please check the log file or open an issue.
