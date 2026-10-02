"""Centralized logging setup."""
import logging
import logging.config
import json
import os

def setup_logging(config_path: str = "/app/config/logging.json") -> logging.Logger:
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
    
    return logging.getLogger("puzzle_migrator")