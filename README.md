# FTP Batch Downloader

FTP Batch Downloader is a cross-platform desktop application built with Python and PyQt5 that allows you to browse and batch download files from both HTTP and FTP servers.

## Features

* **Modern GUI:** A clean and responsive user interface built with PyQt5.
* **Batch Downloading:** Download multiple files and entire folders concurrently.
* **HTTP and FTP Support:** Browse and download from both HTTP and FTP directories.
* **Concurrent Operations:** User-configurable number of parallel downloads and directory listings.
* **Download Control:** Pause, resume, and cancel downloads (both globally and individually).
* **Accurate Progress Tracking:** View overall progress based on total download size (bytes) and per-file progress.
* **Directory Tree View:** Recursively lists files and folders from the server.
* **User-Friendly:** Supports drag-and-drop for URLs, provides clear notifications, and includes a centralized error log.
* **Configurable:** Performance-related parameters can be configured via a JSON file.
* **Robust:** Gracefully handles network errors and logs all issues to a file.

## Setup and Installation

1.  **Create the directory structure** and save each file from this chat into its correct location.
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python main.py
    ```
