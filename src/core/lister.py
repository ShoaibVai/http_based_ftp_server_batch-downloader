# core/lister.py
# This module contains the DirectoryLister thread for fetching file lists from servers.

import logging
from urllib.parse import urlparse, urljoin
from ftplib import FTP, error_perm
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal
from .cache_manager import DirectoryCache, MemoryCache

logger = logging.getLogger(__name__)

class DirectoryLister(QThread):
    """A QThread that lists files and directories from an FTP or HTTP URL."""
    item_found = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    cache_status = pyqtSignal(str)  # New signal for cache status

    def __init__(self, url, config, use_cache=True, page_size=None):
        super().__init__()
        self.url = url
        self.config = config
        self.use_cache = use_cache
        self.page_size = page_size or config.get('page_size', 1000)
        self.parsed_url = urlparse(self.url)
        self.base_url = url if url.endswith('/') else url + '/'
        self._cancelled = False
        
        # Initialize caches
        self.disk_cache = DirectoryCache(
            cache_dir=config.get('cache_dir', 'cache'),
            cache_expiry_hours=config.get('cache_expiry_hours', 24)
        )
        self.memory_cache = MemoryCache(max_size=config.get('memory_cache_size', 50))
        
        self.items_processed = 0
        self.total_items = 0

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            # Check memory cache first
            cached_data = None
            if self.use_cache:
                cached_data = self.memory_cache.get(self.url)
                if cached_data:
                    self.cache_status.emit("Using memory cache")
                    self._emit_cached_items(cached_data)
                    return
                
                # Check disk cache
                cached_data = self.disk_cache.get(self.url)
                if cached_data:
                    self.cache_status.emit("Using disk cache")
                    # Store in memory cache for future use
                    self.memory_cache.set(self.url, cached_data)
                    self._emit_cached_items(cached_data)
                    return
            
            # No cache hit, fetch from server
            self.cache_status.emit("Fetching from server")
            items = []
            
            if self.parsed_url.scheme.lower() in ('ftp', ''):
                items = self._list_ftp_paginated(self.parsed_url.path)
            elif self.parsed_url.scheme.lower() in ('http', 'https'):
                items = self._list_http_paginated(self.url)
            else:
                raise ValueError(f"Unsupported URL scheme: {self.parsed_url.scheme}")
            
            # Cache the results if enabled
            if self.use_cache and items:
                self.disk_cache.set(self.url, items)
                self.memory_cache.set(self.url, items)
                
        except Exception as e:
            logger.error(f"Listing error for {self.url}: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
    
    def _emit_cached_items(self, items):
        """Emit cached items with pagination support."""
        for i, item in enumerate(items):
            if self._cancelled:
                break
            if self.page_size and i >= self.page_size:
                break
            self.item_found.emit(item)
    
    def _list_ftp_paginated(self, path, current_depth=0):
        """List FTP directory with pagination support."""
        items = []
        if self._cancelled or current_depth >= self.config.get('listing_depth', 3):
            return items
            
        try:
            with FTP(self.parsed_url.netloc, timeout=self.config.get('request_timeout', 30)) as ftp:
                ftp.login()  # Anonymous login
                ftp.cwd(path)
                lines = []
                ftp.dir(lines.append)
                
                for i, line in enumerate(lines):
                    if self._cancelled:
                        break
                    if self.page_size and len(items) >= self.page_size:
                        break
                        
                    parts = line.split()
                    if len(parts) < 9 or parts[8] in ('.', '..'):
                        continue
                        
                    name = " ".join(parts[8:])
                    is_dir = parts[0].startswith('d')
                    full_path = f"{path.rstrip('/')}/{name}"
                    
                    item = {
                        'name': name,
                        'size': parts[4],
                        'type': "Directory" if is_dir else "File",
                        'modified': ' '.join(parts[5:8]),
                        'path': full_path
                    }
                    
                    items.append(item)
                    self.item_found.emit(item)
                    
                    # Recursively list subdirectories if within limits
                    if is_dir and not self.page_size:  # Skip recursion if paginating
                        sub_items = self._list_ftp_paginated(full_path, current_depth + 1)
                        items.extend(sub_items)
                        
        except Exception as e:
            logger.error(f"FTP error at {path}: {e}")
            self.error.emit(f"FTP error: {e}")
            
        return items
    
    def _list_http_paginated(self, url, current_depth=0):
        """List HTTP directory with pagination support."""
        items = []
        if self._cancelled or current_depth >= self.config.get('listing_depth', 3):
            return items
        
        logger.info(f"Listing HTTP directory at depth {current_depth}: {url}")
        
        try:
            response = requests.get(url, timeout=self.config.get('request_timeout', 30))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for i, link in enumerate(soup.find_all('a')):
                if self._cancelled:
                    break
                if self.page_size and len(items) >= self.page_size:
                    break
                    
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
                
                item = {
                    'name': link_text,
                    'size': '-',
                    'type': "Directory" if is_dir else "File",
                    'modified': '-',
                    'path': relative_path,
                    'full_url': full_url
                }
                
                items.append(item)
                self.item_found.emit(item)
                
                # Recursively list subdirectories if within limits
                if is_dir and full_url.startswith(self.base_url) and not self.page_size:
                    logger.info(f"Recursively listing subdirectory: {full_url}")
                    sub_items = self._list_http_paginated(full_url, current_depth + 1)
                    items.extend(sub_items)
                    
        except requests.RequestException as e:
            logger.error(f"HTTP error for {url}: {e}")
            self.error.emit(f"HTTP error: {e}")
            
        return items
