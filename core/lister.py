# core/lister.py
# This module contains the DirectoryLister thread for fetching file lists from servers.

import logging
from urllib.parse import urlparse, urljoin
from ftplib import FTP, error_perm
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class DirectoryLister(QThread):
    """A QThread that lists files and directories from an FTP or HTTP URL."""
    item_found = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, url, config):
        super().__init__()
        self.url = url
        self.config = config
        self.parsed_url = urlparse(self.url)
        self.base_url = url if url.endswith('/') else url + '/'
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            if self.parsed_url.scheme.lower() in ('ftp', ''):
                self._list_ftp(self.parsed_url.path)
            elif self.parsed_url.scheme.lower() in ('http', 'https'):
                self._list_http(self.url)
            else:
                raise ValueError(f"Unsupported URL scheme: {self.parsed_url.scheme}")
        except Exception as e:
            logger.error(f"Listing error for {self.url}: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def _list_ftp(self, path, current_depth=0):
        if self._cancelled: return
        if current_depth >= self.config.get('listing_depth', 3): return
        try:
            with FTP(self.parsed_url.netloc, timeout=self.config.get('request_timeout', 30)) as ftp:
                ftp.login() # Anonymous login
                ftp.cwd(path)
                lines = []
                ftp.dir(lines.append)
                for line in lines:
                    if self._cancelled: return
                    parts = line.split()
                    if len(parts) < 9 or parts[8] in ('.', '..'): continue
                    name = " ".join(parts[8:])
                    is_dir = parts[0].startswith('d')
                    full_path = f"{path.rstrip('/')}/{name}"
                    self.item_found.emit({
                        'name': name, 'size': parts[4], 'type': "Directory" if is_dir else "File",
                        'modified': ' '.join(parts[5:8]), 'path': full_path
                    })
                    if is_dir: self._list_ftp(full_path, current_depth + 1)
        except Exception as e:
            logger.error(f"FTP error at {path}: {e}")
            self.error.emit(f"FTP error: {e}")

    def _list_http(self, url, current_depth=0):
        if self._cancelled: return
        if current_depth >= self.config.get('listing_depth', 3): return
        
        logger.info(f"Listing HTTP directory at depth {current_depth}: {url}")
        
        try:
            response = requests.get(url, timeout=self.config.get('request_timeout', 30))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a'):
                if self._cancelled: return
                href = link.get('href')
                if not href or href.startswith('?') or href.startswith('#') or link.get_text(strip=True).lower() == 'parent directory': 
                    continue
                    
                full_url = urljoin(url, href)
                is_dir = href.endswith('/')
                link_text = link.get_text(strip=True)
                
                # Extract the relative path from the base URL for proper tree building
                if full_url.startswith(self.base_url):
                    relative_path = full_url[len(self.base_url):].rstrip('/')
                    if not relative_path:  # Root directory
                        relative_path = '/'
                else:
                    relative_path = href.rstrip('/')
                    if not relative_path:
                        relative_path = '/'
                
                logger.info(f"Found item: {link_text} ({'Directory' if is_dir else 'File'}) at path: {relative_path}")
                
                self.item_found.emit({
                    'name': link_text, 'size': '-', 'type': "Directory" if is_dir else "File",
                    'modified': '-', 'path': relative_path, 'full_url': full_url
                })
                
                # Recursively list subdirectories
                if is_dir and full_url.startswith(self.base_url):
                    logger.info(f"Recursively listing subdirectory: {full_url}")
                    self._list_http(full_url, current_depth + 1)
                    
        except requests.RequestException as e:
            logger.error(f"HTTP error for {url}: {e}")
            self.error.emit(f"HTTP error: {e}")
