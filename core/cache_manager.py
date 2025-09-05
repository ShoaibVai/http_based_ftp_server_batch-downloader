# core/cache_manager.py
# Directory cache management for optimization

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DirectoryCache:
    """Manages caching of directory listings to improve performance."""
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=24)  # 24 hour cache expiration
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, url):
        """Generate a safe cache key from URL."""
        # Use hash to create a safe filename
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return f"cache_{url_hash}.json"
    
    def get(self, url):
        """Get cached directory listing if available and not expired."""
        try:
            cache_file = os.path.join(self.cache_dir, self._get_cache_key(url))
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                logger.info(f"Cache hit for URL: {url}")
                return data['content']
            else:
                # Cache expired, remove it
                os.remove(cache_file)
                logger.info(f"Cache expired for URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading cache for {url}: {e}")
            return None
    
    def set(self, url, content):
        """Cache directory listing with timestamp."""
        try:
            cache_file = os.path.join(self.cache_dir, self._get_cache_key(url))
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'content': content
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached directory listing for URL: {url}")
            
        except Exception as e:
            logger.error(f"Error caching directory listing for {url}: {e}")
    
    def clear_expired(self):
        """Remove all expired cache files."""
        try:
            removed_count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.startswith('cache_') and filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        cache_time = datetime.fromisoformat(data['timestamp'])
                        if datetime.now() - cache_time >= self.cache_duration:
                            os.remove(cache_file)
                            removed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing cache file {filename}: {e}")
                        # Remove corrupted cache files
                        try:
                            os.remove(cache_file)
                            removed_count += 1
                        except:
                            pass
            
            if removed_count > 0:
                logger.info(f"Removed {removed_count} expired cache files")
                
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
    
    def clear_all(self):
        """Remove all cache files."""
        try:
            removed_count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.startswith('cache_') and filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(cache_file)
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Error removing cache file {filename}: {e}")
            
            logger.info(f"Removed all {removed_count} cache files")
            
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
    
    def get_cache_stats(self):
        """Get statistics about the cache."""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) 
                          if f.startswith('cache_') and f.endswith('.json')]
            
            total_files = len(cache_files)
            total_size = 0
            valid_files = 0
            expired_files = 0
            
            for filename in cache_files:
                cache_file = os.path.join(self.cache_dir, filename)
                try:
                    file_size = os.path.getsize(cache_file)
                    total_size += file_size
                    
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    cache_time = datetime.fromisoformat(data['timestamp'])
                    if datetime.now() - cache_time < self.cache_duration:
                        valid_files += 1
                    else:
                        expired_files += 1
                        
                except Exception:
                    expired_files += 1
            
            return {
                'total_files': total_files,
                'valid_files': valid_files,
                'expired_files': expired_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'total_files': 0,
                'valid_files': 0,
                'expired_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0
            }
