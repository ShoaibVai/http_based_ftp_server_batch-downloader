# utils/logger.py
# This module sets up centralized logging for the application.

import logging
import os

def setup_logger(log_dir='logs', log_file='app.log'):
    """
    Configures and returns a logger instance.

    The logger will write to both a file and the console.
    """
    log_path = os.path.join(log_dir, log_file)

    # Configure the root logger
    # Use a flag to prevent adding handlers multiple times
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        logging.getLogger(__name__).info("Logger initialized.")
    
    return logging.getLogger(__name__)
