# core/utils.py
# This module contains utility threads for tasks like calculating file sizes.

import logging
from urllib.parse import urlparse
import requests
from ftplib import FTP, error_perm
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class SizeCalculator(QThread):
    """A QThread to calculate the total size of a list of files from FTP or HTTP URLs."""
    finished = pyqtSignal(int, dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)

    def __init__(self, file_urls, config):
        super().__init__()
        self.file_urls = file_urls
        self.config = config
        self._is_running = True

    def run(self):
        total_size, file_sizes_map, processed_count = 0, {}, 0
        total_files = len(self.file_urls)
        for url in self.file_urls:
            if not self._is_running: break
            try:
                parsed_url = urlparse(url)
                size = 0
                if parsed_url.scheme.lower() in ('http', 'https'):
                    size = self._get_http_size(url)
                elif parsed_url.scheme.lower() in ('ftp', ''):
                    size = self._get_ftp_size(parsed_url)
                if size >= 0: # Allow 0-byte files
                    total_size += size
                    file_sizes_map[url] = size
            except Exception as e:
                logger.warning(f"Could not get size for {url}: {e}")
            processed_count += 1
            self.progress.emit(processed_count, total_files)
        if self._is_running:
            self.finished.emit(total_size, file_sizes_map)

    def _get_http_size(self, url):
        try:
            response = requests.head(url, allow_redirects=True, timeout=self.config.get('request_timeout', 10))
            response.raise_for_status()
            return int(response.headers.get('content-length', 0))
        except requests.RequestException as e:
            logger.error(f"HTTP size check failed for {url}: {e}")
            return -1 # Indicate error

    def _get_ftp_size(self, parsed_url):
        try:
            with FTP(parsed_url.netloc, timeout=self.config.get('request_timeout', 10)) as ftp:
                ftp.login()
                return ftp.size(parsed_url.path)
        except Exception as e:
            logger.error(f"FTP size check failed for {parsed_url.geturl()}: {e}")
            return -1 # Indicate error

    def stop(self):
        self._is_running = False
