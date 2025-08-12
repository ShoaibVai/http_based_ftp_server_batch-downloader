# core/downloader.py
# This module contains the DownloadManager and DownloadWorker for handling file downloads.

import os
import logging
import time
from urllib.parse import urlparse, unquote
import requests
from ftplib import FTP, error_perm
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QMutex, QWaitCondition, QMutexLocker

from .utils import SizeCalculator

logger = logging.getLogger(__name__)

class DownloadWorker(QThread):
    """A QThread that handles the download of a single file."""
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(str, int)
    error = pyqtSignal(str, str)
    status_changed = pyqtSignal(str, str)

    def __init__(self, worker_id, url, rel_path, base_folder, config, total_size=0):
        super().__init__()
        self.worker_id, self.url, self.rel_path, self.base_folder, self.config, self.total_size = worker_id, url, rel_path, base_folder, config, total_size
        self.parsed_url = urlparse(self.url)
        self._is_running, self._is_paused = True, False
        self.mutex, self.pause_cond = QMutex(), QWaitCondition()
        self.bytes_downloaded_this_session = 0

    def run(self):
        if not self._is_running: return
        self.status_changed.emit(self.worker_id, "Downloading")
        for attempt in range(self.config.get('retry_attempts', 3)):
            if not self._is_running: break
            try:
                if self.parsed_url.scheme.lower() in ('http', 'https'): self._download_http()
                elif self.parsed_url.scheme.lower() in ('ftp', ''): self._download_ftp()
                else: raise ValueError(f"Unsupported scheme: {self.parsed_url.scheme}")
                break
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {self.url}: {e}")
                if attempt + 1 >= self.config.get('retry_attempts', 3): self.error.emit(self.worker_id, str(e))
                else:
                    self.status_changed.emit(self.worker_id, f"Retrying ({attempt+1})...")
                    time.sleep(self.config.get('retry_delay', 5))
        if self._is_running: self.finished.emit(self.worker_id, self.bytes_downloaded_this_session)

    def _download_http(self):
        # Decode percent-encoded rel_path for local file creation
        local_filename = os.path.join(self.base_folder, unquote(self.rel_path))
        headers, resumed_bytes = {}, 0
        if os.path.exists(local_filename):
            resumed_bytes = os.path.getsize(local_filename)
            headers['Range'] = f'bytes={resumed_bytes}-'
        with requests.get(self.url, stream=True, headers=headers, timeout=self.config.get('request_timeout')) as r:
            r.raise_for_status()
            total_size = self.total_size or int(r.headers.get('content-length', 0)) + resumed_bytes
            downloaded_bytes = resumed_bytes
            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            with open(local_filename, 'ab' if resumed_bytes > 0 else 'wb') as f:
                for chunk in r.iter_content(chunk_size=self.config.get('chunk_size')):
                    with QMutexLocker(self.mutex):
                        if not self._is_running: return
                        if self._is_paused: self.pause_cond.wait(self.mutex)
                    if chunk:
                        f.write(chunk)
                        chunk_len = len(chunk)
                        downloaded_bytes += chunk_len
                        self.bytes_downloaded_this_session += chunk_len
                        self.progress.emit(self.worker_id, downloaded_bytes, total_size)

    def _download_ftp(self):
        # Decode percent-encoded rel_path for local file creation
        local_filename = os.path.join(self.base_folder, unquote(self.rel_path))
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        with FTP(self.parsed_url.netloc, timeout=self.config.get('request_timeout')) as ftp:
            ftp.login()
            total_size = self.total_size or ftp.size(self.parsed_url.path)
            downloaded_bytes = 0
            if os.path.exists(local_filename): downloaded_bytes = os.path.getsize(local_filename)
            with open(local_filename, 'ab' if downloaded_bytes > 0 else 'wb') as f:
                def callback(chunk):
                    nonlocal downloaded_bytes
                    with QMutexLocker(self.mutex):
                        if not self._is_running: raise IOError("Download canceled.")
                        if self._is_paused: self.pause_cond.wait(self.mutex)
                    f.write(chunk)
                    chunk_len = len(chunk)
                    downloaded_bytes += chunk_len
                    self.bytes_downloaded_this_session += chunk_len
                    self.progress.emit(self.worker_id, downloaded_bytes, total_size)
                ftp.retrbinary(f'RETR {self.parsed_url.path}', callback, blocksize=self.config.get('chunk_size'), rest=downloaded_bytes or None)

    def stop(self):
        with QMutexLocker(self.mutex):
            self._is_running = False
            if self._is_paused: self._is_paused = False; self.pause_cond.wakeAll()
        self.status_changed.emit(self.worker_id, "Canceled")

    def pause(self):
        with QMutexLocker(self.mutex):
            if self._is_running and not self._is_paused: self._is_paused = True; self.status_changed.emit(self.worker_id, "Paused")

    def resume(self):
        with QMutexLocker(self.mutex):
            if self._is_paused: self._is_paused = False; self.pause_cond.wakeAll(); self.status_changed.emit(self.worker_id, "Downloading")

class DownloadManager(QObject):
    """Manages a queue of downloads and a pool of worker threads."""
    overall_progress = pyqtSignal(int, int)
    file_started = pyqtSignal(str, str)
    file_progress = pyqtSignal(str, int, int)
    file_finished = pyqtSignal(str, str)
    file_status_changed = pyqtSignal(str, str)
    all_finished = pyqtSignal()
    error = pyqtSignal(str, str)
    size_calc_progress = pyqtSignal(int, int)
    size_calc_finished = pyqtSignal()
    downloads_updated = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.download_queue, self.active_workers, self.file_sizes = [], {}, {}
        self.total_bytes_to_download, self.total_bytes_downloaded = 0, 0
        self.size_calculator = None
        # Persistent download state
        self.downloads = []  # List of dicts: {url, rel_path, status, progress, size, file_path, ...}

    def start_downloads(self, file_tuples, base_folder):
        self.base_folder = base_folder
        new_urls = [url for url, _ in file_tuples if url not in [d['url'] for d in self.downloads if d['status'] in ('Queued','Downloading','Paused')] and url not in self.active_workers]
        if not new_urls:
            return
        self.size_calculator = SizeCalculator(new_urls, self.config)
        self.size_calculator.progress.connect(self.size_calc_progress)
        self.size_calculator.finished.connect(lambda total_size, file_sizes_map: self._on_size_calc_finished(total_size, file_sizes_map, file_tuples))
        self.size_calculator.error.connect(lambda msg: self.error.emit("Size Calculation", msg))
        self.size_calculator.start()

    def _on_size_calc_finished(self, total_size, file_sizes_map, file_tuples):
        self.size_calc_finished.emit()
        for url, size in file_sizes_map.items():
            if url not in self.file_sizes:
                self.file_sizes[url] = size
                self.total_bytes_to_download += size
        for url, rel_path in file_tuples:
            if url in file_sizes_map and not any(d['url'] == url and d['rel_path'] == rel_path for d in self.downloads):
                self.downloads.append({
                    'url': url,
                    'rel_path': rel_path,
                    'status': 'Queued',
                    'progress': 0,
                    'size': self.file_sizes[url],
                    'file_path': os.path.join(self.base_folder, rel_path),
                })
                self.download_queue.append((url, rel_path))
        self.downloads_updated.emit()
        if not self.download_queue and not self.active_workers:
            self.all_finished.emit()
        else:
            self.check_queue()

    def check_queue(self):
        if not self.download_queue and not self.active_workers:
            if self.total_bytes_downloaded >= self.total_bytes_to_download - 1:
                self.all_finished.emit()
            return
        max_workers = self.config.get('max_concurrent_downloads', 4)
        while self.download_queue and len(self.active_workers) < max_workers:
            url, rel_path = self.download_queue.pop(0)
            # Find the download entry to get its specific file path
            for download_entry in self.downloads:
                if download_entry['url'] == url and download_entry['rel_path'] == rel_path and download_entry['status'] == 'Queued':
                    base_folder = os.path.dirname(download_entry['file_path'])
                    worker = DownloadWorker(url, url, rel_path, base_folder, self.config, self.file_sizes.get(url, 0))
                    worker.finished.connect(self._on_worker_finished)
                    worker.error.connect(self._on_worker_error)
                    worker.progress.connect(self.file_progress)
                    worker.progress.connect(self._on_file_progress_update)
                    worker.status_changed.connect(self.file_status_changed)
                    self.active_workers[url] = worker
                    self._update_download_status(url, 'Downloading')
                    self.file_started.emit(url, os.path.basename(url))
                    worker.start()
                    self.downloads_updated.emit()
                    break # Found the entry and started the worker

    def _on_worker_finished(self, worker_id, bytes_downloaded):
        # Use a mutex if updating shared overall progress is still needed
        # with QMutexLocker(self.progress_mutex):
        self.total_bytes_downloaded += bytes_downloaded
        self.overall_progress.emit(self.total_bytes_downloaded, self.total_bytes_to_download)
        with QMutexLocker(self.mutex):  # Added mutex lock
            if worker_id in self.active_workers: # This line and the following lines were incorrectly unindented
                self.file_finished.emit(worker_id, os.path.basename(self.active_workers[worker_id].url)) # Also unindented
                self._update_download_status(worker_id, 'Completed') # Also unindented
 del self.active_workers[worker_id]
 self.downloads_updated.emit()
 self.check_queue()

    def _on_worker_error(self, worker_id, message):
        if worker_id in self.active_workers:
            self.error.emit(os.path.basename(self.active_workers[worker_id].url), message)
            self.file_status_changed.emit(worker_id, "Error")
            self._update_download_status(worker_id, 'Failed')
            del self.active_workers[worker_id]
            self.downloads_updated.emit()
            self.check_queue()

    def _update_download_status(self, url, status):
        for d in self.downloads:
            if d['url'] == url:
                d['status'] = status
                if status == 'Completed':
                    d['progress'] = 100
                break

    def update_progress(self, url, downloaded, total):
        for d in self.downloads:
            if d['url'] == url:
                d['progress'] = int((downloaded / total) * 100) if total else 0
                break
        self.downloads_updated.emit()

    def _on_file_progress_update(self, worker_id, downloaded, total):
        self.update_progress(worker_id, downloaded, total)
        # self.downloads_updated.emit()  # Removed to prevent UI freeze

    def pause_file(self, worker_id):
        if worker_id in self.active_workers: self.active_workers[worker_id].pause(); self._update_download_status(worker_id, 'Paused'); self.downloads_updated.emit()
    def resume_file(self, worker_id):
        if worker_id in self.active_workers: self.active_workers[worker_id].resume(); self._update_download_status(worker_id, 'Downloading'); self.downloads_updated.emit()
    def cancel_file(self, worker_id):
        if worker_id in self.active_workers: self.active_workers[worker_id].stop(); self._update_download_status(worker_id, 'Canceled'); self.downloads_updated.emit()
    def pause_all(self):
        for worker in self.active_workers.values(): worker.pause(); self._update_download_status(worker.worker_id, 'Paused')
        self.downloads_updated.emit()
    def resume_all(self):
        for worker in self.active_workers.values(): worker.resume(); self._update_download_status(worker.worker_id, 'Downloading')
        self.downloads_updated.emit()
    def cancel_all(self):
        # Cancel all active workers
        for worker in self.active_workers.values():
            worker.stop()
            self._update_download_status(worker.worker_id, 'Canceled')
        # Mark all queued downloads as canceled
        for url, rel_path in self.download_queue:
            for d in self.downloads:
                if d['url'] == url and d['rel_path'] == rel_path and d['status'] == 'Queued':
                    d['status'] = 'Canceled'
                    d['progress'] = 0
        self.download_queue.clear()
        self.downloads_updated.emit()

    def retry_download(self, url):
        # Find the download and re-queue it
        for d in self.downloads:
            if d['url'] == url and d['status'] in ('Failed', 'Canceled'):
                d['status'] = 'Queued'
                d['progress'] = 0
                self.download_queue.append((d['url'], d['rel_path']))
                self.downloads_updated.emit()
                self.check_queue()
                break

    def get_downloads_by_status(self):
        active = [d for d in self.downloads if d['status'] in ('Queued','Downloading','Paused')]
        completed = [d for d in self.downloads if d['status'] == 'Completed']
        failed = [d for d in self.downloads if d['status'] == 'Failed']
        canceled = [d for d in self.downloads if d['status'] == 'Canceled']
        return active, completed, failed, canceled
