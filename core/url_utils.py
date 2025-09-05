# core/url_utils.py
# URL utility functions for proper encoding and validation

import logging
from urllib.parse import quote, unquote
from PyQt5.QtCore import QUrl

logger = logging.getLogger(__name__)

def ensure_url_encoded(url):
    """Ensure URL is properly percent-encoded for FTP/HTTP operations."""
    if not url:
        return None
    
    try:
        qurl = QUrl(url)
        if not qurl.isValid():
            logger.warning(f"Invalid URL: {url}")
            return None
        
        # Check if URL has a valid scheme and host
        if not qurl.scheme() or (qurl.scheme().lower() != 'http' and qurl.scheme().lower() != 'https' and qurl.scheme().lower() != 'ftp'):
            logger.warning(f"Unsupported scheme in URL: {url}")
            return None
        
        if not qurl.host() and qurl.scheme().lower() == 'ftp':
            logger.warning(f"FTP URL missing host: {url}")
            return None
        
        # Handle special characters that QUrl doesn't encode properly
        # QUrl tends to leave some characters unencoded that should be encoded for FTP
        encoded_bytes = qurl.toEncoded()
        encoded_url = encoded_bytes.data().decode('utf-8')
        
        # Manually encode characters that QUrl misses
        # Replace unencoded ampersands with encoded ones
        encoded_url = encoded_url.replace('&', '%26')
        
        logger.debug(f"URL encoding: {url} -> {encoded_url}")
        return encoded_url
        
    except Exception as e:
        logger.error(f"Error encoding URL {url}: {e}")
        return None

def is_valid_ftp_url(url):
    """Check if URL is a valid FTP/HTTP URL for server operations."""
    if not url:
        return False
    
    try:
        qurl = QUrl(url)
        scheme = qurl.scheme().lower()
        
        # Basic validity check
        if not qurl.isValid():
            return False
        
        # Check supported schemes
        if scheme not in ['ftp', 'http', 'https']:
            return False
        
        # Additional validation for FTP URLs
        if scheme == 'ftp':
            # Ensure FTP URL has a host
            if not qurl.host():
                return False
        
        # Reject URLs that are just scheme without anything else
        if url.strip() in ['http://', 'https://', 'ftp://']:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating URL {url}: {e}")
        return False

def get_display_url(url):
    """Get user-friendly display version of URL (decoded for readability)."""
    if not url:
        return ""
    
    try:
        qurl = QUrl(url)
        if not qurl.isValid():
            return url
        
        # Return the toString() version which is user-friendly
        return qurl.toString()
        
    except Exception as e:
        logger.error(f"Error getting display URL for {url}: {e}")
        return url

def normalize_ftp_url(url):
    """Normalize FTP URL for consistent handling."""
    if not url:
        return None
    
    try:
        qurl = QUrl(url)
        if not qurl.isValid():
            return None
        
        # Ensure trailing slash for directories
        path = qurl.path()
        if not path.endswith('/') and '.' not in path.split('/')[-1]:
            qurl.setPath(path + '/')
        
        return qurl.toEncoded().data().decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error normalizing URL {url}: {e}")
        return None

def extract_filename_from_url(url):
    """Extract filename from URL path."""
    if not url:
        return ""
    
    try:
        qurl = QUrl(url)
        path = qurl.path()
        if path and '/' in path:
            return path.split('/')[-1]
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting filename from URL {url}: {e}")
        return ""

def is_directory_url(url):
    """Check if URL appears to be a directory (ends with / or has no file extension)."""
    if not url:
        return False
    
    try:
        qurl = QUrl(url)
        path = qurl.path()
        
        # If path ends with /, it's a directory
        if path.endswith('/'):
            return True
        
        # If the last component has no extension, likely a directory
        if path and '/' in path:
            last_component = path.split('/')[-1]
            return '.' not in last_component
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking if URL is directory {url}: {e}")
        return False
