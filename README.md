# FTP Batch Downloader

A modern, colorful, and highly-configurable batch downloader for HTTP/FTP servers with a beautiful PyQt5 GUI.

---

## Features

- **Modern, Colorful UI**: Multiple themes (Colorful, Dark, Light, Solarized, Classic) with real-time switching.
- **Tabbed Interface**: Downloader, Downloads, and Settings tabs for clear workflow.
- **Batch Downloading**: Download multiple files and entire folders concurrently.
- **HTTP & FTP Support**: Recursively list and download from both HTTP and FTP servers.
- **Smart Directory Tree**: Hierarchical tree view for browsing and selecting files/folders.
- **Download Manager**: Pause, resume, cancel, retry (per-file and global), with real-time progress and ETA.
- **Disk Space Check**: Warns if there’s not enough space before starting a download.
- **Percent-Decoding**: Local folders/files use spaces instead of %20, matching server names.
- **Log Viewer**: View logs in-app with themed window.
- **Settings Tab**: Change concurrency, listing depth, and theme on the fly.
- **Robust Error Handling**: Retries, error reporting, and persistent download state.
- **No venv Required**: Just install dependencies and run.

---

## Project Structure

- `main.py` — Entry point, launches the PyQt5 app.
- `ui/main_window.py` — Main window, tab logic, and all UI/UX.
- `ui/downloads_tab.py` — Downloads tab: progress, ETA, actions, sub-tabs.
- `ui/settings_tab.py` — Settings tab: concurrency, depth, theme, log viewer.
- `core/downloader.py` — Download manager and worker threads (pause/resume/cancel/retry, percent-decode, disk check).
- `core/lister.py` — Directory lister for HTTP/FTP, recursive.
- `core/utils.py` — Size calculator and helpers.
- `config/manager.py` — Loads/saves settings from `config.json`.
- `logs/app.log` — Application log file.
- `requirements.txt` — Python dependencies.

---

## Installation

1. **Clone or download this repository.**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python main.py
   ```

---

## Usage

- **Downloader Tab**: Enter or drag-and-drop an HTTP/FTP URL, click Fetch, select files/folders, choose download directory, and click Download.
- **Downloads Tab**: Monitor all downloads (Active, Completed, Failed, Canceled), see real-time progress and ETA, pause/resume/cancel/retry, open completed files in Explorer.
- **Settings Tab**: Change concurrent downloads, listing depth, and theme. View logs.
- **Themes**: Instantly switch between Colorful, Dark, Light, Solarized, and Classic.
- **Disk Space**: Get warned if you don’t have enough space for a file before download starts.
- **Percent-Decoding**: Local folders/files use spaces (not %20) for readability.

---

## Configuration

- All settings are stored in `config.json` and can be changed in the Settings tab.
- Key options:
  - `default_download_path`: Default folder for downloads
  - `max_concurrent_downloads`: Number of parallel downloads
  - `listing_depth`: Recursion depth for directory listings
  - `theme_name`: UI theme

---

## Requirements

- Python 3.7+
- PyQt5
- PyQtWebEngine (if you use browser features)
- requests
- beautifulsoup4

See `requirements.txt` for exact versions.

---

## Notes

- No virtual environment (venv) is required. Just install dependencies globally or in your preferred environment.
- All folders/files created locally will use spaces instead of percent-encoded names.
- The app is robust for extremely large files and large batches.

---

## License

MIT License (see LICENSE file) 