# config/manager.py
# This module handles loading and saving application settings from a JSON file.

import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration settings."""

    def __init__(self, config_path='config.json'):
        """
        Initializes the ConfigManager.

        Args:
            config_path (str): The path to the configuration file.
        """
        self.config_path = config_path
        self.settings = self.load_settings()

    def get_default_settings(self):
        """Returns a dictionary with default settings."""
        return {
            "default_download_path": os.path.join(os.path.expanduser("~"), "Downloads"),
            "max_concurrent_downloads": 4,
            "max_concurrent_listings": 4,
            "listing_depth": 3,
            "chunk_size": 8192,
            "request_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5
        }

    def load_settings(self):
        """
        Loads settings from the JSON file. If the file doesn't exist,
        it creates one with default settings.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    settings = json.load(f)
                    # Ensure all default keys are present
                    default_settings = self.get_default_settings()
                    for key, value in default_settings.items():
                        settings.setdefault(key, value)
                    return settings
            else:
                logger.info(f"Configuration file not found at {self.config_path}. Creating with default settings.")
                return self.create_default_config()
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading configuration: {e}. Using default settings.")
            return self.get_default_settings()

    def create_default_config(self):
        """Creates and saves a default configuration file."""
        settings = self.get_default_settings()
        self.save_settings(settings)
        return settings

    def save_settings(self, settings=None):
        """
        Saves the current settings to the JSON file.
        """
        if settings is None:
            settings = self.settings
            
        try:
            with open(self.config_path, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info(f"Settings saved to {self.config_path}")
        except IOError as e:
            logger.error(f"Error saving configuration: {e}")

    def get(self, key, default=None):
        """Retrieves a setting value by key."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Sets a setting value and saves it."""
        self.settings[key] = value
        self.save_settings()
